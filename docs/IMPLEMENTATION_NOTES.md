# Implementation Notes

## Recommended Repo Shape

```text
fan-intelligence/
  main.py
  requirements.txt
  .env.example
  routers/
    scan.py
    fans.py
    vapi.py
    publish.py
  services/
    tinyfish.py
    redis_service.py
    scorer.py
    profile_store.py
    publisher.py
  models/
    fan.py
  scripts/
    seed_demo_data.py
    test_redis.py
    test_tinyfish.py
  frontend/
    index.html
    app.js
    styles.css
  skill/
    SKILL.md
    shipables.json
```

## Service Boundaries

### `profile_store.py`

Create this abstraction even if Ghost is not ready.

Methods:

- `upsert_profile(profile)`
- `get_profile(creator, fan)`
- `list_profiles(creator)`

Implementation order:

1. Redis implementation.
2. Optional Ghost implementation.

### `publisher.py`

Create this abstraction even if cited.md is not ready.

Methods:

- `publish_creator_report(creator)`
- `publish_fan_profile(profile)`

Implementation order:

1. local markdown file publish.
2. cited.md/Senso live publish.
3. optional payment metadata.

### `vapi.py`

Start with the smallest useful voice surface.

Endpoint options:

- `/vapi/tools` for custom tools.
- `/vapi/llm` for custom LLM.

Choose one. Do not implement both unless the first path is working.

## Scoring Formula

Keep scoring explainable:

```text
score =
  comment_count * 30
  + reply_count * 20
  + min(follower_count / 100, 200)
  + cross_platform_bonus
  + recency_bonus
```

Suggested bonuses:

```text
cross_platform_bonus = 100 if present on 2+ platforms else 0
recency_bonus = 50 if active within 7 days, 20 if active within 30 days, else 0
```

Every fan card should show:

- score
- top reason
- suggested action

## Seed Data Quality Bar

Seed data should not look generic.

Each seed fan needs:

- specific handle
- believable bio
- comment snippets tied to the creator topic
- one reason the creator should care
- one suggested action

Good suggested actions:

- invite to beta
- ask to co-host Q&A
- DM for feedback
- feature their question in next episode
- recruit as community moderator

## UI Notes

One screen only.

Layout:

- top: handle input, Scan button, status.
- left: TinyFish/event stream.
- center: leaderboard.
- right: selected fan details and Vapi panel.
- bottom: publish log and sponsor trace.

Avoid:

- landing page hero.
- auth.
- settings pages.
- admin dashboards.

## Testing Before Demo

Run these every time before rehearsing:

```bash
python scripts/seed_demo_data.py --creator @lexfridman
curl http://localhost:8000/health
curl http://localhost:8000/fans/%40lexfridman
```

Then test Vapi:

```text
Who are my top three fans and what should I do with them?
```

