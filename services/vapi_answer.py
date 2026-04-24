from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from models.fan import FanProfile, normalize_handle
from services.redis_ai import search_fan_memory
from services.redis_service import RedisService, redis_service


def message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            elif item:
                parts.append(str(item))
        return " ".join(parts)
    return str(content or "")


def last_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            text = message_content_to_text(message.get("content"))
            if text:
                return text
    return "Who are my top fans and what should I do with them?"


def system_text(messages: list[dict[str, Any]]) -> str:
    return "\n".join(
        message_content_to_text(message.get("content"))
        for message in messages
        if message.get("role") == "system"
    )


def extract_handle_from_text(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}\s*[:=]\s*(@?[A-Za-z0-9_.-]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return normalize_handle(match.group(1))


def parse_persona_model(model: str) -> tuple[str | None, str | None]:
    if not model.startswith("faniq-persona:"):
        return None, None
    raw = model.split(":", 1)[1]
    parts = [part for part in raw.split(":") if part]
    if len(parts) >= 2:
        return normalize_handle(parts[0]), normalize_handle(parts[1])
    if len(parts) == 1:
        return None, normalize_handle(parts[0])
    return None, None


def extract_creator(body: dict[str, Any], messages: list[dict[str, Any]]) -> str:
    model_creator, _ = parse_persona_model(str(body.get("model", "")))
    text = system_text(messages)
    creator = (
        body.get("creator_handle")
        or body.get("metadata", {}).get("creator_handle")
        or body.get("call", {}).get("metadata", {}).get("creator_handle")
        or model_creator
        or extract_handle_from_text(text, "creator_handle")
        or extract_handle_from_text(text, "creator")
    )
    if not creator:
        match = re.search(r"@[A-Za-z0-9_.-]+", text)
        creator = match.group(0) if match else os.getenv("CREATOR_HANDLE", "@lexfridman")
    return normalize_handle(str(creator))


def extract_fan(body: dict[str, Any], messages: list[dict[str, Any]]) -> str | None:
    _, model_fan = parse_persona_model(str(body.get("model", "")))
    text = system_text(messages)
    fan = (
        body.get("fan_handle")
        or body.get("metadata", {}).get("fan_handle")
        or body.get("metadata", {}).get("selected_fan")
        or body.get("call", {}).get("metadata", {}).get("fan_handle")
        or model_fan
        or extract_handle_from_text(text, "fan_handle")
        or extract_handle_from_text(text, "fan")
    )
    return normalize_handle(str(fan)) if fan else None


def deterministic_answer(
    creator_handle: str,
    fans: list[FanProfile],
    memories: list[dict[str, Any]] | None = None,
) -> str:
    if not fans:
        return (
            f"I do not have fan data for {creator_handle} yet. Run a scan first, then I can rank the highest-signal fans "
            "and recommend exactly who to activate."
        )

    memories = memories or []
    lead = fans[0]
    answer = (
        f"Your highest-signal fan is {lead.display_name} ({lead.handle}) with score {lead.score} because {lead.reason}. "
        f"The next move is: {lead.suggested_action}"
    )
    if len(fans) > 1:
        names = ", ".join(f"{fan.display_name} ({fan.handle})" for fan in fans[1:3])
        answer += f" After that, prioritize {names}; they have repeated, source-backed engagement worth acting on."
    if memories:
        memory = memories[0]
        answer += (
            f" Redis memory backs this with a snippet from {memory.get('display_name')}: "
            f"\"{memory.get('content')}\""
        )
    return answer


async def maybe_anthropic_text(
    system: str,
    user_message: str,
    max_tokens: int = 180,
) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        return text.strip() or None
    except Exception:
        return None


async def maybe_anthropic_intelligence_answer(
    creator_handle: str,
    fans: list[FanProfile],
    user_message: str,
    memories: list[dict[str, Any]] | None = None,
) -> str | None:
    if not fans:
        return None

    context = "\n".join(
        f"- {fan.display_name} ({fan.handle}), score {fan.score}: {fan.reason}. Action: {fan.suggested_action}"
        for fan in fans[:5]
    )
    memory_context = "\n".join(
        f"- {memory.get('display_name')} ({memory.get('fan_handle')}): {memory.get('content')}"
        for memory in (memories or [])[:5]
    )
    system = (
        "You are FanIQ, a concise voice assistant for creators. Answer in 1-3 short spoken sentences. "
        "Use only the fan data provided. Mention concrete names, handles, scores, reasons, and next actions. "
        "No markdown, no bullet points, and no claims beyond the provided data."
    )
    prompt = (
        f"Creator: {creator_handle}\nFan data:\n{context}\n"
        f"Redis AI memory snippets:\n{memory_context or 'No memory snippets.'}\nQuestion: {user_message}"
    )
    return await maybe_anthropic_text(system, prompt, max_tokens=180)


def deterministic_persona_answer(creator_handle: str, fan: FanProfile | None, user_message: str) -> str:
    if not fan:
        return (
            "I do not have enough fan data to synthesize that persona yet. Run a scan first, select a fan, "
            "and then I can ground the persona in saved comments."
        )

    comment = fan.raw_comments[0] if fan.raw_comments else fan.reason
    return (
        f"I am a synthetic FanIQ persona based on {fan.display_name}'s public engagement, not the real person. "
        f"Based on the saved comments, I would engage because: \"{comment}\" "
        f"If you want to activate someone like me, {fan.suggested_action}"
    )


async def maybe_anthropic_persona_answer(
    creator_handle: str,
    fan: FanProfile | None,
    user_message: str,
) -> str | None:
    if not fan:
        return None

    comments = "\n".join(f"- {comment}" for comment in fan.raw_comments[:6])
    system = (
        f"You are a synthetic FanIQ fan persona based on public engagement from {fan.display_name} ({fan.handle}). "
        "You are not the real person and must clearly disclose that in the first response. "
        "Stay grounded in the provided bio, comments, reason, and suggested action. "
        "Do not invent private facts. Keep responses to 1-3 short spoken sentences with no markdown."
    )
    prompt = (
        f"Creator: {creator_handle}\nFan: {fan.display_name} ({fan.handle})\nBio: {fan.bio}\n"
        f"Score reason: {fan.reason}\nSuggested action: {fan.suggested_action}\n"
        f"Saved comments:\n{comments or 'No saved comments.'}\nQuestion: {user_message}"
    )
    return await maybe_anthropic_text(system, prompt, max_tokens=180)


async def find_profile_by_fan(redis: RedisService, creator: str, fan_handle: str) -> FanProfile | None:
    profile = await redis.get_profile(creator, fan_handle)
    if profile:
        return profile

    pattern = f"fan_profile:*:{normalize_handle(fan_handle)}"
    keys = await redis.client.keys(pattern)
    for key in keys:
        raw = await redis.client.get(key)
        if raw:
            return FanProfile.model_validate_json(raw)
    return None


async def build_vapi_answer(
    body: dict[str, Any],
    redis_client: RedisService | None = None,
) -> dict[str, Any]:
    redis = redis_client or redis_service
    messages = body.get("messages", []) or []
    creator = extract_creator(body, messages)
    user_message = last_user_message(messages)
    model = str(body.get("model", "faniq-intelligence"))
    mode = "persona" if model.startswith("faniq-persona:") else "intelligence"

    fans: list[FanProfile] = []
    memories: list[dict[str, Any]] = []
    fan: FanProfile | None = None

    if mode == "persona":
        fan_handle = extract_fan(body, messages)
        if fan_handle:
            try:
                fan = await find_profile_by_fan(redis, creator, fan_handle)
            except Exception:
                fan = None
        answer = await maybe_anthropic_persona_answer(creator, fan, user_message)
        if not answer:
            answer = deterministic_persona_answer(creator, fan, user_message)
    else:
        try:
            fans = await redis.list_top_fans(creator, limit=5)
        except Exception:
            fans = []
        try:
            memories = await search_fan_memory(redis, creator, user_message, limit=5)
        except Exception:
            memories = []
        answer = await maybe_anthropic_intelligence_answer(creator, fans, user_message, memories)
        if not answer:
            answer = deterministic_answer(creator, fans, memories)

    try:
        await redis.push_sponsor_trace(
            creator,
            {
                "sponsor": "Vapi",
                "operation": "Custom LLM + Redis",
                "detail": (
                    f"Mode B persona for {fan.handle if fan else 'missing fan'}"
                    if mode == "persona"
                    else f"Mode A answered from {len(fans)} profiles and {len(memories)} memory snippets"
                ),
            },
        )
    except Exception:
        pass

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
    }


def chunk_text(text: str, max_chars: int = 36) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current + " ")
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [""]


def sse_data(payload: dict[str, Any] | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


async def stream_vapi_answer(
    body: dict[str, Any],
    redis_client: RedisService | None = None,
) -> AsyncIterator[str]:
    response = await build_vapi_answer(body, redis_client=redis_client)
    call_id = response["id"]
    created = response["created"]
    model = response["model"]
    content = response["choices"][0]["message"]["content"]

    yield sse_data(
        {
            "id": call_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}],
        }
    )

    for text_chunk in chunk_text(content):
        yield sse_data(
            {
                "id": call_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"content": text_chunk}, "finish_reason": None}],
            }
        )
        await asyncio.sleep(0)

    yield sse_data(
        {
            "id": call_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
    )
    yield sse_data("[DONE]")
