import uuid
from typing import Any

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["What is the total revenue this month?"],
        description="Natural language question about your financial data",
    )
    database_id: uuid.UUID = Field(
        ...,
        description="Which Tenant Database Connection ID to use",
    )


class SQLResult(BaseModel):
    rows: list[dict[str, Any]]
    row_count: int
    columns: list[str]


class AgentResponse(BaseModel):
    answer: str = Field(description="Natural language answer to your question")
    sql_query: str | None = Field(
        default=None, description="The SQL query that was executed"
    )
    sql_result: SQLResult | None = Field(
        default=None, description="Raw query results"
    )
    steps: list[str] = Field(default=[], description="Agent reasoning steps")
    execution_time_ms: float = Field(description="Total execution time in milliseconds")
    mdl_version: int | None = Field(
        default=None, description="MDL version used"
    )
    error: str | None = Field(
        default=None, description="Error message if something went wrong"
    )
