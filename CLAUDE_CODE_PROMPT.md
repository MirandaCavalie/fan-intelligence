# FanIQ — Claude Code Bootstrap Prompt

> Paste everything below this line as your first message to Claude Code.
> Claude Code will read it, think through the product, and generate all project files.

---

You are the lead engineer for **FanIQ**, a Fan Intelligence Platform being built at the
**Ship to Prod — Agentic Engineering Hackathon** (San Francisco, Apr 24 2025, 11:00 AM–4:30 PM PT).
You have ~5.5 hours. Max team size is 4. This is a real competition with $45k+ in prizes.

Read every word of this prompt before writing a single line of code. Then create all the
project files listed at the bottom. Think hard. This is a competition — every architectural
decision matters.

---

## 1. THE PRODUCT — FANIQ

### Problem
Content creators (YouTubers, podcasters, writers, developers) have thousands of followers but
zero intelligence about who their actual superfans are. They can't identify the people who
comment on every post, share their content, and mention them across multiple platforms.

### Solution
FanIQ is an autonomous agent that:
1. Takes a creator's handle as input
2. Uses Tinyfish to crawl X (Twitter) and LinkedIn for every person who has engaged with them
3. Builds enriched fan profiles stored in Ghost/TigerData
4. Scores and ranks fans in real-time using Redis sorted sets
5. Exposes two Vapi voice interfaces:
   - **Intelligence mode**: creator asks "Who are my top 5 fans?" → AI answers with real data
   - **Persona mode**: creator picks a fan → talks to a voice agent embodying that fan's persona,
     built from their actual comments and bio

### The "cited.md" layer (CRITICAL for judging)
Every fan profile FanIQ generates must be published to **cited.md** via Senso's context layer.
This makes FanIQ's output discoverable and monetizable by other agents. Wire in payment rails
(x402 or agentic.market) so that when another agent fetches a fan profile, FanIQ earns a
micro-payment. This is the autonomy + monetization story judges want to see.

---

## 2. HACKATHON RULES & JUDGING (20% each criterion)

- **Autonomy** — Agent acts on real-time data without manual intervention
- **Idea** — Meaningful problem, real-world value
- **Technical Implementation** — How well built
- **Tool Use** — Must use ≥3 sponsor tools effectively
- **Presentation (Demo)** — 3 minutes, must be polished

**Hard constraints:**
- No previous projects. Fresh GitHub required.
- Submission deadline: 4:30 PM PT Apr 24
- Must use ≥3 sponsor tools
- Must install ≥1 sponsor skill via shipables.dev
- Must publish agent output to cited.md
- Team max: 4 people

---

## 3. SPONSORS WE USE (and exactly why)

### Tinyfish — AI Web Agent (PRIMARY)
- **What it does**: Natural language web automation. You give it a URL + a goal in plain English,
  it navigates the real site (handles anti-bot, JS, logins) and returns clean JSON.
- **Why it's critical**: X and LinkedIn have no public APIs for this use case. Tinyfish lets us
  scrape both without any API approval. This is the data acquisition layer.
- **API**: `POST https://agent.tinyfish.ai/v1/automation/run-sse`
  ```json
  {
    "url": "https://twitter.com/{handle}",
    "goal": "Find the 20 most recent posts. For each post extract all reply authors: handle, display_name, follower_count, bio, reply_text. Return JSON array."
  }
  ```
- **Key**: Header `X-API-Key: $TINYFISH_API_KEY`
- **SSE streaming**: The run-sse endpoint streams agent steps — show this live in the UI for WOW factor
- **Concurrent runs**: Run X and LinkedIn jobs in parallel using async

### Ghost by TigerData — Research Data Infrastructure (PRIMARY)
- **What it does**: Ghost is the persistent fan profile store. Each fan is a Ghost "member" record
  with custom metadata fields.
- **Data model per fan**:
  ```json
  {
    "email": "{handle}@faniq.local",
    "name": "Display Name",
    "labels": ["superfan", "x-commenter", "linkedin-engager"],
    "note": "Bio text",
    "metadata": {
      "x_handle": "@techguy_42",
      "linkedin_url": "https://linkedin.com/in/...",
      "follower_count": 12000,
      "engagement_events": [...],
      "raw_comments": [...],
      "fan_score": 847,
      "creator_handle": "@lexfridman",
      "last_seen": "2025-04-24T..."
    }
  }
  ```
