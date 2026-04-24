# Hackathon Strategy — Ship to Prod Apr 24

> $45k+ in prizes. 5.5 hours. One shot. This document is the competitive strategy.

Current MVP note: Tinyfish, Redis, Vapi Mode A, and Shipables are the core sponsor stack. Ghost/TigerData, live cited.md/Senso, x402, LinkedIn, and Vapi persona mode add sponsor depth only if they are stable before rehearsal.

---

## Schedule

| Time | Event |
|---|---|
| 9:30 AM | Doors open — arrive, set up laptops, test all API keys |
| 10:00 AM | Keynote & opening remarks — listen for prize details |
| 11:00 AM | Start coding |
| 1:30 PM | Lunch — take it, don't code through it |
| 4:30 PM | Project submission deadline — GitHub + demo link |
| 5:00 PM | Finalist presentations |
| 7:00 PM | Awards |

---

## Judging criteria — 20% each

### 1. Autonomy (20%)
**What judges want:** Agent acts on real-time data without manual intervention.

**Our answer:**
- Tinyfish crawl fires automatically from a single API call — no human clicks
- Redis scores update without polling — push-driven
- publish triggers automatically after the fan report is generated
- x402 payment collection is shown only if the live rail is configured and verified
- The whole pipeline from handle input to published + scored profiles requires zero human steps

**What to say:** "After the creator types their handle and hits Scan, FanIQ runs
completely autonomously — crawling, profiling, scoring, publishing, and monetizing
without any further human input."

---

### 2. Idea (20%)
**What judges want:** Meaningful problem, real-world value.

**Our answer:**
- Creators with 100k+ followers genuinely cannot identify their top fans today
- No existing product solves cross-platform fan discovery without API access
- The persona voice mode is a genuinely novel interaction paradigm
- The cited.md monetization model is a new revenue stream for creator tools
- Real TAM: 50M+ content creators worldwide

**What to say:** "Every creator tool today tells you how many followers you have.
None tell you who your fans actually are. FanIQ is the first product to solve this
without requiring API access to any platform."

---

### 3. Technical Implementation (20%)
**What judges want:** Well-built, not just duct-taped.

**Our answer:**
- Async FastAPI with proper SSE streaming (not polling)
- Redis sorted sets — correct data structure choice, not a hack
- Vapi custom LLM pattern — proper OpenAI-compatible endpoint, not a prompt injection
- Fan deduplication across platforms by handle normalization
- Tinyfish concurrent async runs for X and LinkedIn simultaneously
- Error handling: if Tinyfish fails for one platform, the other still completes

**Code quality signals to show if asked:**
- Pydantic models for all fan data
- Async/await throughout — no blocking calls
- Proper env var handling — no hardcoded keys

---

### 4. Tool Use (20%)
**What judges want:** ≥3 sponsor tools used effectively, not superficially.

**Our sponsors and depth of usage:**

| Sponsor | Usage depth | Visible in demo? |
|---|---|---|
| Tinyfish | Core data acquisition, with seeded demo fallback | Yes — SSE stream |
| Ghost/TigerData | Primary persistence layer | Yes — fan cards |
| Redis | Core scoring engine and leaderboard | Yes — live leaderboard |
| Vapi | Primary UX — both voice modes | Yes — voice calls |
| cited.md/Senso | Monetization + publication | Yes — payment log |
| Shipables.dev | Skill installed + published | Mention in pitch |

**Minimum viable sponsor stack:** Tinyfish, Redis, Vapi, and Shipables. Ghost/TigerData and cited.md/Senso add depth if they are stable before demo rehearsal.

---

### 5. Presentation / Demo (20%)
**What judges want:** 3 minutes, impressive, clear story.

**Our strategy:** See DEMO.md for the full script. Key principles:
- Open with a one-line problem statement (everyone understands it)
- Show the agent working live — the SSE stream is visually arresting
- The Vapi persona mode is the "wow" moment — protect it
- End with cited.md earning money autonomously — answers the Autonomy criterion

---

## Sponsor prize tracks

### Tinyfish track
**Our usage:** Tinyfish is the core data acquisition layer. We use the `run-sse` endpoint
for real-time streaming, running two concurrent agents (X + LinkedIn) in async. We use the
goal-based natural language interface for both social media platforms without any API keys.
This demonstrates exactly what Tinyfish is built for: treating real websites as programmable
surfaces.

