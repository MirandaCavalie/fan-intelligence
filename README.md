# FanIQ — Fan Intelligence Platform

> Know your fans. Not just your follower count.

## Hackathon MVP

FanIQ is optimized for a reliable 3-minute Ship to Prod hackathon demo. The implemented MVP uses seeded fan data, Redis sorted sets, a FastAPI backend, a one-screen frontend, a Vapi-compatible answer endpoint, a TinyFish-visible scan path, a local publish adapter, and a Shipables skill package.

Ghost/TigerData persistence, live cited.md/Senso publish, LinkedIn crawling, synthetic fan persona voice mode, x402 payments, and Redis vector search are sponsor-depth or stretch integrations. They should not block the core demo.

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
├── main.py                     # FastAPI app + static frontend
├── routers/                    # health, scan, fans, vapi, publish endpoints
├── services/                   # Redis, scoring, seed data, TinyFish, Vapi, publish adapters
├── models/                     # FanProfile, ScanJob, ScanEvent, PublishResult
├── scripts/                    # seed + smoke tests
├── frontend/                   # one-screen demo UI
├── skill/                      # Shipables skill package
├── output/published/           # local publish artifacts
├── requirements.txt
└── .env.example
```

## Quick start

```bash
cp .env.example .env
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Seed demo data
python scripts/seed_demo_data.py --creator @lexfridman --clear

# Start server
uvicorn main:app --reload --port 8000

# Open http://localhost:8000
```

## The cited.md layer

The MVP publishes a local agent-consumable markdown artifact from `POST /publish/{creator}`. If Senso credentials are configured, the publisher attempts a live cited.md/Senso publish and falls back to the local artifact if unavailable.

The intended cited.md layer means:
- Other agents can discover and consume FanIQ's fan intelligence
- Each fetch triggers a micro-payment via x402 payment rails
- FanIQ earns money autonomously, 24/7, without human intervention

Only claim live payments in the demo if the real x402 rail is configured and verified.

## Team

- [ ] Engineer 1 — Tinyfish + Ghost integration
- [ ] Engineer 2 — Redis scoring + FastAPI
- [ ] Engineer 3 — Vapi voice agent + persona
- [ ] Engineer 4 — Frontend + cited.md + demo

---

*Built at Ship to Prod — Agentic Engineering Hackathon, San Francisco, Apr 24 2026*
