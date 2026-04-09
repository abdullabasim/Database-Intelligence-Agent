"""
Agent Graph Definition
----------------------
This module defines the LangGraph state machine that orchestrates the data analysis flow:
1. load_mdl: Fetches semantic metadata for the target database.
2. understand_question: Analyzes the natural language intent.
3. generate_sql: Transpiles intent to valid SQL.
4. validate_sql: Sanitizes and checks the SQL for safety/correctness.
5. execute_sql: Runs the query against the tenant database.
6. format_answer: Synthesizes the result into a human-readable response.
"""
from langgraph.graph import END, StateGraph

from app.core.config import get_settings

from app.agent.nodes import (
    execute_sql_node,
    format_answer_node,
    generate_sql_node,
    load_mdl_node,
    understand_question_node,
    validate_sql_node,
)
from app.agent.state import AgentState


def should_continue_after_load(state: AgentState) -> str:
    """
    Decision node after attempting to load the MDL.
    Routes to 'understand_question' if successful, or skips to 'format_answer' if the MDL is missing.
    """
    if state.get("error"):
        return "format_answer"
    return "understand_question"


def should_continue_after_validate(state: AgentState) -> str:
    """
    Decision node after SQL validation.
    Routes to 'execute_sql' if the query is safe, or 'format_answer' to report validation errors.
    """
    if state.get("error"):
        return "format_answer"
    return "execute_sql"


def should_continue_after_execute(state: AgentState) -> str:
    """
    Decision node after SQL execution.
    - If in 'explore' mode, loops back to 'generate_sql' to gather more context.
    - If an execution error occurred, loops back to 'generate_sql' to attempt a fix (up to MAX_SQL_RETRIES).
    - Otherwise, proceeds to 'format_answer'.
    """
    if state.get("query_type") == "explore":
        return "generate_sql"
        
    if state.get("error") and not state.get("error").startswith("FATAL"):
        settings = get_settings()
        if state.get("retry_count", 0) <= settings.MAX_SQL_RETRIES:
            return "generate_sql"
    return "format_answer"


# ── Build the agent graph ────────────────────────────────────────────────
builder = StateGraph(AgentState)

builder.add_node("load_mdl", load_mdl_node)
builder.add_node("understand_question", understand_question_node)
builder.add_node("generate_sql", generate_sql_node)
builder.add_node("validate_sql", validate_sql_node)
builder.add_node("execute_sql", execute_sql_node)
builder.add_node("format_answer", format_answer_node)

builder.set_entry_point("load_mdl")

builder.add_conditional_edges(
    "load_mdl",
    should_continue_after_load,
    {
        "understand_question": "understand_question",
        "format_answer": "format_answer",
    },
)

builder.add_edge("understand_question", "generate_sql")
builder.add_edge("generate_sql", "validate_sql")

builder.add_conditional_edges(
    "validate_sql",
    should_continue_after_validate,
    {
        "execute_sql": "execute_sql",
        "format_answer": "format_answer",
    },
)

builder.add_conditional_edges(
    "execute_sql",
    should_continue_after_execute,
    {
        "generate_sql": "generate_sql",
        "format_answer": "format_answer",
    },
)

builder.add_edge("format_answer", END)

agent_graph = builder.compile()
