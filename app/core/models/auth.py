from datetime import datetime
import uuid

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    Represents a registered user of the Database Intelligence Agent.
    Stores authentication details and serves as the primary entity for session management.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        comment="Unique identifier for the user"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True,
        comment="User's email address, used for login"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        comment="Bcrypt hashed version of the user's password"
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        comment="Timestamp of when the user account was created"
    )
