# FanIQ Docs

This folder is the working control room for the hackathon build. Root markdown files are the public-facing project docs; this folder contains the sharper implementation notes, scope decisions, official docs synthesis, and cut decisions.

## Read Order

1. `DEMO_SCOPE.md` - the build north star.
2. `ROOT_MD_AUDIT.md` - what to keep, change, move, or delete from the current markdown set.
3. `SPONSOR_DOCS_NOTES.md` - official-docs-driven integration notes.
4. `SPONSOR_INTEGRATION_PLAN.md` - exact MVP path for TinyFish, Redis, Vapi, cited.md/Senso, Shipables, and Ghost/TigerData.
5. `API_CONTRACTS.md` - endpoint and payload contracts to implement.
6. `IMPLEMENTATION_CUTS.md` - what to cut first when time gets tight.

## Current Product Decision

FanIQ should be built as a 3-minute demo product, not a complete creator CRM.

The demo should prove:

- TinyFish can discover fan-like signals from live web pages or a controlled live target.
- Redis can score and rank fans in real time with sorted sets.
- Vapi can answer creator questions from the Redis-backed fan graph.
- cited.md/Senso or a cited.md-style publish log can show agent output leaving the app.
- Shipables can package the workflow as a reusable skill.

Everything else is optional.

