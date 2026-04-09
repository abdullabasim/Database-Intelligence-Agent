import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_mdl_operations_unauthorized(client: AsyncClient):
    """Test that MDL operations fail without auth."""
    db_id = uuid.uuid4()
    response = await client.get(f"/mdl/latest?database_id={db_id}")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_mdl_latest_not_found(client: AsyncClient):
    """Test latest MDL returns 404 when none exists."""
    email = "mdltest@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    # Create a DB connection first
    db_payload = {
        "name": "MDL Test DB",
        "host": "localhost",
        "port": 5432,
        "db_name": "testdb",
        "username": "testuser",
        "password": "testpassword"
    }
    resp = await client.post("/databases", json=db_payload, auth=(email, pwd))
    db_id = resp.json()["id"]
    
    # Try to get latest MDL - should be 404
    response = await client.get(f"/mdl/latest?database_id={db_id}", auth=(email, pwd))
    assert response.status_code == 404
    assert response.json()["error_code"] == "MDL_NOT_FOUND"

@pytest.mark.asyncio
async def test_mdl_refresh_trigger(client: AsyncClient):
    """Test triggering MDL refresh."""
    email = "refresh@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    resp = await client.post("/databases", json={
        "name": "Refresh DB", "host": "h", "port": 5432, "db_name": "d", "username": "u", "password": "p"
    }, auth=(email, pwd))
    db_id = resp.json()["id"]
    
    # Trigger refresh
    response = await client.post(
        "/mdl/refresh", 
        json={"database_id": db_id, "name": "schema_v1"}, 
        auth=(email, pwd)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "started"
