import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login using Basic Auth."""
    # First, register
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"}
    )
    
    # Then login
    response = await client.post(
        "/auth/login",
        auth=("login@example.com", "password123")
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "login@example.com"

@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient):
    """Test login with wrong password."""
    # Register
    await client.post(
        "/auth/register",
        json={"email": "fail@example.com", "password": "password123"}
    )
    
    # Wrong password
    response = await client.post(
        "/auth/login",
        auth=("fail@example.com", "wrongpassword")
    )
    assert response.status_code == 401
