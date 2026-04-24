from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.redis_service import redis_service
from services.seed_data import demo_fans


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed FanIQ demo data into Redis.")
    parser.add_argument("--creator", default="@lexfridman")
    parser.add_argument("--clear", action="store_true", help="Clear existing creator data before seeding.")
    args = parser.parse_args()

    if args.clear:
        await redis_service.clear_creator(args.creator)

    fans = demo_fans(args.creator)
    for fan in fans:
        await redis_service.upsert_fan(fan)
    top = await redis_service.list_top_fans(args.creator, limit=3)
    print(f"Seeded {len(fans)} fans for {args.creator} - leaderboard ready")
    for fan in top:
        print(f"{fan.score:>4}  {fan.handle:<20} {fan.display_name}")
    await redis_service.close()


if __name__ == "__main__":
    asyncio.run(main())
