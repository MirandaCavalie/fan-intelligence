from __future__ import annotations

import os

from fastapi import APIRouter

from services.redis_service import redis_service

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    try:
        redis_state = "connected" if await redis_service.ping() else "unavailable"
    except Exception:
        redis_state = "unavailable"
    return {
        "status": "ok" if redis_state == "connected" else "degraded",
        "redis": redis_state,
        "tinyfish": "configured" if os.getenv("TINYFISH_API_KEY") else "missing",
        "vapi": "ready",
        "publisher": "senso" if os.getenv("SENSO_API_KEY") and os.getenv("SENSO_API_URL") else "local",
        "mode": os.getenv("APP_MODE", "demo"),
    }
