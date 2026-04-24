from __future__ import annotations

import json
import os
from typing import Any

import redis.asyncio as redis
from dotenv import load_dotenv

from models.fan import FanProfile, FanSummary, normalize_handle
from models.job import PublishResult, ScanEvent, ScanJob

load_dotenv()


def _json_default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default, separators=(",", ":"))


class RedisService:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def ping(self) -> bool:
        return bool(await self.client.ping())

    async def clear_creator(self, creator_handle: str) -> None:
        creator = normalize_handle(creator_handle)
        profile_keys = await self.client.keys(f"fan_profile:{creator}:*")
        keys = [
            f"fans:{creator}",
            f"events:{creator}",
            f"sponsor_trace:{creator}",
            f"publish:{creator}",
            *profile_keys,
        ]
        if keys:
            await self.client.delete(*keys)

    async def upsert_fan(self, profile: FanProfile) -> None:
        creator = normalize_handle(profile.creator_handle)
        fan = normalize_handle(profile.handle)
        data = profile.model_dump(mode="json")
        await self.client.zadd(f"fans:{creator}", {fan: profile.score})
        await self.client.set(f"fan_profile:{creator}:{fan}", dumps(data))
        await self.push_event(
            creator,
            ScanEvent(
                type="redis_write",
                sponsor="redis",
                message=f"Stored {fan} profile and score",
                command=f"ZADD fans:{creator} {profile.score} {fan}",
            ),
        )
        await self.push_sponsor_trace(
            creator,
            {
                "sponsor": "Redis",
                "operation": "ZADD + SET",
                "detail": f"{fan} scored {profile.score}",
            },
        )

    async def get_profile(self, creator_handle: str, fan_handle: str) -> FanProfile | None:
        creator = normalize_handle(creator_handle)
        fan = normalize_handle(fan_handle)
        raw = await self.client.get(f"fan_profile:{creator}:{fan}")
        if not raw:
            return None
        return FanProfile.model_validate_json(raw)

    async def list_top_fans(self, creator_handle: str, limit: int = 10) -> list[FanProfile]:
        creator = normalize_handle(creator_handle)
        rows = await self.client.zrevrange(f"fans:{creator}", 0, limit - 1, withscores=True)
        fans: list[FanProfile] = []
        for fan_handle, score in rows:
            profile = await self.get_profile(creator, fan_handle)
            if profile:
                profile.score = int(score)
                fans.append(profile)
        await self.push_sponsor_trace(
            creator,
            {
                "sponsor": "Redis",
                "operation": "ZREVRANGE",
                "detail": f"Fetched top {len(fans)} fans",
            },
        )
        return fans

    async def fan_count(self, creator_handle: str) -> int:
        return int(await self.client.zcard(f"fans:{normalize_handle(creator_handle)}"))

    async def fan_summary_response(self, creator_handle: str, limit: int = 10) -> dict[str, Any]:
        creator = normalize_handle(creator_handle)
        fans = await self.list_top_fans(creator, limit=limit)
        summaries = [
            FanSummary(
                handle=fan.handle,
                display_name=fan.display_name,
                score=fan.score,
                platforms=fan.platforms,
                reason=fan.reason,
                suggested_action=fan.suggested_action,
                source_urls=fan.source_urls,
                source_tool=fan.source_tool,
            ).model_dump()
            for fan in fans
        ]
        return {"creator_handle": creator, "total_fans": await self.fan_count(creator), "top_fans": summaries}

    async def save_scan_job(self, job: ScanJob) -> None:
        await self.client.set(f"scan:{job.job_id}", dumps(job.model_dump(mode="json")), ex=3600)

    async def get_scan_job(self, job_id: str) -> ScanJob | None:
        raw = await self.client.get(f"scan:{job_id}")
        if not raw:
            return None
        return ScanJob.model_validate_json(raw)

    async def push_scan_event(self, job_id: str, event: ScanEvent) -> None:
        await self.client.rpush(f"scan_events:{job_id}", dumps(event.model_dump(mode="json")))
        await self.client.expire(f"scan_events:{job_id}", 3600)

    async def scan_events(self, job_id: str, start: int = 0) -> list[ScanEvent]:
        rows = await self.client.lrange(f"scan_events:{job_id}", start, -1)
        return [ScanEvent.model_validate_json(row) for row in rows]

    async def push_event(self, creator_handle: str, event: ScanEvent) -> None:
        creator = normalize_handle(creator_handle)
        await self.client.lpush(f"events:{creator}", dumps(event.model_dump(mode="json")))
        await self.client.ltrim(f"events:{creator}", 0, 99)

    async def recent_events(self, creator_handle: str, limit: int = 25) -> list[ScanEvent]:
        rows = await self.client.lrange(f"events:{normalize_handle(creator_handle)}", 0, limit - 1)
        return [ScanEvent.model_validate_json(row) for row in rows]

    async def push_sponsor_trace(self, creator_handle: str, trace: dict[str, str]) -> None:
        creator = normalize_handle(creator_handle)
        await self.client.lpush(f"sponsor_trace:{creator}", dumps(trace))
        await self.client.ltrim(f"sponsor_trace:{creator}", 0, 49)

    async def sponsor_trace(self, creator_handle: str, limit: int = 20) -> list[dict[str, str]]:
        rows = await self.client.lrange(f"sponsor_trace:{normalize_handle(creator_handle)}", 0, limit - 1)
        return [json.loads(row) for row in rows]

    async def save_publish_result(self, result: PublishResult) -> None:
        await self.client.set(f"publish:{normalize_handle(result.creator_handle)}", dumps(result.model_dump(mode="json")))

    async def get_publish_result(self, creator_handle: str) -> PublishResult | None:
        raw = await self.client.get(f"publish:{normalize_handle(creator_handle)}")
        if not raw:
            return None
        return PublishResult.model_validate_json(raw)


redis_service = RedisService()
