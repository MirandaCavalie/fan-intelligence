from __future__ import annotations

import os

from models.fan import FanProfile
from services.redis_service import RedisService, redis_service


class ProfileStore:
    def __init__(self, redis_client: RedisService | None = None) -> None:
        self.redis = redis_client or redis_service
        self.ghost_enabled = bool(os.getenv("GHOST_API_URL") and os.getenv("GHOST_ADMIN_API_KEY"))

    async def upsert_profile(self, profile: FanProfile) -> None:
        await self.redis.upsert_fan(profile)
        if self.ghost_enabled:
            from services.ghost import ghost_upsert_profile

            try:
                await ghost_upsert_profile(profile)
            except Exception as exc:
                await self.redis.push_sponsor_trace(
                    profile.creator_handle,
                    {"sponsor": "Ghost", "operation": "fallback", "detail": f"Redis-only profile store: {exc}"},
                )

    async def get_profile(self, creator_handle: str, fan_handle: str) -> FanProfile | None:
        return await self.redis.get_profile(creator_handle, fan_handle)

    async def list_profiles(self, creator_handle: str, limit: int = 10) -> list[FanProfile]:
        return await self.redis.list_top_fans(creator_handle, limit)


profile_store = ProfileStore()
