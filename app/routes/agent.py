import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agent.graph import agent_graph
from app.core.database import get_db
from app.core.models.auth import User
from app.core.models.tenant import DatabaseConnection
from app.core.services.auth import get_current_user
from app.core.services.crypto import decrypt_password
from app.core.schemas.agent import AgentResponse, QuestionRequest, SQLResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/ask", response_model=AgentResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    # ... existing implementation (omitted for brevity in this tool call, but kept in file)
    logger.info("Received question: %s", request.question)
    start = time.time()
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == request.database_id))
    conn = result.scalar_one_or_none()
    if not conn or conn.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    decrypted_password = decrypt_password(conn.encrypted_password)
    db_url = f"postgresql+asyncpg://{conn.username}:{decrypted_password}@{conn.host}:{conn.port}/{conn.db_name}"

    initial_state = {
        "question": request.question,
        "database_id": str(request.database_id),
        "db_url": db_url,
        "blocked_tables": conn.blocked_tables or [],
        "mdl": {}, "mdl_version": None,
        "sql_query": "", "sql_result": [], "result_columns": [],
        "answer": "", "steps": [], "error": None, "retry_count": 0,
        "query_type": "final", "exploration_context": "", "exploration_count": 0,
    }

    try:
        final_state = await agent_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error("Graph execution failed: %s", str(e))
        return AgentResponse(
            answer=f"I encountered a system error: {str(e)}",
            steps=initial_state["steps"] + [f"✗ System Error"],
            execution_time_ms=round((time.time() - start) * 1000, 2),
            error=str(e),
        )

    elapsed = (time.time() - start) * 1000
    sql_result = SQLResult(rows=final_state["sql_result"], row_count=len(final_state["sql_result"]), columns=final_state.get("result_columns", [])) if final_state.get("sql_result") else None

    return AgentResponse(
        answer=final_state.get("answer", ""),
        sql_query=final_state.get("sql_query"),
        sql_result=sql_result,
        steps=final_state.get("steps", []),
        execution_time_ms=round(elapsed, 2),
        mdl_version=final_state.get("mdl_version"),
        error=final_state.get("error"),
    )


@router.post("/ask/stream")
async def stream_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Streams agent progress and results using SSE.
    """
    logger.info("Streaming question: %s", request.question)
    
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == request.database_id))
    conn = result.scalar_one_or_none()
    if not conn or conn.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Database connection not found.")

    decrypted_password = decrypt_password(conn.encrypted_password)
    db_url = f"postgresql+asyncpg://{conn.username}:{decrypted_password}@{conn.host}:{conn.port}/{conn.db_name}"

    initial_state = {
        "question": request.question,
        "database_id": str(request.database_id),
        "db_url": db_url,
        "blocked_tables": conn.blocked_tables or [],
        "mdl": {}, "mdl_version": None,
        "sql_query": "", "sql_result": [], "result_columns": [],
        "answer": "", "steps": [], "error": None, "retry_count": 0,
        "query_type": "final", "exploration_context": "", "exploration_count": 0,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event': 'connected', 'data': True})}\n\n"
        last_steps_len = 0
        try:
            async for event in agent_graph.astream(initial_state):
                # LangGraph yields updates per node
                for node_name, state_update in event.items():
                    # Check for new steps
                    current_steps = state_update.get("steps", [])
                    if len(current_steps) > last_steps_len:
                        for i in range(last_steps_len, len(current_steps)):
                            yield f"data: {json.dumps({'event': 'step', 'data': current_steps[i]})}\n\n"
                        last_steps_len = len(current_steps)
                    
                    # Check for SQL
                    if "sql_query" in state_update and state_update["sql_query"]:
                        yield f"data: {json.dumps({'event': 'sql', 'data': state_update['sql_query']})}\n\n"
                    
                    # Check for Result
                    if "sql_result" in state_update and state_update["sql_result"]:
                        result_data = {
                            "rows": state_update["sql_result"],
                            "columns": state_update.get("result_columns", [])
                        }
                        yield f"data: {json.dumps({'event': 'result', 'data': result_data})}\n\n"
                    
                    # Check for Error
                    if "error" in state_update and state_update["error"]:
                        yield f"data: {json.dumps({'event': 'error', 'data': state_update['error']})}\n\n"
                    
                    # Check for Answer
                    if "answer" in state_update and state_update["answer"]:
                        yield f"data: {json.dumps({'event': 'answer', 'data': state_update['answer']})}\n\n"
            
            yield "data: {\"event\": \"done\"}\n\n"
            
        except Exception as e:
            logger.error("Streaming failed: %s", str(e))
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
