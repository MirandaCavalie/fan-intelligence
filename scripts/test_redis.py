from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.redis_service import redis_service


async def main() -> None:
    assert await redis_service.ping()
    await redis_service.client.zadd("test:faniq", {"@testfan": 100})
    result = await redis_service.client.zrevrange("test:faniq", 0, 0, withscores=True)
    assert result[0][0] == "@testfan"
    await redis_service.client.delete("test:faniq")
    await redis_service.close()
    print("Redis OK - PING returned PONG, sorted set operations work")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Redis test failed - start Redis on localhost:6379 or set REDIS_URL. Details: {exc}")
        raise SystemExit(1)