- Ghost Admin API: `POST /ghost/api/admin/members/`
- Each source (X, LinkedIn) writes its own fan document; deduplication merges by handle

### Redis — Real-time Fan Scoring (PRIMARY)
- **What it does**: Sorted sets for live leaderboard. Sub-millisecond fan ranking.
- **Key design**:
  - `fans:{creator_handle}` → sorted set, score = engagement score, member = fan_handle
  - `fan_profile:{creator_handle}:{fan_handle}` → hash, all profile fields
  - `crawl_status:{job_id}` → string, "running" | "done" | "failed"
  - `events:{creator_handle}` → list, recent engagement events for activity feed
- **Scoring formula**:
  ```
  score = (comment_count * 3) + (follower_count / 1000) + (cross_platform_bonus * 5) + (recency_weight)
  ```
- Commands used: `ZADD`, `ZREVRANGE`, `HSET`, `HGETALL`, `LPUSH`, `EXPIRE`
- The leaderboard updates in real-time as Tinyfish returns results — push updates via WebSocket

### Vapi — Voice AI Agent (PRIMARY)
- **What it does**: Voice infrastructure. You register a custom LLM endpoint; Vapi handles
  STT → your LLM → TTS with ~1.9s latency.
- **Two assistants to create**:

  **Assistant 1: FanIQ Intelligence** (creator talks TO the system)
  ```
  System: You are FanIQ, a fan intelligence assistant for the creator {creator_handle}.
  You have access to their fan database. Answer questions about their fans naturally and
  conversationally. Keep answers under 3 sentences for voice. No markdown.
  Context: [top 10 fans from Redis ZREVRANGE injected here at call time]
  ```

  **Assistant 2: Fan Persona** (creator talks WITH a fan)
  ```
  System: You are {fan_display_name} (@{fan_handle}). You are a real fan of {creator_handle}.
  Facts about you: {bio}. You have {follower_count} followers. You work as {job_title}.
  Your actual comments on their content: {raw_comments[]}. Stay completely in character.
  Never break persona. Respond as this person would speak — casual, authentic.
  Your opinion on topics comes from what you've actually written.
  ```

- **Custom LLM endpoint** (FastAPI): `POST /vapi/llm`
  Receives Vapi's OpenAI-compatible request → reads Redis/Ghost → enriches system prompt → streams to Claude → returns SSE
- **Vapi webhook**: `POST /vapi/webhook` for call events

### cited.md / Senso — Agent Output Publication (REQUIRED for judging)
- **What it does**: Publishes agent outputs to the open web so other agents can discover,
  cite, and pay for them.
- **What we publish**: Each completed fan profile document (after Ghost write)
- **Setup**: docs.senso.ai/docs/hello-world — 5 minute setup
- **Payment rail**: Wire x402 or agentic.market so fetching a fan profile costs micro-payment
- **This is the autonomy story**: FanIQ doesn't just collect data, it publishes intelligence
  that earns money autonomously when consumed

### Shipables.dev — Sponsor Skills (REQUIRED for judging)
- Sign up at shipables.dev (GitHub auth)
- Install at least one sponsor skill
- Publish FanIQ itself as a skill at the end

---

## 4. TECH STACK

```
Language:     Python 3.11+ (backend) + vanilla JS or React (frontend)
Framework:    FastAPI (async, perfect for SSE streaming)
Database:     Redis (scoring + cache) + Ghost/TigerData (profiles)
Voice:        Vapi (custom LLM endpoint pattern)
Web agent:    Tinyfish (run-sse for live streaming)
AI:           Anthropic Claude claude-sonnet-4-5 via API (fan persona + intelligence)
Deploy:       Local with ngrok for Vapi webhook (hackathon day)
```

---

## 5. FILES TO CREATE

Create every file below. Use the filename exactly as shown (first line of each file must be
the filename as a comment or H1). Be thorough — these are the north star documents for the
entire team during the hackathon.

---

