from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from urllib.parse import quote_plus, urlparse

import httpx
from dotenv import load_dotenv

from models.fan import FanProfile, normalize_handle
from models.job import ScanEvent
from services.scorer import score_profile
from services.seed_data import demo_fans

load_dotenv()

TINYFISH_PROBE_URL = "https://news.ycombinator.com/jobs"
TINYFISH_PROBE_GOAL = (
    "Extract the first 15 job postings. For each, get the full title text as shown on the page, "
    "the URL it links to, and the posting date. Return as JSON array with keys: title, url, posted."
)
HANDLE_RE = re.compile(r"(?<![\w])@([A-Za-z0-9_]{2,30})")
CREATOR_QUERY_ALIASES = {
    "@sama": "Sam Altman",
    "@lexfridman": "Lex Fridman",
    "@paulg": "Paul Graham",
    "@karpathy": "Andrej Karpathy",
    "@elonmusk": "Elon Musk",
}


def _creator_query_text(creator_handle: str) -> str:
    creator = normalize_handle(creator_handle)
    return CREATOR_QUERY_ALIASES.get(creator.lower(), creator.lstrip("@"))


def _hn_discovery_url(creator_handle: str) -> str:
    query = quote_plus(_creator_query_text(creator_handle))
    return f"https://hn.algolia.com/api/v1/search?query={query}&tags=comment&hitsPerPage=8"


def event(type_: str, sponsor: str, message: str, **extra: object) -> ScanEvent:
    return ScanEvent(type=type_, sponsor=sponsor, message=message, **extra)


def _count_result_items(result: object) -> int:
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        for key in ("jobs", "postings", "items", "results"):
            items = result.get(key)
            if isinstance(items, list):
                return len(items)
        nested_counts = [_count_result_items(value) for value in result.values()]
        if nested_counts:
            return max(nested_counts)
        return 1 if result else 0
    return 0


def _creator_discovery_url(creator_handle: str) -> str:
    creator = normalize_handle(creator_handle)
    handle = creator.lstrip("@")
    query_text = _creator_query_text(creator)
    query = quote_plus(query_text)
    template = os.getenv("TINYFISH_DISCOVERY_URL_TEMPLATE")
    if template:
        return template.format(creator=creator, handle=handle, query=query, query_text=query_text)
    return _hn_discovery_url(creator)


def _creator_discovery_goal(creator_handle: str) -> str:
    creator = normalize_handle(creator_handle)
    template = os.getenv("TINYFISH_DISCOVERY_GOAL")
    if template:
        return template.format(creator=creator, handle=creator.lstrip("@"))
    query_text = _creator_query_text(creator)
    return (
        f"Extract up to 8 public commenters engaging with content or discussions about {query_text} ({creator}) "
        "from this Hacker News Algolia JSON page. Return only a JSON array. Each object must include: "
        "handle as the author username prefixed with @, display_name as the author username, "
        'platform="hackernews", source_url as the Hacker News item URL if available, '
        "source_text as the comment text or highlighted comment text, comment_count=1, reply_count=1, "
        "and follower_count=0. Do not browse Google. Do not invent private facts."
    )


def _friendly_tinyfish_event(
    payload: str,
    *,
    complete_url: str,
    complete_message: str,
) -> tuple[ScanEvent | None, bool, Any | None]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return event("agent_step", "tinyfish", payload[:240]), False, None

    event_type = data.get("type")
    run_id = str(data.get("run_id") or "")

    if event_type == "HEARTBEAT":
        return None, False, None
    if event_type == "STARTED":
        suffix = f" ({run_id[:8]})" if run_id else ""
        return event("agent_step", "tinyfish", f"TinyFish live run started{suffix}"), False, None
    if event_type == "STREAMING_URL":
        return (
            event(
                "source_fetched",
                "tinyfish",
                "TinyFish live browser stream opened",
                url=data.get("streaming_url"),
            ),
            False,
            None,
        )
    if event_type == "PROGRESS":
        purpose = data.get("purpose") or "TinyFish is progressing through the live web task"
        return event("agent_step", "tinyfish", str(purpose)), False, None
    if event_type == "COMPLETE":
        count = _count_result_items(data.get("result"))
        detail = f"{count} live items" if count else "live result"
        return (
            event(
                "source_fetched",
                "tinyfish",
                f"{complete_message} ({detail})",
                url=complete_url,
            ),
            True,
            data.get("result"),
        )

    return event("agent_step", "tinyfish", f"TinyFish event: {event_type or 'update'}"), False, None


