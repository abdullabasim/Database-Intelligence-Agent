from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.models.auth import User

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Basic Auth security scheme
security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password matches its hashed version.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Transforms a plain-text password into a secure Bcrypt hash.
    """
    return pwd_context.hash(password)


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    A FastAPI dependency that authenticates a user using HTTP Basic credentials.
    Returns the User model if successful, otherwise raises 401 Unauthorized.
    """
    email = credentials.username
    password = credentials.password
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(password, user.hashed_password):
        raise credentials_exception
    return user