### README.md
First line must be: `# FanIQ — Fan Intelligence Platform`

Include:
- One-paragraph product vision
- The core user journey (3 sentences)
- Sponsor tracks we're targeting and why
- Tech stack table
- Repo structure (planned)
- How to run locally (placeholder — SETUP.md has details)
- The cited.md monetization angle
- Team section (placeholder)

---

### DEMO.md
First line must be: `# FanIQ — 3-Minute Demo Script`

This is the NORTH STAR of the project. Every technical decision should serve this demo.

Structure the 3 minutes exactly:
- **0:00–0:30** — Hook. One sentence problem. One sentence solution. Show the UI.
- **0:30–1:30** — Live demo part 1. Creator enters @handle, Tinyfish fires (show SSE stream on screen), fans appear in real-time, Redis leaderboard updates live.
- **1:30–2:30** — Live demo part 2. Voice — Mode A (ask about fans), then Mode B (talk to fan persona). This is the killer moment.
- **2:30–3:00** — Autonomy + monetization. Show cited.md publish. Show the x402 payment log. "FanIQ earns money while you sleep."

Include:
- Exact words to say at each timestamp
- What's on screen at each moment
- Which sponsor tools are visible/audible at each point
- Backup plan if Tinyfish is slow (pre-seeded data)
- What NOT to show (keep it tight)

---

### HACKATHON.md
First line must be: `# Hackathon Strategy — Ship to Prod Apr 24`

Include:
- Full judging criteria breakdown (20% each) with our specific strategy per criterion
- Sponsor prize tracks and how FanIQ qualifies for each:
  - Tinyfish track: explain our usage
  - Redis track: explain sorted set + real-time usage
  - Vapi track: explain dual-mode voice agent
  - Ghost/TigerData track: explain profile store
- cited.md requirement and our implementation plan
- Shipables.dev requirement (install skill + publish)
- Risk matrix: what can go wrong, mitigation for each
- Submission checklist (GitHub, cited.md, demo video if needed)
- Judge psychology: what impresses technical judges vs product judges

---

### ARCHITECTURE.md
First line must be: `# FanIQ — System Architecture`

Include:
- Full system diagram described in ASCII art
- Component breakdown with responsibilities
- Data flow: input → Tinyfish → Ghost → Redis → Vapi → cited.md
- Redis key schema (all keys, types, TTLs)
- Ghost data model (member fields + metadata schema)
- API endpoint list:
  - `POST /scan` — start a fan scan job
  - `GET /scan/{job_id}` — SSE stream of progress
  - `GET /fans/{creator_handle}` — top fans from Redis
  - `GET /fan/{creator_handle}/{fan_handle}` — single fan profile
  - `POST /vapi/llm` — custom LLM for Vapi
  - `POST /vapi/webhook` — Vapi call events
  - `POST /publish/{creator_handle}` — publish profiles to cited.md
- Tinyfish job schema (request + expected response shape)
- Fan scoring algorithm (formula + weights + rationale)
- Vapi assistant configuration (both assistants)
- cited.md publish schema
- Sequence diagrams in text for the two main flows:
  1. Scan flow (input → Tinyfish → Ghost → Redis → WebSocket update)
  2. Voice call flow (Vapi → /vapi/llm → Redis/Ghost → Claude → Vapi)

---

### BUILD_PLAN.md
First line must be: `# FanIQ — Build Plan (Apr 24, 11:00 AM – 4:30 PM PT)`

5.5 hours of real coding time. Plan in 30-minute blocks. Be ruthless about priority.
DEMO.md is the north star — build only what serves the demo.

Structure:
- **11:00–11:30** — Environment setup (Redis, env vars, ngrok, Ghost connection test)
- **11:30–12:30** — Tinyfish integration: run-sse client, X crawl job, parse response to fan schema
- **12:30–13:00** — Ghost write: POST member with fan metadata
- **13:00–13:30** — LUNCH (non-negotiable, protect focus)
- **13:30–14:00** — Redis scoring: ZADD pipeline, leaderboard endpoint
- **14:00–14:45** — Vapi Mode A: custom LLM endpoint, intelligence assistant
- **14:45–15:15** — Vapi Mode B: fan persona injection, persona assistant
- **15:15–15:30** — Frontend: minimal UI (handle input, SSE stream display, leaderboard, voice buttons)
- **15:30–15:45** — cited.md publish + x402 payment rail
- **15:45–16:00** — shipables.dev skill install + publish
- **16:00–16:15** — End-to-end test with real creator handle
- **16:15–16:25** — Demo rehearsal (time it: must be ≤3 min)
- **16:25–16:30** — GitHub push + submission

