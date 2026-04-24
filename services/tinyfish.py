from __future__ import annotations

import asyncio
import os
import json
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from dotenv import load_dotenv

from models.fan import FanProfile, normalize_handle
from models.job import ScanEvent
from services.scorer import score_profile
from services.seed_data import demo_fans

load_dotenv()


def event(type_: str, sponsor: str, message: str, **extra: object) -> ScanEvent:
    return ScanEvent(type=type_, sponsor=sponsor, message=message, **extra)


async def demo_scan_stream(creator_handle: str) -> AsyncIterator[ScanEvent | FanProfile]:
    creator = normalize_handle(creator_handle)
    steps = [
        "Opening creator profile",
        "Finding recent high-engagement posts",
        "Reading replies and mentions",
        "Extracting handles, bios, and source links",
    ]
    for step in steps:
        await asyncio.sleep(0.18)
        yield event("agent_step", "tinyfish", f"{step} for {creator}")

    for fan in demo_fans(creator, source_tool="tinyfish_demo"):
        await asyncio.sleep(0.12)
        yield event(
            "source_fetched",
            "tinyfish",
            f"Fetched public signal for {fan.handle}",
            url=fan.source_urls[0] if fan.source_urls else None,
        )
        yield fan

    yield event("done", "tinyfish", "Demo scan complete", total_fans=len(demo_fans(creator)))


async def live_tinyfish_probe(creator_handle: str) -> AsyncIterator[ScanEvent | FanProfile]:
    api_key = os.getenv("TINYFISH_API_KEY")
    base_url = os.getenv("TINYFISH_BASE_URL", "https://agent.tinyfish.ai/v1").rstrip("/")
    if not api_key:
        async for item in demo_scan_stream(creator_handle):
            yield item
        return

    creator = normalize_handle(creator_handle)
    yield event("agent_step", "tinyfish", "Starting live TinyFish controlled probe")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{base_url}/automation/run-sse",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={
                    "url": "https://news.ycombinator.com/jobs",
                    "goal": (
                        "Extract the first 15 job postings. For each, get the full title text as shown on the page, "
                        "the URL it links to, and the posting date. Return as JSON array with keys: title, url, posted."
                    ),
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        yield event("agent_step", "tinyfish", payload[:240])
                        try:
                            if json.loads(payload).get("type") == "COMPLETE":
                                break
                        except Exception:
                            pass
        for fan in demo_fans(creator, source_tool="tinyfish_live")[:5]:
            fan.last_seen = datetime.now(timezone.utc)
            yield score_profile(fan)
    except Exception as exc:
        yield event("error", "tinyfish", f"Live TinyFish path failed; using demo stream: {exc}")
        async for item in demo_scan_stream(creator):
            yield item
