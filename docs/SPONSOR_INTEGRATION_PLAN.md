# Sponsor Integration Plan

This file defines exactly how sponsor tools should appear in the demo and what the fallback is.

## TinyFish

### Demo Role

Visible agentic discovery.

### MVP Implementation

- `services/tinyfish.py`
- `POST /scan` starts a scan job.
- Scan job emits events:
  - `agent_step`
  - `fan_found`
  - `source_fetched`
  - `done`
- Store discovered fan signals in Redis.

### Demo Proof

UI shows:

- TinyFish step log.
- source URL.
- extracted fan signal.

### Fallback

If live social crawl fails:

- run TinyFish against a controlled public page or simpler target.
- seed fan results from `scripts/seed_demo_data.py`.
- label seeded rows as fallback in internal logs, not front-and-center in the demo.

## Redis

### Demo Role

Real-time scoring and leaderboard.

### MVP Implementation

Keys:

```text
fans:{creator}                  sorted set
fan_profile:{creator}:{fan}     hash or JSON string
events:{creator}                list
scan:{job_id}                   hash/string status
```

Commands to show:

```text
ZADD
ZREVRANGE
HSET
HGETALL
LPUSH
```

### Demo Proof

UI shows:

- leaderboard sorted by score.
- fan count.
- "Redis trace" panel with recent writes.

### Fallback

No fallback for the track, but if Redis Cloud/local fails:

- restart local Redis.
- run seed script again.

## Vapi

### Demo Role

Voice interface for asking about fans.

### MVP Implementation

One assistant: FanIQ Intelligence.

Expected interaction:

User:

> Who are my top three fans and what should I do with them?

Assistant:

> Your top fan is Alex Chen because they replied to 14 posts, show up on two platforms, and have a strong AI audience. Invite them into a private beta or ask them to co-host a community Q&A.

### Integration Options

Option A - Custom LLM endpoint:

- Vapi calls `/vapi/llm`.
- Backend injects Redis top fan context.
- Backend streams/returns model response.

Option B - Custom tool endpoint:

- Vapi assistant calls `get_top_fans`.
- Backend returns structured top fan summary.
- Vapi speaks the answer.

Use whichever works fastest on-site.

### Fallback

If live voice fails:

- use Vapi dashboard test.
- show Vapi transcript/log.
- use a prerecorded or typed assistant response only as last resort.

## cited.md / Senso

### Demo Role

Agent output publication.

### MVP Implementation

`POST /publish/{creator}` takes top fans and creates a fan intelligence memo:

- title
- summary
- top fan profiles
- source links
- generated timestamp
- payment status if real

### Demo Proof

UI shows:

- published badge.
- publish log.
- URL or local generated markdown.

### Fallback

If live API is not ready:

- generate `output/published/{creator}.md`.
- show "cited.md publish adapter ready; demo fallback generated locally".

Do not claim real payment if not implemented.

## Shipables

### Demo Role

Package project as a reusable agent skill.

### MVP Implementation

Create:

```text
skill/
  SKILL.md
  shipables.json
  references/
    workflow.md
    api-contracts.md
```

### Demo Proof

Mention in close:

> We also packaged FanIQ as a Shipables skill so agents can reuse the fan discovery workflow.

## Ghost / TigerData

### Demo Role

Durable fan profile store.

### MVP Implementation

Only implement if account setup is fast.

Adapter methods:

- `upsert_fan_profile(profile)`
- `get_fan_profile(creator, fan)`

### Fallback

Redis-only profile store.

Pitch:

- If Ghost is not working, do not pitch it as live. Keep it in README as planned optional integration.

