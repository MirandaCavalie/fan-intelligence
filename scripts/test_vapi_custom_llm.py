from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.redis_service import redis_service
from services.seed_data import demo_fans
from services.vapi_answer import build_vapi_answer, stream_vapi_answer


async def main() -> None:
    creator = "@lexfridman"
    await redis_service.clear_creator(creator)
    for fan in demo_fans(creator):
        await redis_service.upsert_fan(fan)

    intelligence_body = {
        "model": "faniq-intelligence",
        "stream": False,
        "metadata": {"creator_handle": creator},
        "messages": [{"role": "user", "content": "Who are my top fans?"}],
    }
    intelligence = await build_vapi_answer(intelligence_body)
    intelligence_text = intelligence["choices"][0]["message"]["content"]
    assert "@airesearcher_sf" in intelligence_text
    assert intelligence["object"] == "chat.completion"

    persona_body = {
        "model": "faniq-persona:@lexfridman:@airesearcher_sf",
        "stream": False,
        "messages": [{"role": "user", "content": "Why do you keep engaging with Lex?"}],
    }
    persona = await build_vapi_answer(persona_body)
    persona_text = persona["choices"][0]["message"]["content"]
    assert "synthetic" in persona_text.lower()
    assert "real person" in persona_text.lower()

    chunks = []
    async for chunk in stream_vapi_answer({**intelligence_body, "stream": True}):
        chunks.append(chunk)
    stream_text = "".join(chunks)
    assert "chat.completion.chunk" in stream_text
    assert "data: [DONE]" in stream_text

    print("Vapi custom LLM OK - non-streaming, streaming, and persona modes work")
    await redis_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Vapi custom LLM test failed. Details: {exc}")
        raise SystemExit(1)
