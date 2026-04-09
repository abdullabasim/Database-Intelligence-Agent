import pytest
from httpx import AsyncClient
import uuid
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_ask_question_unauthorized(client: AsyncClient):
    """Test passing a question without auth."""
    payload = {"question": "How many users?", "database_id": str(uuid.uuid4())}
    response = await client.post("/agent/ask", json=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_ask_question_db_not_found(client: AsyncClient):
    """Test asking a question about a non-existent database."""
    email = "agent@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    payload = {"question": "How many users?", "database_id": str(uuid.uuid4())}
    response = await client.post("/agent/ask", json=payload, auth=(email, pwd))
    assert response.status_code == 404
    assert response.json()["detail"] == "Database connection not found."

@pytest.mark.asyncio
async def test_ask_question_success_mocked(client: AsyncClient):
    """Test asking a question with a mocked agent graph response."""
    email = "agent_mock@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    # Create DB connection
    db_payload = {
        "name": "Mock DB", "host": "h", "port": 5432, "db_name": "d", 
        "username": "u", "password": "p"
    }
    resp = await client.post("/databases", json=db_payload, auth=(email, pwd))
    db_id = resp.json()["id"]
    
    # Mock the agent_graph.ainvoke
    mock_final_state = {
        "answer": "There are 42 records.",
        "sql_query": "SELECT COUNT(*) FROM records;",
        "sql_result": [{"count": 42}],
        "result_columns": ["count"],
        "steps": ["Step 1", "Step 2"],
        "mdl_version": 1,
        "error": None
    }
    
    with patch("app.routes.agent.agent_graph.ainvoke", return_value=mock_final_state):
        payload = {"question": "Total records?", "database_id": db_id}
        response = await client.post("/agent/ask", json=payload, auth=(email, pwd))
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "There are 42 records."
        assert data["sql_query"] == "SELECT COUNT(*) FROM records;"
        assert data["mdl_version"] == 1
