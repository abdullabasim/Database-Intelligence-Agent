from typing import Any, TypedDict


class AgentState(TypedDict):
    """State that flows through the LangGraph agent pipeline."""

    # Input
    question: str
    database_id: str
    db_url: str

    # Loaded context
    mdl: dict[str, Any]
    mdl_version: int | None
    blocked_tables: list[str]
    error: str | None
    retry_count: int

    # Exploration
    query_type: str
    exploration_context: str
    exploration_count: int

    # Generation
    sql_query: str
    sql_result: list[dict[str, Any]]
    result_columns: list[str]

    # Output
    answer: str
    steps: list[str]
    error: str | None