For each block include:
- Exact deliverable (what "done" means)
- The one person responsible (P1/P2/P3/P4 placeholder)
- MVP vs nice-to-have flag
- What to skip if behind schedule

---

### SETUP.md
First line must be: `# FanIQ — Environment Setup`

Include:
- All required env vars with descriptions:
  ```
  TINYFISH_API_KEY=
  GHOST_ADMIN_API_KEY=
  GHOST_API_URL=
  REDIS_URL=redis://localhost:6379
  VAPI_API_KEY=
  VAPI_PHONE_NUMBER_ID=
  ANTHROPIC_API_KEY=
  SENSO_API_KEY=
  NGROK_URL=  # set after ngrok starts
  ```
- Step-by-step account setup for each sponsor:
  - Tinyfish: sign up at agent.tinyfish.ai, grab API key, test with curl
  - Ghost/TigerData: setup instructions + Admin API key location
  - Redis: local install OR Redis Cloud free tier (upstash.com as fallback)
  - Vapi: account setup, create assistant, get phone number, set custom LLM URL
  - Senso/cited.md: docs.senso.ai/docs/hello-world walkthrough
  - Shipables.dev: GitHub auth, install first skill
- Local Redis quickstart: `docker run -d -p 6379:6379 redis:alpine`
- ngrok setup for Vapi webhooks: `ngrok http 8000`
- Python environment: requirements.txt contents
- Test commands to verify each integration before coding:
  - `python scripts/test_tinyfish.py`
  - `python scripts/test_redis.py`
  - `python scripts/test_ghost.py`
  - `python scripts/test_vapi.py`
- Common errors and fixes (Tinyfish rate limits, Ghost auth, Vapi webhook timeout)
- Pre-seeded test data instructions (for demo backup)

---

## 6. AFTER CREATING THE DOCS

Once all 6 markdown files are created, also create:

### `scripts/test_tinyfish.py`
A script that:
1. Calls Tinyfish run-sse with a test URL (agentql.com) and goal "extract pricing plans"
2. Streams the SSE output to console
3. Prints the final JSON result
4. Confirms the API key works

### `scripts/seed_demo_data.py`
A script that pre-seeds Redis and Ghost with ~15 realistic fan profiles for the demo backup.
Fan profiles should look real: handles like @airesearcher_sf, @ml_nerd_42, etc.
With realistic bios, follower counts (500–50000), comment histories, scores.
This is the insurance policy if Tinyfish is slow during the demo.

### `requirements.txt`
All Python dependencies needed:
- fastapi, uvicorn[standard]
- redis[asyncio] (use redis.asyncio)
- httpx (for Tinyfish async calls)
- anthropic
- python-dotenv
- websockets
- Any Ghost API client or requests

---

## 7. IMPORTANT PRINCIPLES

1. **DEMO.md is god.** If a feature doesn't appear in the 3-minute demo, it doesn't exist.
2. **Pre-seed the demo data.** Never demo live-only. Always have seed_demo_data.py ready.
3. **Show the SSE stream.** The Tinyfish live agent stream is visually impressive. Keep it visible.
4. **Voice is the closer.** The Vapi persona mode (talking to a simulated fan) is the moment judges remember. Protect this feature above all others.
5. **cited.md = autonomy score.** The judge criterion for autonomy is answered by showing FanIQ publishing and earning money without human intervention. Don't skip this.
6. **Simplicity wins.** A clean FastAPI backend + minimal HTML frontend beats a complex React app that breaks. Ship something that works.

---

Start with the documentation files. Think through each one carefully. The BUILD_PLAN.md especially
needs to be realistic about what one person can ship in 5.5 hours (assume 1-2 engineers coding).
