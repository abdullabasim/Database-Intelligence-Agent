from datetime import datetime
import uuid

from sqlalchemy import String, Integer, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DatabaseConnection(Base):
    """
    Stores connection credentials and metadata for tenant databases.
    Allows the agent to connect to multiple external data sources securely.
    """
    __tablename__ = "database_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        comment="Unique identifier for the connection"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True,
        comment="The owner of this connection"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        comment="Human-readable name for the database (e.g., 'Production')"
    )
    host: Mapped[str] = mapped_column(
        String(255),
        comment="Database host address"
    )
    port: Mapped[int] = mapped_column(
        Integer, default=5432,
        comment="Database port number"
    )
    db_name: Mapped[str] = mapped_column(
        String(100),
        comment="Name of the specific database to connect to"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        comment="Database user with READ-ONLY permissions"
    )
    encrypted_password: Mapped[str] = mapped_column(
        String(1000),
        comment="Fernet-encrypted password for the database user"
    )
    blocked_tables: Mapped[list[str]] = mapped_column(
        JSON, default=list,
        comment="List of specific tables that should be hidden from the agent"
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        comment="Timestamp of when the connection was added"
    )

    @property
    def async_url(self) -> str:
        """
        Constructs a SQLAlchemy asynchronous connection string (asyncpg).
        Decrypts the password on the fly.
        """
        from app.core.services.crypto import decrypt_password
        pwd = decrypt_password(self.encrypted_password)
        return f"postgresql+asyncpg://{self.username}:{pwd}@{self.host}:{self.port}/{self.db_name}"

    @property
    def sync_url(self) -> str:
        """
        Constructs a SQLAlchemy synchronous connection string (psycopg2).
        Used for schema inspection and migrations.
        """
        from app.core.services.crypto import decrypt_password
        pwd = decrypt_password(self.encrypted_password)
        return f"postgresql+psycopg2://{self.username}:{pwd}@{self.host}:{self.port}/{self.db_name}"
