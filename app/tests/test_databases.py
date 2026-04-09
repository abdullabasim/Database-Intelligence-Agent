import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_list_databases(client: AsyncClient):
    """Test creating a database connection and listing with pagination."""
    # 1. Register & Login (Implicitly handled by auth in client fixture if needed, 
    # but here we'll do it explicitly for simplicity)
    email = "dbtest@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    # 2. Create DB Connection
    db_payload = {
        "name": "Test DB",
        "host": "localhost",
        "port": 5432,
        "db_name": "testdb",
        "username": "testuser",
        "password": "testpassword",
        "blocked_tables": ["secret"]
    }
    response = await client.post("/databases", json=db_payload, auth=(email, pwd))
    assert response.status_code == 201
    db_id = response.json()["id"]
    
    # 3. List DB Connections (Pagination)
    response = await client.get("/databases?limit=10&offset=0", auth=(email, pwd))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["name"] == "Test DB"
    assert data["page"] == 1
    assert data["size"] == 10

@pytest.mark.asyncio
async def test_update_database(client: AsyncClient):
    """Test updating a database connection."""
    email = "update@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    # Create
    db_payload = {
        "name": "Old Name",
        "host": "localhost",
        "port": 5432,
        "db_name": "testdb",
        "username": "testuser",
        "password": "testpassword"
    }
    resp = await client.post("/databases", json=db_payload, auth=(email, pwd))
    db_id = resp.json()["id"]
    
    # Update
    update_payload = {"name": "New Name"}
    response = await client.put(f"/databases/{db_id}", json=update_payload, auth=(email, pwd))
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"

@pytest.mark.asyncio
async def test_delete_database(client: AsyncClient):
    """Test deleting a database connection."""
    email = "delete@example.com"
    pwd = "password123"
    await client.post("/auth/register", json={"email": email, "password": pwd})
    
    # Create
    db_payload = {
        "name": "To Delete",
        "host": "localhost",
        "port": 5432,
        "db_name": "testdb",
        "username": "testuser",
        "password": "testpassword"
    }
    resp = await client.post("/databases", json=db_payload, auth=(email, pwd))
    db_id = resp.json()["id"]
    
    # Delete
    response = await client.delete(f"/databases/{db_id}", auth=(email, pwd))
    assert response.status_code == 204
    
    # Verify 404
    response = await client.get(f"/databases/{db_id}", auth=(email, pwd))
    assert response.status_code == 404
