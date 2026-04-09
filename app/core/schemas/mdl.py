from datetime import datetime

from pydantic import BaseModel, Field
import uuid


class MDLColumnInfo(BaseModel):
    description: str
    is_metric: bool = False
    is_date: bool = False
    aggregatable: bool = False
    data_type: str
    enum_values: list[str] | None = None


class MDLTableInfo(BaseModel):
    description: str
    business_purpose: str = ""
    columns: dict[str, MDLColumnInfo] = {}
    common_filters: list[str] = []
    join_hints: dict[str, str] = {}
    example_questions: list[str] = []


class MDLResponse(BaseModel):
    id: int
    database_id: uuid.UUID
    name: str
    version: int
    is_active: bool
    is_generating: bool
    schema_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class MDLVersionSummary(BaseModel):
    id: int
    version: int
    is_active: bool
    is_generating: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MDLRefreshRequest(BaseModel):
    database_id: uuid.UUID
    name: str = Field(default="production_db")
    blocked_tables: list[str] | None = Field(
        default=None,
        description="Override default blocked tables. If None, uses BLOCKED_TABLES env var.",
    )


class MDLRefreshResponse(BaseModel):
    message: str
    mdl_name: str
    current_version: int | None
    status: str  # "started", "already_running", "skipped"
