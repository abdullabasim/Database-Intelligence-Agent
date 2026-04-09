"""
Semantic Metadata Builder
-------------------------
Handles the automatic inspection and enrichment of database schemas.
Uses SQLAlchemy to extract raw structure and Groq LLM to add business-level 
context (MDL - Metadata Definition Layer).
"""
import asyncio
import json
import logging
import traceback
from datetime import datetime

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_engine, get_dynamic_sync_engine
from app.core.models.mdl import MDLSchema
from app.core.models.tenant import DatabaseConnection
import uuid

logger = logging.getLogger(__name__)

MDL_ENRICHMENT_SYSTEM_PROMPT = """You are a senior data analyst.
You will receive a raw database schema extracted via SQLAlchemy inspector.
Your job is to enrich it with business-level semantic metadata.
Return ONLY a valid JSON object. No markdown, no code fences, no explanation, no preamble.

The JSON must follow this exact structure:
{
  "tables": {
    "<table_name>": {
      "description": "<what this table stores in business terms>",
      "business_purpose": "<how this table is used for analysis>",
      "columns": {
        "<column_name>": {
          "description": "<business meaning of this column>",
          "is_metric": "<true if numeric and measurable>",
          "is_date": "<true if this is a date/time column>",
          "aggregatable": "<true if SUM/AVG/COUNT makes sense>",
          "data_type": "<original SQL type>",
          "enum_values": ["<possible values if categorical, else null>"]
        }
      },
      "common_filters": ["<columns most often used in WHERE clauses>"],
      "join_hints": {
        "<other_table>": "<full JOIN SQL snippet>"
      },
      "example_questions": [
        "<natural language question this table can answer>"
      ]
    }
  },
  "metric_definitions": {
    "count_records": "COUNT(*)",
    "total_value": "SUM(amount) -- (if applicable)"
  },
  "date_conventions": {
    "last_7_days": "WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'",
    "this_month": "WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)"
  },
  "query_guidelines": [
    "Always use table aliases for clarity",
    "Use COALESCE for aggregations to avoid NULL",
    "Select specific columns instead of SELECT *"
  ]
}"""


def _inspect_schema_sync(sync_engine, blocked_tables: list[str]) -> dict:
    """
    Performs a synchronous inspection of the database schema using SQLAlchemy.
    Extracts table names, columns, types, foreign keys, and primary keys.
    
    Args:
        sync_engine: A SQLAlchemy synchronous engine.
        blocked_tables: List of table names to exclude from the inspection.
        
    Returns:
        dict: A dictionary representing the raw SQL schema.
    """
    inspector = sa_inspect(sync_engine)

    raw_schema = {}
    for table_name in inspector.get_table_names():
        if table_name.lower() in blocked_tables:
            continue

        columns = inspector.get_columns(table_name)
        fks = inspector.get_foreign_keys(table_name)
        pk = inspector.get_pk_constraint(table_name)
        indexes = inspector.get_indexes(table_name)

        raw_schema[table_name] = {
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col.get("default", "")) if col.get("default") else None,
                    "primary_key": col["name"] in (pk.get("constrained_columns") or []),
                }
                for col in columns
            ],
            "foreign_keys": [
                {
                    "column": fk["constrained_columns"],
                    "references_table": fk["referred_table"],
                    "references_column": fk["referred_columns"],
                }
                for fk in fks
            ],
            "indexes": [idx["name"] for idx in indexes],
        }

    return raw_schema


