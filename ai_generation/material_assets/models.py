from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    created_at: datetime = Field(default_factory=_utc_now)


class AssetRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    original_relpath: str
    staged_relpath: str | None = None
    mask_relpath: str | None = None
    room_type: str | None = None
    style_tags: list[str] = Field(default_factory=list)
    analysis: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
