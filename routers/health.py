from __future__ import annotations

import os

from fastapi import APIRouter

from services.ghost_build import ghost_cli_status
from services.redis_service import redis_service

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    try:
        redis_state = "connected" if await redis_service.ping() else "unavailable"
    except Exception:
        redis_state = "unavailable"
    ghost_status = ghost_cli_status()
    return {
        "status": "ok" if redis_state == "connected" else "degraded",
        "redis": redis_state,
        "tinyfish": "configured" if os.getenv("TINYFISH_API_KEY") else "missing",
        "vapi": "api_configured" if os.getenv("VAPI_API_KEY") else "custom_llm_ready",
        "publisher": "senso" if os.getenv("SENSO_API_KEY") and os.getenv("SENSO_API_URL") else "local",
        "ghost_build": "installed" if ghost_status["installed"] else "missing",
        "mode": os.getenv("APP_MODE", "demo"),
    }
