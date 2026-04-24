from __future__ import annotations

import os
from typing import Any

from models.fan import FanProfile, normalize_handle
from services.redis_ai import search_fan_memory
from services.redis_service import RedisService, redis_service


def deterministic_answer(creator_handle: str, fans: list[FanProfile], memories: list[dict[str, Any]] | None = None) -> str:
    if not fans:
        return (
            f"I do not have fan data for {creator_handle} yet. Run a scan or seed the demo data, "
            "then I can rank the highest-signal fans and recommend actions."
        )

    memories = memories or []
    lead = fans[0]
    parts = [
        f"Your top fan is {lead.display_name} ({lead.handle}) with score {lead.score}: {lead.reason}. "
        f"Start by doing this: {lead.suggested_action}"
    ]
    if len(fans) > 1:
        names = ", ".join(f"{fan.display_name} ({fan.handle})" for fan in fans[1:3])
        parts.append(f"Next strongest fans are {names}; each has repeated, source-backed engagement worth acting on.")
    if len(fans) > 3:
        action_lines = " ".join(f"For {fan.display_name}, {fan.suggested_action}" for fan in fans[1:4])
        parts.append(action_lines)
    if memories:
        memory = memories[0]
        parts.append(
            f"Redis memory backs this with a snippet from {memory.get('display_name')}: "
            f"\"{memory.get('content')}\""
        )
    return " ".join(parts)


async def maybe_anthropic_answer(
    creator_handle: str,
    fans: list[FanProfile],
    user_message: str,
    memories: list[dict[str, Any]] | None = None,
) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not fans:
        return None

    try:
        from anthropic import AsyncAnthropic

        context = "\n".join(
            f"- {fan.display_name} ({fan.handle}), score {fan.score}: {fan.reason}. Action: {fan.suggested_action}"
            for fan in fans[:5]
        )
        memory_context = "\n".join(
            f"- {memory.get('display_name')} ({memory.get('fan_handle')}): {memory.get('content')}"
            for memory in (memories or [])[:5]
        )
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=220,
            system=(
                "You are FanIQ, a concise voice assistant for creators. Answer in 2-4 short sentences. "
                "Use only the fan data provided. Mention concrete names, reasons, and next actions."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Creator: {creator_handle}\nFan data:\n{context}\n"
                        f"Redis AI memory snippets:\n{memory_context}\nQuestion: {user_message}"
                    ),
                }
            ],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        return text.strip() or None
    except Exception:
        return None


async def build_vapi_answer(
    body: dict[str, Any],
    redis_client: RedisService | None = None,
) -> dict[str, Any]:
    redis = redis_client or redis_service
    creator_handle = (
        body.get("creator_handle")
        or body.get("metadata", {}).get("creator_handle")
        or body.get("call", {}).get("metadata", {}).get("creator_handle")
        or os.getenv("CREATOR_HANDLE", "@lexfridman")
    )
    creator = normalize_handle(creator_handle)
    messages = body.get("messages", [])
    user_message = "Who are my top fans and what should I do with them?"
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            user_message = content if isinstance(content, str) else str(content)
            break

    try:
        fans = await redis.list_top_fans(creator, limit=5)
    except Exception:
        fans = []
    try:
        memories = await search_fan_memory(redis, creator, user_message, limit=5)
    except Exception:
        memories = []
    answer = await maybe_anthropic_answer(creator, fans, user_message, memories)
    if not answer:
        answer = deterministic_answer(creator, fans, memories)

    try:
        await redis.push_sponsor_trace(
            creator,
            {
                "sponsor": "Vapi",
                "operation": "LLM + Redis memory",
                "detail": f"Answered from {len(fans)} profiles and {len(memories)} memory snippets",
            },
        )
    except Exception:
        pass

    return {
        "id": "chatcmpl-faniq-demo",
        "object": "chat.completion",
        "created": 0,
        "model": body.get("model", "faniq-intelligence"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
    }
