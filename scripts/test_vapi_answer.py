from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.redis_service import redis_service
from services.seed_data import demo_fans
from services.vapi_answer import build_vapi_answer


async def main() -> None:
    creator = "@lexfridman"
    await redis_service.clear_creator(creator)
    for fan in demo_fans(creator):
        await redis_service.upsert_fan(fan)
    response = await build_vapi_answer(
        {
            "model": "faniq-intelligence",
            "metadata": {"creator_handle": creator},
            "messages": [{"role": "user", "content": "Who are my top three fans and what should I do with them?"}],
        }
    )
    text = response["choices"][0]["message"]["content"]
    assert "@airesearcher_sf" in text
    print(text)
    await redis_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Vapi answer test failed - Redis is required for seeded fan context. Details: {exc}")
        raise SystemExit(1)
