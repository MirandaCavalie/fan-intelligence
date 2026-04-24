from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.vapi_answer import build_vapi_answer

router = APIRouter()


@router.post("/vapi/llm")
async def vapi_llm(body: dict[str, Any]) -> dict[str, Any]:
    return await build_vapi_answer(body)


@router.post("/vapi/answer")
async def local_vapi_answer(body: dict[str, Any]) -> dict[str, Any]:
    return await build_vapi_answer(body)
