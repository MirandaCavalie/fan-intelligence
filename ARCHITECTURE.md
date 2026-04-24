# FanIQ — System Architecture

---

## System diagram

```
                        ┌─────────────────────────────────────────┐
                        │             FanIQ Frontend               │
                        │  (handle input · SSE stream · leaderboard│
                        │   · voice buttons · cited.md log)        │
                        └──────────────┬──────────────────────────┘
                                       │ HTTP / WebSocket
                        ┌──────────────▼──────────────────────────┐
                        │           FastAPI Backend                 │
                        │                                          │
                        │  POST /scan          ← start scan job    │
                        │  GET  /scan/{id}     ← SSE progress      │
                        │  GET  /fans/{creator}← leaderboard       │
                        │  GET  /fan/{c}/{f}   ← single profile    │
                        │  POST /vapi/llm      ← custom LLM        │
                        │  POST /vapi/webhook  ← call events       │
                        │  POST /publish/{c}   ← cited.md trigger  │
                        └──┬────────┬──────────┬──────────┬────────┘
                           │        │          │          │
              ┌────────────▼┐  ┌────▼─────┐  ┌▼──────┐  ┌▼────────────┐
              │  Tinyfish   │  │  Ghost   │  │ Redis │  │ cited.md    │
              │  Web Agent  │  │TigerData │  │       │  │ Senso/x402  │
              │             │  │          │  │ Sorted│  │             │
              │ /run-sse    │  │ Members  │  │ Sets  │  │ Fan profile │
              │ X + LinkedIn│  │ + Meta   │  │ Hashes│  │ documents   │
              └────────────┘  └────┬─────┘  └▲──────┘  └─────────────┘
                                   │          │
                                   └──────────┘
                                (Ghost write → Redis score)

                        ┌─────────────────────────────────────────┐
                        │                Vapi                      │
                        │  STT → POST /vapi/llm → TTS             │
                        │  Assistant A: FanIQ Intelligence         │
                        │  Assistant B: Fan Persona                │
                        └──────────────┬──────────────────────────┘
                                       │ custom LLM call
                        ┌──────────────▼──────────────────────────┐
                        │    Anthropic Claude (claude-sonnet-4-5)  │
                        │  Receives: system prompt with fan data   │
                        │  Returns: natural voice response         │
                        └─────────────────────────────────────────┘
```

---

## Component responsibilities

### FastAPI backend (`main.py` + `routers/`)
- Receives scan requests, dispatches Tinyfish jobs
- Streams Tinyfish SSE back to frontend via Server-Sent Events
- Writes fan profiles to Ghost after Tinyfish completes
- Scores fans and writes to Redis
- Serves leaderboard and profile endpoints
- Hosts the Vapi custom LLM endpoint
- Triggers cited.md publication

### Tinyfish service (`services/tinyfish.py`)
- Async HTTP client wrapping `agent.tinyfish.ai/v1/automation/run-sse`
- Two concurrent jobs: X goal + LinkedIn goal
- SSE parser → yields fan dicts as they are extracted
- Fan deduplication by handle normalization

### Ghost service (`services/ghost.py`)
- Ghost Admin API client
- Creates/upserts member records
- Custom metadata schema (see below)
- Reads profiles for Vapi persona injection

### Redis service (`services/redis_service.py`)
- Fan scoring pipeline
- Leaderboard queries (`ZREVRANGE`)
- Profile cache (`HSET`/`HGETALL`)
- Job status tracking
- Event stream (`LPUSH`)

### Scorer (`services/scorer.py`)
- Scoring formula implementation
- Cross-platform dedup bonus calculation
- Score normalization

### Persona builder (`services/persona.py`)
- Builds system prompt for Vapi Fan Persona mode
- Injects fan's bio, comments, job, follower count
- Keeps prompt under ~800 tokens for latency

### cited.md service (`services/cited.py`)
- Publishes fan profile documents to Senso context layer
- Wires x402 payment requirement
- Logs earned micro-payments

---

## Data models

### FanProfile (`models/fan.py`)
```python
class FanProfile(BaseModel):
    handle: str                    # @username normalized
    display_name: str
    bio: str
    follower_count: int
    platforms: list[str]           # ["x", "linkedin"]
    raw_comments: list[str]        # actual comment texts
    engagement_events: list[EngagementEvent]
    linkedin_url: str | None
    job_title: str | None
    company: str | None
    creator_handle: str            # which creator they fan of
    fan_score: float
    last_seen: datetime
    cited_md_url: str | None       # populated after publish

class EngagementEvent(BaseModel):
    platform: str
    event_type: str                # "comment" | "mention" | "share" | "reply"
    content: str
    timestamp: datetime | None
    post_url: str | None
```

