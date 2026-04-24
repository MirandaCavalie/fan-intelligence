from __future__ import annotations

from fastapi import APIRouter

from models.fan import normalize_handle
from services.publisher import publisher

router = APIRouter()


@router.post("/publish/{creator_handle}")
async def publish_creator(creator_handle: str) -> dict:
    result = await publisher.publish_creator_report(normalize_handle(creator_handle))
    return result.model_dump(mode="json")
