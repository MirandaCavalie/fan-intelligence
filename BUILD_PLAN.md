# FanIQ — Build Plan (Apr 24, 11:00 AM – 4:30 PM PT)

> 5.5 hours. DEMO.md is the north star. Build only what serves the demo.
> Cut anything that doesn't appear in the 3-minute script.

---

## Team roles

| Role | Owns | Person |
|---|---|---|
| P1 — Backend Lead | FastAPI app, Tinyfish service, scan pipeline | TBD |
| P2 — Data Engineer | Ghost service, Redis service, scorer | TBD |
| P3 — Voice Engineer | Vapi LLM endpoint, persona builder | TBD |
| P4 — Frontend + Ship | index.html, cited.md, shipables.dev, demo prep | TBD |

---

## Block 1: 11:00–11:30 — Environment setup (ALL HANDS)

**Everyone does this together in the first 30 minutes.**

### Deliverables (done = all tests green)
- [ ] GitHub repo created, all team members have push access
- [ ] `.env` populated with real keys for all services
- [ ] Redis running (`docker run -d -p 6379:6379 redis:alpine`)
- [ ] `python scripts/test_redis.py` → "Redis OK"
- [ ] `python scripts/test_tinyfish.py` → returns JSON from test URL
- [ ] `python scripts/test_ghost.py` → creates test member
- [ ] ngrok running, URL noted
- [ ] Vapi account open, assistant A created (placeholder LLM URL for now)
- [ ] cited.md / Senso account created (docs.senso.ai/docs/hello-world)
- [ ] Shipables.dev: signed up, Tinyfish skill installed

### If anyone is blocked
Don't wait. Move to your assigned block and unblock later.

---

## Block 2: 11:30–12:30 — Tinyfish crawl pipeline (P1)

**MVP deliverable:** `POST /scan` fires two Tinyfish jobs and streams results via SSE.

### Steps
1. `services/tinyfish.py` — async client for `run-sse`
   - Parse SSE chunks from Tinyfish
   - Yield fan dicts as they are extracted from agent output
   - Run X and LinkedIn jobs concurrently (`asyncio.gather`)
2. `routers/scan.py`
   - `POST /scan` → create job_id, set Redis `crawl_status:{id}=queued`, fire background task
   - `GET /scan/{job_id}` → SSE endpoint that reads from Tinyfish stream and re-emits
3. `models/fan.py` — Pydantic FanProfile, EngagementEvent
4. **Test:** `curl -N localhost:8000/scan/{id}` and watch SSE stream live