**Pitch to Tinyfish judges:** "We built cross-platform social media intelligence without
a single platform API. Tinyfish is the reason this product is possible."

### Redis track
**Our usage:** Redis sorted sets (`ZADD`/`ZREVRANGE`) for real-time fan scoring and leaderboard.
Redis hashes for fan profile cache. Redis lists for engagement event streams. Every score update
is instant — when a new fan is discovered, their score hits the leaderboard in sub-millisecond
time. This is the canonical Redis use case: real-time ranking.

**Pitch to Redis judges:** "The leaderboard you see updating live is backed entirely by
Redis sorted sets. No SQL, no polling — pure Redis sorted set semantics."

### Vapi track
**Our usage:** Two distinct voice assistants using Vapi's custom LLM pattern. The FanIQ
Intelligence assistant pulls live data from Redis and Ghost at call time, injecting it as
system context. The Fan Persona assistant is a stretch path that injects a full persona prompt
built from the fan's actual engagement history. Keep voice answers short for demo latency.

**Pitch to Vapi judges:** "We built two completely different voice experiences with one
infrastructure. The persona mode is something nobody has seen before — talking to your fan,
not about your fan."

### Ghost / TigerData track
**Our usage:** Ghost is the agentic database layer. Each fan becomes a Ghost member record
with rich custom metadata — engagement events, raw comments, cross-platform handles, scores.
Ghost provides structured persistence that both the voice agent and the cited.md layer read from.

**Pitch to Ghost/TigerData judges:** "Ghost isn't just a blog platform here — it's a
structured research database that feeds our entire intelligence pipeline."

---

## cited.md requirement

**What to verify on-site:** Publish agent output to cited.md and wire payment rails if sponsor instructions require it and credentials are ready.

**Our implementation:**
1. After each fan profile is written to Ghost, trigger `services/cited.py`
2. Publish a structured fan profile document to cited.md via Senso API
3. Set x402 payment requirement on each profile fetch if the live payment rail is ready
4. Show the publish log in the demo; show earnings only if real

**Setup:** docs.senso.ai/docs/hello-world — complete this in the first 30 minutes of setup.

---

## Shipables.dev requirement

**What's required:** Install ≥1 sponsor skill + publish project as a skill.

**Steps:**
1. Sign up at shipables.dev with GitHub
2. Install the Tinyfish skill: search "tinyfish" in skill directory
3. After 4:00 PM, publish FanIQ as a skill before submission

---

## Risk matrix

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Tinyfish slow during demo | Medium | High | Pre-seed demo data with seed_demo_data.py |
| Vapi webhook URL changes | Low | High | ngrok URL in .env, easy to update |
| Ghost API auth fails | Low | Medium | Test in first 30 min of setup |
| Redis connection drops | Low | High | Docker healthcheck, retry logic |
| cited.md publish fails | Medium | Low | Log errors but don't block main flow |
| Voice latency too high | Medium | Medium | Test with different Vapi models |
| Team member blocked | Medium | Medium | Each person owns one service end-to-end |

---

## Submission checklist

- [ ] GitHub repo created (fresh, no previous projects)
- [ ] All 6 markdown docs committed
- [ ] `requirements.txt` committed
- [ ] `.env.example` committed (no real keys)
- [ ] cited.md publish working — at least one profile published
- [ ] Shipables.dev: skill installed
- [ ] Shipables.dev: FanIQ published as skill
- [ ] Demo rehearsed and timed (≤3 min)
- [ ] seed_demo_data.py run — backup data ready
- [ ] Submitted before 4:30 PM PT

---

## Judge psychology

**Technical judges** (engineers from sponsor companies):
- Show the code if asked — clean async FastAPI impresses
- Mention the Redis sorted set choice specifically — it signals you know the tool
- The Tinyfish no-API-key angle is a great talking point with Homer Wang (Tinyfish Head of Product)

**Product judges** (startup founders, VCs):
- Lead with the problem. "Creators don't know their fans" is instantly relatable.
- The voice persona mode is the demo highlight — make sure they experience it
- The cited.md monetization angle shows you've thought about the business model

**Everyone:**
- Be enthusiastic. You built this in 5 hours. That's impressive regardless of polish.
- Know your 30-second pitch cold. Assume judges are distracted.
- If something breaks, narrate what it would do: "normally Tinyfish would stream here..."
