from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.models.auth import User
from app.core.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.core.services.auth import get_password_hash, verify_password, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user in the system.
    Hashes the password before storing it in the database.
    """
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(current_user: User = Depends(get_current_user)):
    """
    A simple endpoint to verify HTTP Basic credentials.
    If the 'current_user' dependency succeeds, the credentials are valid.
    """
    return {"message": "Authenticated successfully", "user": current_user.email}