### Ghost member metadata schema
```json
{
  "x_handle": "@handle",
  "linkedin_url": "https://linkedin.com/in/...",
  "follower_count": 12000,
  "platforms": ["x", "linkedin"],
  "engagement_events": "[{...}, {...}]",
  "raw_comments": "[\"comment 1\", \"comment 2\"]",
  "fan_score": 847.5,
  "creator_handle": "@lexfridman",
  "job_title": "AI Researcher",
  "company": "Google",
  "last_seen": "2026-04-24T14:30:00Z",
  "cited_md_url": "https://cited.md/faniq/..."
}
```

---

## Redis key schema

| Key | Type | Content | TTL |
|---|---|---|---|
| `fans:{creator_handle}` | Sorted Set | member=fan_handle, score=engagement_score | 24h |
| `fan_profile:{creator}:{fan}` | Hash | all FanProfile fields as strings | 24h |
| `crawl_status:{job_id}` | String | "queued"\|"running"\|"done"\|"failed" | 1h |
| `crawl_result:{job_id}` | String | JSON array of fan dicts | 2h |
| `events:{creator_handle}` | List | recent engagement events JSON | 24h |
| `cited_earnings:{creator}` | Hash | fan_handle → amount_earned | 24h |

### Redis commands used

```python
# Add/update fan score
await redis.zadd(f"fans:{creator}", {fan_handle: score})

# Get top 10 fans
fans = await redis.zrevrange(f"fans:{creator}", 0, 9, withscores=True)

# Store full profile
await redis.hset(f"fan_profile:{creator}:{fan}", mapping=profile_dict)

# Get profile
profile = await redis.hgetall(f"fan_profile:{creator}:{fan}")

# Track job
await redis.setex(f"crawl_status:{job_id}", 3600, "running")

# Event feed
await redis.lpush(f"events:{creator}", json.dumps(event))
await redis.ltrim(f"events:{creator}", 0, 99)  # keep last 100
```

---

## Fan scoring algorithm

```
score = (comment_count × 3.0)
      + (follower_count / 1000)
      + (cross_platform_bonus × 5.0)
      + (recency_weight × 2.0)
      + (reply_count × 1.5)

Where:
  comment_count       = total comments on creator's content
  follower_count      = their audience size (reach multiplier)
  cross_platform_bonus = 1 if on both X + LinkedIn, 0 otherwise
  recency_weight      = 1 if active in last 7 days, 0.5 if last 30 days, 0 otherwise
  reply_count         = direct replies (higher intent than comments)

Rationale:
  - Comments (×3) signal active engagement, not passive following
  - Follower count / 1000 contributes but doesn't dominate (an amplifier, not the score)
  - Cross-platform bonus rewards the most devoted fans
  - Recency matters — a fan who was active 2 years ago is less valuable
```

---

## API endpoints

### `POST /scan`
```json
Request:  { "creator_handle": "@lexfridman", "platforms": ["x", "linkedin"] }
Response: { "job_id": "uuid", "status": "queued" }
```

### `GET /scan/{job_id}` — SSE stream
```
data: {"type": "agent_step", "message": "Navigating to twitter.com...", "platform": "x"}
data: {"type": "fan_found", "fan": {...FanProfile...}, "score": 847}
data: {"type": "progress", "found": 23, "platform": "x"}
data: {"type": "done", "total_fans": 47, "duration_seconds": 94}
```

### `GET /fans/{creator_handle}`
```json
Response: {
  "creator": "@lexfridman",
  "total_fans": 47,
  "top_fans": [
    { "handle": "@airesearcher_sf", "score": 847, "display_name": "...", "platforms": ["x","linkedin"] },
    ...
  ]
}
```

### `GET /fan/{creator_handle}/{fan_handle}`
```json
Response: { ...full FanProfile... }
```

### `POST /vapi/llm` — Vapi custom LLM endpoint
Vapi sends an OpenAI-compatible chat completion request. We:
1. Parse the user message
2. Detect mode (intelligence vs persona) from assistant config
3. Fetch data from Redis/Ghost
4. Build enriched system prompt
5. Stream to Claude
6. Return SSE in OpenAI format

```python
# Request shape from Vapi (OpenAI-compatible)
{
  "model": "faniq-intelligence",  # or "faniq-persona:{fan_handle}"
  "messages": [...],
  "stream": true,
  "call": { "id": "...", "assistantId": "..." }
}
```

### `POST /vapi/webhook`
Handles Vapi call events: `call-started`, `call-ended`, `transcript`.
On `call-ended`: log call summary to Redis event feed.

### `POST /publish/{creator_handle}`
Publishes all fan profiles for a creator to cited.md.
Returns list of published URLs + earnings setup status.

---

## Tinyfish job schema

