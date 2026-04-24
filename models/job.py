from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


ScanStatus = Literal["queued", "running", "done", "failed"]
ScanEventType = Literal[
    "agent_step",
    "fan_found",
    "source_fetched",
    "redis_write",
    "publish",
    "vapi",
    "done",
    "error",
]


class ScanJob(BaseModel):
    job_id: str
    creator_handle: str
    platforms: list[str] = Field(default_factory=lambda: ["x"])
    demo_mode: bool = True
    status: ScanStatus = "queued"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_fans: int = 0
    error: str | None = None


class ScanEvent(BaseModel):
    type: ScanEventType
    sponsor: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fan: dict[str, Any] | None = None
    url: str | None = None
    command: str | None = None
    total_fans: int | None = None


class PublishResult(BaseModel):
    creator_handle: str
    published: bool
    url: str
    payment_enabled: bool = False
    publisher: str = "local"
    published_count: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
