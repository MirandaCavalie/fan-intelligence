from __future__ import annotations

import json
import re
from typing import Any

from models.fan import FanProfile, normalize_handle
from services.redis_service import dumps


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "who",
    "why",
    "with",
    "my",
    "fans",
    "fan",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    return [token for token in tokens if len(token) > 2 and token not in STOPWORDS]


async def store_fan_memory(redis_service: Any, profile: FanProfile) -> None:
    creator = normalize_handle(profile.creator_handle)
    fan = normalize_handle(profile.handle)
    comments = profile.raw_comments or [profile.reason]

    pipe = redis_service.client.pipeline(transaction=False)
    for index, comment in enumerate(comments):
        memory_id = f"{fan}:{index}"
        key = f"fan_memory:{creator}:{memory_id}"
        payload = {
            "id": memory_id,
            "creator_handle": creator,
            "fan_handle": fan,
            "display_name": profile.display_name,
            "score": profile.score,
            "platforms": profile.platforms,
            "content": comment,
            "source_urls": profile.source_urls,
            "source_tool": profile.source_tool,
        }
        pipe.set(key, dumps(payload))
        pipe.zadd(f"fan_memory_scores:{creator}", {memory_id: profile.score})
        for token in set(tokenize(comment + " " + profile.bio + " " + profile.reason)):
            pipe.sadd(f"fan_memory_index:{creator}:{token}", memory_id)
    await pipe.execute()

    await redis_service.push_sponsor_trace(
        creator,
        {
            "sponsor": "Redis AI Incubator",
            "operation": "Agent Memory",
            "detail": f"Indexed {len(comments)} memory snippets for {fan}",
        },
    )


async def search_fan_memory(redis_service: Any, creator_handle: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    creator = normalize_handle(creator_handle)
    tokens = tokenize(query)
    if not tokens:
        tokens = ["ai", "research", "episode"]

    candidate_ids: set[str] = set()
    for token in tokens:
        rows = await redis_service.client.smembers(f"fan_memory_index:{creator}:{token}")
        candidate_ids.update(str(row) for row in rows)

    if not candidate_ids:
        rows = await redis_service.client.zrevrange(f"fan_memory_scores:{creator}", 0, limit - 1)
        candidate_ids.update(str(row) for row in rows)

    scored: list[tuple[float, dict[str, Any]]] = []
    for memory_id in candidate_ids:
        raw = await redis_service.client.get(f"fan_memory:{creator}:{memory_id}")
        if not raw:
            continue
        payload = json.loads(raw)
        content_tokens = set(tokenize(payload.get("content", "")))
        hit_count = len(content_tokens.intersection(tokens))
        score = float(payload.get("score", 0)) + hit_count * 75
        payload["match_score"] = int(score)
        payload["matched_terms"] = sorted(content_tokens.intersection(tokens))
        scored.append((score, payload))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [payload for _, payload in scored[:limit]]
    await redis_service.push_sponsor_trace(
        creator,
        {
            "sponsor": "Redis AI Incubator",
            "operation": "Memory search",
            "detail": f"{len(results)} snippets for query: {query[:48]}",
        },
    )
    return results
