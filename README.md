# FanIQ — Fan Intelligence Platform

> Know your fans. Not just your follower count.

## Vision

Content creators have millions of followers but zero intelligence about who their actual superfans are. FanIQ is an autonomous agent that discovers, profiles, and ranks the people who engage with a creator across X and LinkedIn — then lets the creator talk to them, literally, through a voice interface powered by their real engagement data. Every fan profile FanIQ generates is published to the open web via cited.md and earns micro-payments when consumed by other agents.

## The 30-second pitch

A creator enters their handle. FanIQ's Tinyfish web agent crawls X and LinkedIn in real-time, extracting every person who has commented, mentioned, or engaged. Those people become enriched fan profiles stored in Ghost/TigerData, scored and ranked live in Redis. The creator then opens a voice call and asks "who are my top fans?" — or picks a fan from the leaderboard and has an actual conversation with an AI persona built from that fan's real comments.

## User journey

1. Creator enters `@handle` + selects platforms → FanIQ dispatches web agents
2. Fans appear in real-time as Tinyfish crawls → Redis leaderboard updates live
3. Creator talks to FanIQ by voice ("Who's my top fan on LinkedIn?") or talks *as* a fan persona built from real data

## Sponsor tracks

| Sponsor | How we use it | Track |
|---|---|---|
| **Tinyfish** | Web agent crawls X + LinkedIn, no API keys needed | Primary |
| **Ghost / TigerData** | Persistent fan profile store, agentic member database | Primary |
| **Redis** | Real-time fan scoring, sorted sets, leaderboard | Primary |
| **Vapi** | Dual-mode voice agent — intelligence + fan persona | Primary |
| **cited.md / Senso** | Publish fan profiles to open web, monetize via x402 | Required |
| **Shipables.dev** | Install sponsor skills, publish FanIQ as a skill | Required |

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI (async) |
| Web agent | Tinyfish `run-sse` endpoint |
| Fan store | Ghost/TigerData Admin API |
| Scoring | Redis sorted sets + hashes |
| Voice | Vapi with custom LLM endpoint |
| AI | Anthropic Claude (persona + intelligence) |
| Publication | cited.md via Senso context layer |
| Transport | ngrok (dev), WebSocket for live updates |

## Hackathon docs

The root docs are the public project narrative. The implementation control room lives in [`docs/`](docs/README.md):

- [`docs/DEMO_SCOPE.md`](docs/DEMO_SCOPE.md) - demo-first scope lock
- [`docs/ROOT_MD_AUDIT.md`](docs/ROOT_MD_AUDIT.md) - markdown audit and recommended cuts
- [`docs/SPONSOR_DOCS_NOTES.md`](docs/SPONSOR_DOCS_NOTES.md) - official-docs-driven integration notes
- [`docs/SPONSOR_INTEGRATION_PLAN.md`](docs/SPONSOR_INTEGRATION_PLAN.md) - MVP sponsor plan and fallbacks
- [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) - backend/API contracts
- [`docs/IMPLEMENTATION_CUTS.md`](docs/IMPLEMENTATION_CUTS.md) - cut order if time gets tight

## Repo structure

```
faniq/
├── main.py                 # FastAPI app entry point
├── routers/
│   ├── scan.py             # POST /scan, GET /scan/{id} SSE
│   ├── fans.py             # GET /fans/{creator}, GET /fan/{creator}/{fan}
│   └── vapi.py             # POST /vapi/llm, POST /vapi/webhook
├── services/
│   ├── tinyfish.py         # Tinyfish async client
│   ├── ghost.py            # Ghost Admin API client
│   ├── redis_service.py    # Scoring, leaderboard, cache
│   ├── scorer.py           # Fan scoring algorithm
│   ├── persona.py          # Fan persona prompt builder
│   └── cited.py            # cited.md publish + x402
├── models/
│   ├── fan.py              # FanProfile, EngagementEvent
│   └── job.py              # ScanJob
├── scripts/
│   ├── test_tinyfish.py    # Integration test
│   ├── test_redis.py       # Integration test
│   ├── test_ghost.py       # Integration test
│   └── seed_demo_data.py   # Pre-seed 15 fan profiles for demo backup
├── frontend/
│   └── index.html          # Minimal UI: handle input, SSE stream, leaderboard, voice
├── requirements.txt
├── .env.example
├── README.md
├── DEMO.md
├── HACKATHON.md
├── ARCHITECTURE.md
├── BUILD_PLAN.md
└── SETUP.md
```

## Quick start

```bash
git clone https://github.com/YOUR_TEAM/faniq
cd faniq
cp .env.example .env
# Fill in all API keys — see SETUP.md

pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Start server
uvicorn main:app --reload --port 8000

# In another terminal — expose for Vapi webhooks
ngrok http 8000
# Copy ngrok URL → NGROK_URL in .env + update Vapi assistant's serverUrl
```

## The cited.md layer

Every fan profile FanIQ generates is published to `cited.md` via Senso's context layer. This means:
- Other agents can discover and consume FanIQ's fan intelligence
- Each fetch triggers a micro-payment via x402 payment rails
- FanIQ earns money autonomously, 24/7, without human intervention

This is what makes FanIQ an **agentic** product, not just a tool.

## Team

- [ ] Engineer 1 — Tinyfish + Ghost integration
- [ ] Engineer 2 — Redis scoring + FastAPI
- [ ] Engineer 3 — Vapi voice agent + persona
- [ ] Engineer 4 — Frontend + cited.md + demo

---

*Built at Ship to Prod — Agentic Engineering Hackathon, San Francisco, Apr 24 2026*