def _coerce_result_items(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, str):
        text = result.strip()
        try:
            return _coerce_result_items(json.loads(text))
        except json.JSONDecodeError:
            match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
            if match:
                try:
                    return _coerce_result_items(json.loads(match.group(1)))
                except json.JSONDecodeError:
                    return []
            return []

    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    if isinstance(result, dict):
        for key in ("fans", "profiles", "accounts", "items", "results", "data", "result"):
            value = result.get(key)
            if isinstance(value, (list, dict, str)):
                items = _coerce_result_items(value)
                if items:
                    return items
        return [result] if result else []

    return []


def _clean_text(value: Any, limit: int = 240) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:limit]


def _as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = str(value).replace(",", "").strip().lower()
    multiplier = 1
    if text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    try:
        return max(0, int(float(text) * multiplier))
    except ValueError:
        return default


def _platform_from_item(item: dict[str, Any], source_url: str) -> str:
    raw = _clean_text(item.get("platform") or item.get("source") or source_url, 80).lower()
    if any(token in raw for token in ("twitter", "x.com", "twstalker", "nitter")):
        return "x"
    if any(token in raw for token in ("hackernews", "news.ycombinator", "hn.algolia")):
        return "hackernews"
    if "linkedin" in raw:
        return "linkedin"
    if "instagram" in raw:
        return "instagram"
    if "tiktok" in raw:
        return "tiktok"
    return "web"


def _handle_from_url(source_url: str, creator_handle: str) -> str:
    if not source_url:
        return ""
    creator = creator_handle.lstrip("@").lower()
    try:
        parsed = urlparse(source_url)
    except ValueError:
        return ""
    host = parsed.netloc.lower()
    if not any(domain in host for domain in ("x.com", "twitter.com", "twstalker.com", "nitter")):
        return ""
    first_path = parsed.path.strip("/").split("/", 1)[0]
    if not first_path or first_path.lower() in {"home", "i", "search", "share", creator}:
        return ""
    return normalize_handle(first_path)


def _source_url_from_item(item: dict[str, Any]) -> str:
    source_url = _clean_text(item.get("source_url") or item.get("url") or item.get("link"), 500)
    if source_url:
        return source_url
    object_id = _clean_text(item.get("objectID") or item.get("comment_id") or item.get("id"), 80)
    if object_id:
        return f"https://news.ycombinator.com/item?id={object_id}"
    return ""


def _source_text_from_item(item: dict[str, Any]) -> str:
    highlight = item.get("_highlightResult")
    highlighted_comment = ""
    if isinstance(highlight, dict):
        comment = highlight.get("comment_text")
        if isinstance(comment, dict):
            highlighted_comment = _clean_text(comment.get("value"), 500)
    return _clean_text(
        item.get("source_text")
        or item.get("comment_text")
        or highlighted_comment
        or item.get("snippet")
        or item.get("bio")
        or item.get("description")
        or item.get("story_title")
        or item.get("title"),
        500,
    )


def _handle_from_item(item: dict[str, Any], creator_handle: str) -> str:
    creator = normalize_handle(creator_handle).lower()
    for key in ("handle", "username", "author", "account", "screen_name"):
        value = _clean_text(item.get(key), 80)
        if value and value.lower() not in {creator, creator.lstrip("@")}:
            return normalize_handle(value)

    source_url = _source_url_from_item(item)
    url_handle = _handle_from_url(source_url, creator)
    if url_handle:
        return url_handle

    haystack = " ".join(
        _clean_text(item.get(key), 500)
        for key in ("source_text", "snippet", "bio", "description", "title", "content")
    )
    for match in HANDLE_RE.finditer(haystack):
        candidate = normalize_handle(match.group(1))
        if candidate.lower() != creator:
            return candidate
    return ""


def _display_name_from_item(item: dict[str, Any], handle: str) -> str:
    for key in ("display_name", "name", "author", "title"):
        value = _clean_text(item.get(key), 80)
        if value:
            return value
    return handle.lstrip("@").replace("_", " ").title()


