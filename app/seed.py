import asyncio
import uuid
from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.models.auth import User
from app.core.services.auth import get_password_hash

async def seed_core():
    """
    Seeds the core application with a default administrator user.
    """
    print("--- Starting Core Database Seeding ---")
    
    async with async_session_factory() as session:
        # Check if default user already exists
        result = await session.execute(select(User).filter_by(email="admin@example.com"))
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            admin_user = User(
                id=uuid.uuid4(),
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
            )
            session.add(admin_user)
            await session.commit()
            print("SUCCESS: Created default user 'admin@example.com' with password 'admin123'")
        else:
            print("INFO: Default user 'admin@example.com' already exists. Skipping.")

    print("--- Seeding Complete ---")

if __name__ == "__main__":
    asyncio.run(seed_core())
