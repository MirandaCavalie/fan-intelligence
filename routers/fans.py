from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.fan import normalize_handle
from services.redis_service import redis_service

router = APIRouter()


@router.get("/fans/{creator_handle}")
async def top_fans(creator_handle: str, limit: int = 10) -> dict:
    creator = normalize_handle(creator_handle)
    try:
        return await redis_service.fan_summary_response(creator, limit)
    except Exception as exc:
        return {"creator_handle": creator, "total_fans": 0, "top_fans": [], "error": str(exc)}


@router.get("/fan/{creator_handle}/{fan_handle}")
async def single_fan(creator_handle: str, fan_handle: str) -> dict:
    profile = await redis_service.get_profile(normalize_handle(creator_handle), normalize_handle(fan_handle))
    if not profile:
        raise HTTPException(status_code=404, detail="fan not found")
    return profile.model_dump(mode="json")


@router.get("/events/{creator_handle}")
async def recent_events(creator_handle: str) -> dict:
    creator = normalize_handle(creator_handle)
    try:
        events = await redis_service.recent_events(creator)
        trace = await redis_service.sponsor_trace(creator)
        publish = await redis_service.get_publish_result(creator)
    except Exception as exc:
        return {"creator_handle": creator, "events": [], "sponsor_trace": [], "publish": None, "error": str(exc)}
    return {
        "creator_handle": creator,
        "events": [event.model_dump(mode="json") for event in events],
        "sponsor_trace": trace,
        "publish": publish.model_dump(mode="json") if publish else None,
    }
