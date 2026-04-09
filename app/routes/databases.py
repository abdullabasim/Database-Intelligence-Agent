from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db, get_dynamic_async_engine
from app.core.models.tenant import DatabaseConnection
from app.core.models.auth import User
from app.core.schemas.tenant import DatabaseConnectionCreate, DatabaseConnectionUpdate, DatabaseConnectionResponse, DatabaseConnectionListResponse
from app.core.services.auth import get_current_user
from app.core.services.crypto import encrypt_password

router = APIRouter(prefix="/databases", tags=["Databases"])

@router.post("", response_model=DatabaseConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_database_connection(
    conn_data: DatabaseConnectionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Registers a new external database connection for the agent to query.
    Encrypts the provided password before storage.
    NOTE: It is highly recommended to use a READ-ONLY database user.
    """
    encrypted_pwd = encrypt_password(conn_data.password)
    
    new_conn = DatabaseConnection(
        user_id=user.id,
        name=conn_data.name,
        host=conn_data.host,
        port=conn_data.port,
        db_name=conn_data.db_name,
        username=conn_data.username,
        encrypted_password=encrypted_pwd,
        blocked_tables=conn_data.blocked_tables
    )
    
    db.add(new_conn)
    await db.commit()
    await db.refresh(new_conn)
    return new_conn

@router.get("", response_model=DatabaseConnectionListResponse)
async def list_database_connections(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Retrieves a paginated list of all database connections owned by the current user.
    Includes total count and navigation metadata.
    """
    query = select(DatabaseConnection).where(DatabaseConnection.user_id == user.id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get paginated items
    items_query = query.offset(offset).limit(limit)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total or 0,
        "page": (offset // limit + 1) if limit else 1,
        "size": limit
    }

@router.get("/{conn_id}", response_model=DatabaseConnectionResponse)
async def get_database_connection(
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Fetches details for a specific database connection by ID.
    Returns 404 if the connection does not exist or belongs to another user.
    """
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_id, DatabaseConnection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
        
    return conn

@router.put("/{conn_id}", response_model=DatabaseConnectionResponse)
async def update_database_connection(
    conn_id: uuid.UUID,
    conn_data: DatabaseConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Updates the configuration of an existing database connection.
    Only provided fields will be modified.
    """
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_id, DatabaseConnection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
        
    update_data = conn_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["encrypted_password"] = encrypt_password(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(conn, key, value)
        
    await db.commit()
    await db.refresh(conn)
    return conn

@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database_connection(
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Permanently removes a database connection and its associated MDL schemas.
    """
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_id, DatabaseConnection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
        
    await db.delete(conn)
    await db.commit()
    return None

@router.post("/{conn_id}/test-connection")
async def test_database_connection(
    conn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Verifies that the stored credentials are correct by attempting a 'SELECT 1' 
    on the target database.
    """
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == conn_id, DatabaseConnection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
        
    try:
        dynamic_engine = get_dynamic_async_engine(conn.async_url)
        async with dynamic_engine.connect() as dynamic_conn:
            from sqlalchemy import text
            await dynamic_conn.execute(text("SELECT 1"))
        return {"status": "success", "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