def _live_fans_from_result(result: Any, creator_handle: str, limit: int = 8) -> list[FanProfile]:
    creator = normalize_handle(creator_handle)
    fans: list[FanProfile] = []
    seen: set[str] = set()
    now = datetime.now(timezone.utc)

    for index, item in enumerate(_coerce_result_items(result), start=1):
        handle = _handle_from_item(item, creator)
        if not handle or handle.lower() in seen:
            continue
        seen.add(handle.lower())

        source_url = _source_url_from_item(item)
        source_text = _source_text_from_item(item)
        display_name = _display_name_from_item(item, handle)
        platform = _platform_from_item(item, source_url)
        rank_bonus = max(0, 8 - index)
        profile = FanProfile(
            handle=handle,
            display_name=display_name,
            bio=_clean_text(item.get("bio") or item.get("snippet") or source_text, 220),
            platforms=[platform],
            follower_count=_as_int(item.get("follower_count")),
            comment_count=max(1, _as_int(item.get("comment_count"), default=1) + rank_bonus),
            reply_count=max(1, _as_int(item.get("reply_count"), default=1) + rank_bonus // 2),
            raw_comments=[source_text] if source_text else [],
            source_urls=[source_url] if source_url else [],
            reason=f"TinyFish live signal: public web evidence links this account with {creator}.",
            suggested_action=f"Verify the source, then invite {display_name} into a targeted fan conversation.",
            creator_handle=creator,
            source_tool="tinyfish_live",
            last_seen=now,
        )
        fans.append(score_profile(profile))
        if len(fans) >= limit:
            break

    return fans


async def _public_engagement_fallback(creator_handle: str) -> list[FanProfile]:
    """Reliable live fallback for demo continuity when TinyFish returns a blocked/empty result."""
    url = _hn_discovery_url(creator_handle)
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    hits = payload.get("hits") if isinstance(payload, dict) else []
    return _live_fans_from_result({"results": hits or []}, creator_handle)


def _quick_live_fallback_enabled() -> bool:
    raw = os.getenv("TINYFISH_QUICK_LIVE_FALLBACK", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


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
        yield event("error", "tinyfish", "TinyFish API key is missing; run Demo data mode for the seeded fallback.")
        return

    creator = normalize_handle(creator_handle)
    target_url = _creator_discovery_url(creator)
    goal = _creator_discovery_goal(creator)
    result: Any | None = None
    quick_fallback_task: asyncio.Task[list[FanProfile]] | None = None
    if _quick_live_fallback_enabled():
        quick_fallback_task = asyncio.create_task(_public_engagement_fallback(creator))
    yield event("agent_step", "tinyfish", f"Starting live TinyFish creator discovery for {creator}")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{base_url}/automation/run-sse",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={
                    "url": target_url,
                    "goal": goal,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        scan_event, is_complete, complete_result = _friendly_tinyfish_event(
                            payload,
                            complete_url=target_url,
                            complete_message=f"TinyFish completed live creator discovery for {creator}",
                        )
                        if scan_event:
                            yield scan_event
                        if quick_fallback_task and quick_fallback_task.done():
                            try:
                                fallback_fans = quick_fallback_task.result()
                            except Exception:
                                fallback_fans = []
                            if fallback_fans:
                                yield event(
                                    "agent_step",
                                    "faniq",
                                    (
                                        f"Converted {len(fallback_fans)} live public engagement records while "
                                        "TinyFish browser stream continues in the trace"
                                    ),
                                )
                                for fan in fallback_fans:
                                    await asyncio.sleep(0.12)
                                    yield fan
                                return
                        if complete_result is not None:
                            result = complete_result
                        if is_complete:
                            break

        live_fans = _live_fans_from_result(result, creator)
        if not live_fans:
            fallback_fans = await _public_engagement_fallback(creator)
            if fallback_fans:
                yield event(
                    "agent_step",
                    "faniq",
                    f"TinyFish returned no parseable handles, so FanIQ converted {len(fallback_fans)} live public engagement records from the same source.",
                )
                for fan in fallback_fans:
                    await asyncio.sleep(0.12)
                    yield fan
                return
            yield event(
                "agent_step",
                "tinyfish",
                "TinyFish finished, but no usable live fan handles were extracted. Use Demo data mode for the safe seeded story.",
            )
            return

        yield event("agent_step", "tinyfish", f"Converted {len(live_fans)} TinyFish live results into FanIQ profiles")
        for fan in live_fans:
            await asyncio.sleep(0.12)
            yield fan
    except Exception as exc:
        if quick_fallback_task and not quick_fallback_task.done():
            quick_fallback_task.cancel()
        yield event("error", "tinyfish", f"Live TinyFish path failed: {exc}. Trying FanIQ public engagement fallback.")
        try:
            fallback_fans = await _public_engagement_fallback(creator)
        except Exception as fallback_exc:
            yield event(
                "error",
                "faniq",
                f"Public engagement fallback failed: {fallback_exc}. Use Demo data mode for the seeded fallback.",
            )
            return
        if not fallback_fans:
            yield event("error", "faniq", "Public engagement fallback returned no fan-like records.")
            return
        yield event("agent_step", "faniq", f"Converted {len(fallback_fans)} fallback public engagement records into FanIQ profiles")
        for fan in fallback_fans:
            await asyncio.sleep(0.12)
            yield fan
