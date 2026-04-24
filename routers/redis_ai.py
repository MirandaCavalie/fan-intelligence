from __future__ import annotations

from fastapi import APIRouter

from models.fan import normalize_handle
from services.redis_ai import search_fan_memory
from services.redis_service import redis_service

router = APIRouter()


@router.get("/memory/{creator_handle}/search")
async def memory_search(creator_handle: str, q: str = "top fans", limit: int = 5) -> dict:
    creator = normalize_handle(creator_handle)
    try:
        results = await search_fan_memory(redis_service, creator, q, limit=limit)
    except Exception as exc:
        return {"creator_handle": creator, "query": q, "results": [], "error": str(exc)}
    return {"creator_handle": creator, "query": q, "results": results}
