from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class DatabaseConnectionCreate(BaseModel):
    name: str
    host: str
    port: int = 5432
    db_name: str
    username: str
    password: str
    blocked_tables: List[str] = []

class DatabaseConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    blocked_tables: Optional[List[str]] = None

class DatabaseConnectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    port: int
    db_name: str
    username: str
    blocked_tables: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DatabaseConnectionListResponse(BaseModel):
    items: List[DatabaseConnectionResponse]
    total: int
    page: int
    size: int