async def build_and_save_mdl(database_id: uuid.UUID, mdl_name: str, blocked_tables: list[str]) -> None:
    """
    Orchestrates the creation of a Metadata Layer (MDL) for a database connection.
    1. Locks the generation process.
    2. Inspects raw schema.
    3. Enriches the schema with business context using an LLM.
    4. Versions and activates the new MDL.
    """
    settings = get_settings()
    placeholder_id: int | None = None

    try:
        # ── Step 1: Lock check & Connection lookup ─────────────────────
        async with AsyncSession(async_engine) as session:
            # Check for existing lock
            lock_query = select(MDLSchema).where(
                MDLSchema.database_id == database_id,
                MDLSchema.is_generating == True,  # noqa: E712
            )
            lock_result = await session.execute(lock_query)
            if lock_result.scalar_one_or_none():
                logger.warning("MDL generation already in progress for connection '%s'", database_id)
                return

            # Lookup connection to get sync_url
            conn_query = select(DatabaseConnection).where(DatabaseConnection.id == database_id)
            conn_result = await session.execute(conn_query)
            conn = conn_result.scalar_one_or_none()
            if not conn:
                logger.error("Database connection '%s' not found for MDL generation", database_id)
                return
            
            sync_url = conn.sync_url

            # Insert placeholder lock row
            placeholder = MDLSchema(
                database_id=database_id,
                name=mdl_name,
                version=0,
                schema_json={},
                is_active=False,
                is_generating=True,
            )
            session.add(placeholder)
            await session.commit()
            await session.refresh(placeholder)
            placeholder_id = placeholder.id
            logger.info("MDL generation lock acquired (placeholder id=%d)", placeholder_id)

        # ── Step 2: Extract Schema ───────────────────────────────────────
        loop = asyncio.get_event_loop()
        sync_engine = get_dynamic_sync_engine(sync_url)
        raw_schema = await loop.run_in_executor(
            None, _inspect_schema_sync, sync_engine, blocked_tables
        )
        logger.info("Schema inspection complete: %d tables found", len(raw_schema))

        if not raw_schema:
            logger.warning("No tables found after filtering blocked tables. Saving raw schema.")
            enriched_schema = {
                "tables": {},
                "metric_definitions": {},
                "date_conventions": {},
                "query_guidelines": [],
            }
        else:
            # ── Step 3: Groq enrichment ─────────────────────────────────
            logger.info("Enriching schema via Groq LLM...")
            enriched_schema = await _enrich_with_groq(raw_schema, blocked_tables, settings.GROQ_API_KEY)

        # ── Step 4: Version and save ────────────────────────────────────
        async with AsyncSession(async_engine) as session:
            # Determine next version
            version_query = select(func.max(MDLSchema.version)).where(MDLSchema.database_id == database_id)
            ver_result = await session.execute(version_query)
            max_ver = ver_result.scalar() or 0
            new_version = max_ver + 1

            # Deactivate previous versions
            await session.execute(
                update(MDLSchema)
                .where(MDLSchema.database_id == database_id)
                .values(is_active=False)
            )

            # Delete placeholder lock row
            await session.execute(
                delete(MDLSchema).where(MDLSchema.id == placeholder_id)
            )

            # Insert final MDL
            final_mdl = MDLSchema(
                database_id=database_id,
                name=mdl_name,
                version=new_version,
                schema_json=enriched_schema,
                is_active=True,
                is_generating=False,
            )
            session.add(final_mdl)
            await session.commit()

            logger.info(
                "MDL '%s' version %d saved and activated successfully.",
                mdl_name,
                new_version,
            )

    except Exception:
        logger.error("MDL generation failed:\n%s", traceback.format_exc())
        # Release lock by deleting placeholder
        if placeholder_id is not None:
            try:
                async with AsyncSession(async_engine) as session:
                    await session.execute(
                        delete(MDLSchema).where(MDLSchema.id == placeholder_id)
                    )
                    await session.commit()
                    logger.info("Released MDL generation lock (placeholder id=%d)", placeholder_id)
            except Exception:
                logger.error("Failed to release MDL lock:\n%s", traceback.format_exc())
        raise


async def _enrich_with_groq(
    raw_schema: dict,
    blocked_tables: list[str],
    groq_api_key: str,
) -> dict:
    """Send raw schema to Groq LLM for semantic enrichment."""
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    settings = get_settings()
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        temperature=0,
        api_key=groq_api_key,
    )

    blocked_str = ", ".join(blocked_tables) if blocked_tables else "none"
    user_content = (
        f"IMPORTANT: Do NOT include these tables in the output: {blocked_str}\n\n"
        f"Raw schema to enrich:\n{json.dumps(raw_schema, indent=2, default=str)}"
    )

    messages = [
        SystemMessage(content=MDL_ENRICHMENT_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = await llm.ainvoke(messages)
    response_text = response.content.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        enriched = json.loads(response_text)
        logger.info("Successfully parsed Groq enrichment response.")
        return enriched
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Groq response as JSON: %s", str(e))
        logger.error("Raw response (first 500 chars): %s", response_text[:500])
        # Fallback: build minimal metadata from raw schema
        fallback = {
            "tables": {
                table_name: {
                    "description": f"Table: {table_name}",
                    "business_purpose": "",
                    "columns": {
                        col["name"]: {
                            "description": col["name"],
                            "is_metric": False,
                            "is_date": False,
                            "aggregatable": False,
                            "data_type": col["type"],
                            "enum_values": None,
                        }
                        for col in table_info["columns"]
                    },
                    "common_filters": [],
                    "join_hints": {},
                    "example_questions": [],
                }
                for table_name, table_info in raw_schema.items()
            },
            "metric_definitions": {
                "record_count": "COUNT(*)"
            },
            "date_conventions": {
                "lately": "WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
            },
            "query_guidelines": [
                "Always use table aliases for clarity",
                "Use COALESCE for aggregates"
            ],
        }
        return fallback
