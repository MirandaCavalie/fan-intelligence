from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.fan import normalize_handle
from services.redis_service import redis_service
from services.vapi_setup import (
    assistant_payloads,
    create_vapi_assistants,
    public_base_url,
    vapi_setup_errors,
)


async def default_persona(creator_handle: str, fan_handle: str | None) -> tuple[str, str | None]:
    if fan_handle:
        profile = await redis_service.get_profile(creator_handle, fan_handle)
        return normalize_handle(fan_handle), profile.display_name if profile else None

    fans = await redis_service.list_top_fans(creator_handle, limit=1)
    if fans:
        return fans[0].handle, fans[0].display_name
    return "@airesearcher_sf", "Alex Chen"


async def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Create FanIQ Vapi assistants.")
    parser.add_argument("--creator", default="@lexfridman", help="Creator handle for FanIQ Intelligence.")
    parser.add_argument("--persona", default=None, help="Fan handle for the synthetic persona assistant.")
    parser.add_argument("--display-name", default=None, help="Optional display name for the persona first message.")
    parser.add_argument("--dry-run", action="store_true", help="Print assistant payloads without calling Vapi.")
    parser.add_argument(
        "--skip-public-key-check",
        action="store_true",
        help="Allow assistant creation before VAPI_PUBLIC_KEY is configured for the browser UI.",
    )
    args = parser.parse_args()

    creator = normalize_handle(args.creator)
    fan_handle, profile_name = await default_persona(creator, args.persona)
    display_name = args.display_name or profile_name

    errors = vapi_setup_errors(require_public_key=not args.skip_public_key_check)
    if errors:
        print("Vapi setup is not ready:")
        for error in errors:
            print(f"- {error}")
        if not args.dry_run:
            await redis_service.close()
            return 2

    payloads = assistant_payloads(creator, fan_handle, display_name, base_url=public_base_url() or "https://example.ngrok-free.app")
    if args.dry_run:
        print(json.dumps({"creator_handle": creator, "fan_handle": fan_handle, "payloads": payloads}, indent=2))
        await redis_service.close()
        return 0 if not errors else 2

    result = await create_vapi_assistants(
        creator,
        fan_handle,
        display_name=display_name,
        require_public_key=not args.skip_public_key_check,
    )
    print(json.dumps(result, indent=2))
    await redis_service.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
