import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.agent.mdl_builder import build_and_save_mdl
from app.core.config import get_settings
from app.core.database import get_db
from app.core.models.auth import User
from app.core.models.mdl import MDLSchema
from app.core.models.tenant import DatabaseConnection
from app.core.services.auth import get_current_user
from app.core.schemas.mdl import (
    MDLRefreshRequest,
    MDLRefreshResponse,
    MDLResponse,
    MDLVersionSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mdl", tags=["MDL"])


@router.get(
    "/latest",
    # response_model=MDLResponse,
    summary="Get the latest active MDL",
    description="Returns the most recent active Metadata Definition Layer for the given database connection.",
)
async def get_latest_mdl(
    database_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MDLResponse:
    """
    Retrieves the currently active semantic schema layer for a specific database.
    This layer is used by the agent to understand the database structure.
    """
    # Verify ownership
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == database_id,
            DatabaseConnection.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Database connection not found.")

    result = await db.execute(
        select(MDLSchema)
        .where(MDLSchema.database_id == database_id, MDLSchema.is_active == True)  # noqa: E712
        .order_by(MDLSchema.version.desc())
        .limit(1)
    )
    mdl = result.scalar_one_or_none()
    if not mdl:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": f"No active MDL found for connection {database_id}",
                "error_code": "MDL_NOT_FOUND",
            },
        )
    return MDLResponse.model_validate(mdl)


@router.get(
    "/versions",
    # response_model=list[MDLVersionSummary],
    summary="List all MDL versions",
    description="Returns all versions of the MDL for a database, ordered by version descending.",
)
async def list_versions(
    database_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MDLVersionSummary]:
    """
    Returns a history of all MDL schemas generated for a connection.
    Useful for audit logs or rolling back to previous versions.
    """
    # Verify ownership
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == database_id,
            DatabaseConnection.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Database connection not found.")

    result = await db.execute(
        select(MDLSchema)
        .where(MDLSchema.database_id == database_id)
        .order_by(MDLSchema.version.desc())
    )
    rows = result.scalars().all()
    return [MDLVersionSummary.model_validate(r) for r in rows]


@router.get(
    "/{version}",
    # response_model=MDLResponse,
    summary="Get a specific MDL version",
)
async def get_mdl_version(
    version: int,
    database_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MDLResponse:
    """
    Fetches a specific historical version of the MDL for a connection.
    """
    # Verify ownership
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == database_id,
            DatabaseConnection.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Database connection not found.")

    result = await db.execute(
        select(MDLSchema).where(MDLSchema.database_id == database_id, MDLSchema.version == version)
    )
    mdl = result.scalar_one_or_none()
    if not mdl:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": f"MDL version {version} not found for connection {database_id}",
                "error_code": "MDL_VERSION_NOT_FOUND",
            },
        )
    return MDLResponse.model_validate(mdl)


@router.post(
    "/refresh",
    # response_model=MDLRefreshResponse,
    summary="Trigger MDL rebuild in background",
    description=(
        "Starts a background task to re-inspect the schema and enrich it via LLM. "
        "This is required whenever your database schema changes."
    ),
)
async def refresh_mdl(
    request: MDLRefreshRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MDLRefreshResponse:
    """
    Asynchronously regenerates the Metadata Layer.
    Scans the database tables, fetches sample data, and uses an LLM to add semantic context.
    """
    settings = get_settings()

    # Verify ownership
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == request.database_id,
            DatabaseConnection.user_id == current_user.id
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    # Check if already generating
    result = await db.execute(
        select(MDLSchema).where(
            MDLSchema.database_id == request.database_id,
            MDLSchema.is_generating == True,  # noqa: E712
        )
    )
    if result.scalar_one_or_none():
        return MDLRefreshResponse(
            message="MDL generation already in progress.",
            mdl_name=request.name,
            current_version=None,
            status="already_running",
        )

    # Get current version
    ver_result = await db.execute(
        select(func.max(MDLSchema.version)).where(MDLSchema.database_id == request.database_id)
    )
    current_version = ver_result.scalar()

    blocked = request.blocked_tables or conn.blocked_tables or settings.blocked_tables_list

    background_tasks.add_task(build_and_save_mdl, request.database_id, request.name, blocked)

    return MDLRefreshResponse(
        message="MDL generation started in background. Poll /mdl/latest to check when ready.",
        mdl_name=request.name,
        current_version=current_version,
        status="started",
    )