### Nice-to-have (skip if behind)
- LinkedIn job (do X first — it's easier)
- Retry logic on Tinyfish errors

### Output consumed by
P2 (Ghost write), P3 (Vapi context), P4 (SSE display)

---

## Block 3: 11:30–12:30 — Ghost + Redis pipeline (P2) [parallel with P2]

**MVP deliverable:** After P1's Tinyfish yields a fan dict, write to Ghost and score in Redis.

### Steps
1. `services/ghost.py`
   - Ghost Admin API: `POST /ghost/api/admin/members/`
   - Upsert by handle (check if exists first)
   - Map FanProfile → Ghost member + metadata dict
2. `services/redis_service.py`
   - `ZADD fans:{creator} {score} {handle}`
   - `HSET fan_profile:{creator}:{handle} ...`
   - `LPUSH events:{creator} {...}`
3. `services/scorer.py` — scoring formula (see ARCHITECTURE.md)
4. `GET /fans/{creator}` → `ZREVRANGE` top 10 with scores
5. `GET /fan/{creator}/{handle}` → `HGETALL` + format

### Test
```python
# Quick smoke test
from services.redis_service import score_fan
score_fan("@lexfridman", mock_fan_profile)  # should ZADD without error
```

---

## Block 4: 12:30–13:00 — Integration + seed data (P1 + P2 together)

**MVP deliverable:** End-to-end: scan → Ghost → Redis → leaderboard endpoint works.

### Steps
1. Wire P1's Tinyfish output into P2's Ghost + Redis writes
2. `GET /fans/@lexfridman` returns ranked list
3. **Run `scripts/seed_demo_data.py`** — this is the demo insurance policy
   - Pre-seed 15 realistic fan profiles into Ghost + Redis
   - Test that the leaderboard shows them sorted correctly

### seed_demo_data.py fan list
```python
SEED_FANS = [
    {"handle": "@airesearcher_sf", "display_name": "Alex Chen", "follower_count": 12400,
     "bio": "AI researcher at Google Brain, SF", "job_title": "Research Scientist",
     "platforms": ["x", "linkedin"], "comment_count": 14, "score": 847},
    {"handle": "@ml_nerd_42", "display_name": "Marco Ruiz", "follower_count": 8100, ...},
    # ... 13 more
]
```

---

## 13:00–13:30 — LUNCH

**Non-negotiable. Protect this.** Eating while coding = mistakes.
Use this time to discuss what's working, unblock anyone who's stuck.

---

## Block 5: 13:30–14:00 — FastAPI + WebSocket live updates (P1)

**MVP deliverable:** Frontend can subscribe to live fan discovery events.

### Steps
1. WebSocket endpoint `WS /ws/{creator_handle}` — broadcasts fan_found events
2. When Redis ZADD happens, push `{"type":"fan_found","fan":{...}}` to all WS subscribers
3. Leaderboard endpoint also works via REST polling (fallback if WS is tricky)

### Skip if behind schedule
Use polling (`GET /fans/{creator}` every 2 seconds) instead of WebSocket.
The demo still works — just not quite as smooth.

---

## Block 6: 13:30–14:45 — Vapi Mode A — Intelligence (P3)

**MVP deliverable:** Creator can call Vapi and ask "who are my top fans?" and get a real answer.

### Steps
1. `routers/vapi.py` — `POST /vapi/llm` endpoint
   - Parse Vapi's OpenAI-compatible request
   - Detect assistant type from model name: `"faniq-intelligence"` vs `"faniq-persona:*"`
   - For intelligence mode:
     - Extract creator handle from call metadata (passed in assistant config)
     - `ZREVRANGE fans:{creator} 0 4 WITHSCORES` → top 5 fans
     - For each fan: `HGETALL fan_profile:{creator}:{handle}`
     - Build context string from fan data
     - Inject into Claude system prompt
     - Stream Claude response back in OpenAI SSE format
2. Update Vapi Assistant A `serverUrl` with real ngrok URL
3. **Test:** Call the assistant from Vapi dashboard, ask about fans

### Vapi LLM endpoint pattern
```python
@router.post("/vapi/llm")
async def vapi_llm(request: Request):
    body = await request.json()
    model = body.get("model", "")
    messages = body.get("messages", [])
    
    if model == "faniq-intelligence":
        # fetch top fans from Redis, inject as context
        system = build_intelligence_system(creator_handle, top_fans)
    elif model.startswith("faniq-persona:"):
        fan_handle = model.split(":")[1]
        # fetch fan profile from Ghost/Redis
        system = build_persona_system(fan_profile, creator_handle)
    
    # stream Claude response in OpenAI SSE format
    return StreamingResponse(stream_claude(system, messages), media_type="text/event-stream")
```

---

## Block 7: 14:45–15:15 — Vapi Mode B — Fan Persona (P3)

**MVP deliverable:** Creator picks a fan, starts voice call, talks to persona built from real data.

### Steps
1. `services/persona.py` — `build_persona_system(fan_profile, creator_handle)` → str
   - Use `PERSONA_SYSTEM` template from ARCHITECTURE.md
   - Format raw_comments as numbered list
   - Keep under 800 tokens
2. Update Vapi LLM endpoint to handle `faniq-persona:{handle}` model
3. Create Vapi Assistant B (Fan Persona) programmatically via Vapi API
   - Different voice from Assistant A
   - Different first message
4. **Test:** Pick `@airesearcher_sf` from seed data, start persona call

### The demo line
"Hey, what did you think of Lex's last podcast episode?"
Make sure the persona has enough comment data to answer in character.

---

## Block 8: 15:15–15:30 — Frontend UI (P4)

**MVP deliverable:** A working HTML page with: handle input, scan button, SSE stream, leaderboard, voice buttons.

### Keep it dead simple
- Vanilla HTML + CSS + JS (no React, no build step, nothing to break)
- Two columns: left = SSE agent stream, right = leaderboard cards
- "Ask FanIQ" button (triggers Vapi web call or shows phone number)
- "Talk to fan" button on each leaderboard card

### Minimum viable HTML structure
```html
<div class="container">
  <div class="input-row">
    <input id="handle" placeholder="@creator_handle">
    <select id="platforms" multiple>X LinkedIn</select>
    <button onclick="startScan()">Scan</button>
  </div>
  <div class="main">
    <div id="stream-panel"><!-- SSE steps --></div>
    <div id="leaderboard"><!-- Fan cards --></div>
  </div>
  <div id="voice-panel"><!-- Vapi web call widget --></div>
</div>
```

---

## Block 9: 15:30–15:45 — cited.md + x402 (P4)

**MVP deliverable:** Fan profiles publish to cited.md, show earnings in UI.

### Steps
1. `services/cited.py` — POST profile to Senso API
2. Wire `POST /publish/{creator}` endpoint — publishes all profiles
3. Auto-trigger after scan completes
4. Add earnings log to frontend: `[cited.md] Fetch by agent → $0.002 earned`
5. **This is required by the hackathon rules** — don't skip it

---

## Block 10: 15:45–16:00 — Shipables.dev + cleanup (P4)

### Steps
1. Publish FanIQ as a skill on shipables.dev
2. Clean up any console errors in the UI
3. Make sure seed data is loaded and leaderboard looks good

---

## Block 11: 16:00–16:15 — End-to-end test

**ALL HANDS. This is the most important 15 minutes of the day.**

Run the full demo flow with `@lexfridman` (or a smaller account for speed):
1. Enter handle → click Scan
2. Watch SSE stream
3. Leaderboard populates
4. Voice Mode A → ask about fans
5. Voice Mode B → talk to top fan
6. cited.md shows published profiles

Fix any broken edges. Do NOT add features.

---

## Block 12: 16:15–16:25 — Demo rehearsal

**Practice the 3-minute script from DEMO.md. Time it.**

- Person doing the demo talks through it out loud
- Rest of team watches and flags anything confusing
- Confirm mic works, no echo, quiet enough
- Switch to seed data backup if live crawl is slow

---

## Block 13: 16:25–16:30 — Submit

- [ ] `git add . && git commit -m "Ship to prod" && git push`
- [ ] Submit GitHub URL on hackathon platform
- [ ] One final full run to confirm nothing is broken

---

## Cut list (if behind schedule)

Cut in this order — least impact to demo first:

1. LinkedIn Tinyfish job (just do X, demo still works)
2. WebSocket live updates (use polling instead)
3. cited.md x402 payment rail (just show the publish, skip payment)
4. Vapi Mode B dynamic persona creation (hardcode 2 personas instead)
5. Cross-platform dedup (simpler scoring, still looks correct)

**Never cut:**
- Tinyfish SSE stream visible in UI (the WOW moment)
- Redis leaderboard (the proof of real-time scoring)
- Vapi Mode A (intelligence voice — simplest voice demo)
- cited.md publish (required by hackathon rules)
- seed_demo_data.py (insurance policy)