### X job
```python
{
  "url": f"https://twitter.com/{creator_handle}",
  "goal": (
    f"Find the 20 most recent posts by {creator_handle}. "
    "For each post, extract ALL reply authors. For each reply author extract: "
    "handle (with @), display_name, bio, follower_count (if visible), "
    "and their full reply text. "
    "Return a JSON array of objects with fields: "
    "handle, display_name, bio, follower_count, reply_text, post_url."
  )
}
```

### LinkedIn job
```python
{
  "url": f"https://www.linkedin.com/search/results/content/?keywords={creator_name}",
  "goal": (
    f"Find posts that mention or are by {creator_name}. "
    "For each post, extract commenters. For each commenter: "
    "name, headline (job title + company), profile_url, comment_text. "
    "Return a JSON array with fields: "
    "name, headline, profile_url, comment_text."
  )
}
```

---

## Vapi assistant configurations

### Assistant A — FanIQ Intelligence
```json
{
  "name": "FanIQ Intelligence",
  "model": {
    "provider": "custom-llm",
    "url": "{NGROK_URL}/vapi/llm",
    "model": "faniq-intelligence"
  },
  "voice": { "provider": "11labs", "voiceId": "21m00Tcm4TlvDq8ikWAM" },
  "firstMessage": "Hey! I'm FanIQ. Ask me anything about your fans.",
  "systemPrompt": "You are FanIQ, a fan intelligence assistant. Keep responses under 2 sentences for voice. No markdown. Be direct and conversational. Fan data is injected at call time."
}
```

### Assistant B — Fan Persona
```json
{
  "name": "Fan Persona — {fan_handle}",
  "model": {
    "provider": "custom-llm",
    "url": "{NGROK_URL}/vapi/llm",
    "model": "faniq-persona:{fan_handle}"
  },
  "voice": { "provider": "11labs", "voiceId": "AZnzlk1XvdvUeBnXmlld" },
  "firstMessage": "Hey, what's up?",
  "systemPrompt": "Persona injected dynamically from Ghost profile at call time."
}
```

---

## Vapi persona prompt template

```python
PERSONA_SYSTEM = """
You are {display_name} (@{handle}).
You are a real fan of {creator_handle}.

About you:
- Bio: {bio}
- You have {follower_count} followers
- You work as {job_title} at {company}
- You follow {creator_handle} on: {platforms}

Your actual comments and replies to {creator_handle}'s content:
{raw_comments_formatted}

Rules:
- Stay completely in character. Never break persona.
- You speak casually, like you would on social media.
- Your opinions on topics come from what you've actually written above.
- If asked something you have no data for, give a plausible in-character answer.
- Keep responses short — 1-3 sentences for voice.
- Never say you're an AI.
"""
```

---

## cited.md publish schema

```json
{
  "title": "Fan Profile: @{fan_handle} — fan of {creator_handle}",
  "content": "...(structured fan profile as markdown)...",
  "metadata": {
    "fan_handle": "@handle",
    "creator_handle": "@creator",
    "fan_score": 847,
    "platforms": ["x", "linkedin"],
    "generated_by": "faniq-agent",
    "generated_at": "2026-04-24T..."
  },
  "payment": {
    "protocol": "x402",
    "amount": 0.002,
    "currency": "USD"
  }
}
```

---

## Sequence diagrams

### Scan flow
```
Frontend          FastAPI           Tinyfish           Ghost              Redis
   |                 |                  |                 |                  |
   |-- POST /scan -->|                  |                 |                  |
   |<-- {job_id} ----|                  |                 |                  |
   |                 |-- run-sse (X) -->|                 |                  |
   |                 |-- run-sse (LI)-->|                 |                  |
   |-- GET /scan/id ->|                 |                 |                  |
   |                 |<-- SSE steps ----|                 |                  |
   |<-- SSE steps ---|                  |                 |                  |
   |                 |<-- fan JSON -----|                 |                  |
   |                 |-- POST /members ------------------>|                  |
   |                 |-- ZADD score ------------------------------------------->|
   |                 |-- HSET profile ----------------------------------------->|
   |<-- fan_found ---|                  |                 |                  |
   ...              ...                ...               ...                ...
   |                 |<-- done ---------|                 |                  |
   |<-- done --------|                  |                 |                  |
```

### Voice call flow (Mode B — Persona)
```
Creator           Vapi              FastAPI           Ghost / Redis       Claude
   |                |                  |                   |                 |
   |-- speaks ----->|                  |                   |                 |
   |                |-- STT transcript |                   |                 |
   |                |-- POST /vapi/llm>|                   |                 |
   |                |                  |-- HGETALL profile>|                 |
   |                |                  |<-- fan profile ---|                 |
   |                |                  |-- build persona prompt              |
   |                |                  |-- POST /messages ------------------>|
   |                |                  |<-- stream response -----------------|
   |                |<-- SSE tokens ---|                   |                 |
   |                |-- TTS ---------->|                   |                 |
   |<-- voice -------|                  |                   |                 |
```
