from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.fan import FanProfile
from services.tinyfish import demo_scan_stream, live_tinyfish_probe


async def main() -> None:
    stream = live_tinyfish_probe("@lexfridman")
    count = 0
    async for item in stream:
        print(item.model_dump(mode="json") if hasattr(item, "model_dump") else item)
        if isinstance(item, FanProfile):
            count += 1
        if count >= 2:
            break
    if count == 0:
        async for item in demo_scan_stream("@lexfridman"):
            print(item.model_dump(mode="json") if hasattr(item, "model_dump") else item)
            if isinstance(item, FanProfile):
                count += 1
                break
    assert count > 0
    print("TinyFish adapter OK - live or demo-visible path produced fan data")


if __name__ == "__main__":
    asyncio.run(main())
