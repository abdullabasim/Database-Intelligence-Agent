from datetime import datetime

import uuid
from sqlalchemy import Boolean, Integer, JSON, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MDLSchema(Base):
    """
    Stores enriched semantic metadata (Metadata Layer) for a database connection.
    Contains business descriptions, metrics, and query guidelines.
    """
    __tablename__ = "mdl_schemas"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        comment="Auto-incrementing primary key"
    )
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_connections.id", ondelete="CASCADE"), index=True,
        comment="The connection this schema enrichment belongs to"
    )
    name: Mapped[str] = mapped_column(
        String(100), index=True,
        comment="Versioned name or identifier for the MDL"
    )
    version: Mapped[int] = mapped_column(
        Integer,
        comment="Incremental version number"
    )
    schema_json: Mapped[dict] = mapped_column(
        JSON,
        comment="The actual enriched schema object produced by the LLM"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="True if this version is the one currently used for queries"
    )
    is_generating: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="True if a background task is still constructing this MDL"
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        comment="Timestamp of when this version was created"
    )
