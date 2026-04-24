from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


SourceTool = Literal["seed", "tinyfish_live", "tinyfish_demo", "ghost"]


class EngagementEvent(BaseModel):
    platform: str
    event_type: str
    content: str
    timestamp: datetime | None = None
    post_url: str | None = None


class FanProfile(BaseModel):
    handle: str
    display_name: str
    bio: str = ""
    platforms: list[str] = Field(default_factory=list)
    follower_count: int = 0
    comment_count: int = 0
    reply_count: int = 0
    cross_platform: bool = False
    raw_comments: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    score: int = 0
    reason: str = ""
    suggested_action: str = ""
    creator_handle: str
    source_tool: SourceTool = "seed"
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_url: str | None = None
    engagement_events: list[EngagementEvent] = Field(default_factory=list)

    @property
    def normalized_creator(self) -> str:
        return normalize_handle(self.creator_handle)

    @property
    def normalized_handle(self) -> str:
        return normalize_handle(self.handle)


class FanSummary(BaseModel):
    handle: str
    display_name: str
    score: int
    platforms: list[str]
    reason: str
    suggested_action: str
    source_urls: list[str]
    source_tool: SourceTool = "seed"


def normalize_handle(handle: str) -> str:
    value = handle.strip()
    if not value:
        return value
    return value if value.startswith("@") else f"@{value}"
