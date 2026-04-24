from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from services.vapi_answer import build_vapi_answer, stream_vapi_answer
from services.vapi_setup import get_vapi_client_config

router = APIRouter()


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Any:
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    if body.get("stream"):
        return StreamingResponse(
            stream_vapi_answer(body),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return await build_vapi_answer(body)


@router.post("/vapi/llm")
async def vapi_llm(body: dict[str, Any]) -> dict[str, Any]:
    return await build_vapi_answer(body)


@router.post("/vapi/answer")
async def local_vapi_answer(body: dict[str, Any]) -> dict[str, Any]:
    return await build_vapi_answer(body)


@router.get("/vapi/client-config")
async def vapi_client_config(creator_handle: str = "@lexfridman", fan_handle: str | None = None) -> dict[str, Any]:
    return get_vapi_client_config(creator_handle, fan_handle)
