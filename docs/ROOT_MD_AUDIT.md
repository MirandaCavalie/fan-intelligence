# Root Markdown Audit

This is the audit of the current root-level markdown files.

## Summary

The idea is strong: creators do not need another follower counter; they need a ranked map of who actually engages and why they matter.

The risk is scope. The current docs promise too much for a 5.5-hour hackathon:

- X plus LinkedIn crawling.
- Ghost/TigerData as primary persistence.
- Redis leaderboard.
- two Vapi modes.
- cited.md publishing.
- x402 payments.
- Shipables publishing.
- WebSocket or SSE live UI.
- custom LLM streaming.

That is a compelling product roadmap, but too large for a reliable hackathon demo. The docs should make the MVP and cut line much sharper.

## File-by-File Recommendation

| File | Recommendation | Why |
|---|---|---|
| `README.md` | Keep, but simplify after implementation starts | Good public-facing pitch, but it overstates completed functionality before any code exists. |
| `DEMO.md` | Keep as root north star | This is the strongest document. It should stay root-level and drive build decisions. |
| `HACKATHON.md` | Keep, but soften claims | Good judge strategy. Remove lines like "no fallback" and avoid promising six deep sponsor integrations unless they work. |
| `ARCHITECTURE.md` | Keep, but mark MVP vs stretch | Useful, but currently reads like full product architecture. Split reality: Redis + TinyFish + Vapi are MVP; Ghost/cited/x402/LinkedIn/persona are stretch unless validated early. |
| `BUILD_PLAN.md` | Keep, but rewrite timing | Current plan assumes 4 parallel engineers and too many integrations. Needs a single critical path version. |
| `SETUP.md` | Keep, but create a "minimum setup" section | Current setup requires many accounts before coding. First 30 minutes should only verify TinyFish, Redis, Vapi, and one LLM. |
| `CLAUDE_CODE_PROMPT.md` | Move to `docs/archive/` or delete after scaffold exists | It is a generator prompt, not project documentation. It also has stale date references and can confuse future contributors. |

## Specific Issues To Fix

### Date Drift

Some files mention Apr 24, 2025. The hackathon date is Apr 24, 2026.

Fix:

- `README.md` footer.
- `CLAUDE_CODE_PROMPT.md` intro.
- example timestamps in `ARCHITECTURE.md`.

### Claims That Are Too Strong

Avoid claiming:

- "no fallback" for TinyFish or Redis.
- "sub-2s latency" before measured.
- "x402 payment collection is fully autonomous" before implemented.
- "No hallucination" for persona mode. Better: "grounded in collected engagement data."

### Legal/Platform Risk

Do not pitch "no LinkedIn approval needed" too aggressively. Better:

> TinyFish lets us demonstrate a web-agent workflow over public web surfaces without building custom platform integrations.

### Product Risk

The fan persona mode is memorable, but it can feel creepy if phrased as "talk to this real person."

Safer framing:

> Talk to a synthetic fan persona grounded in public engagement history.

### Scope Risk

The real MVP should prioritize:

1. Live/visible discovery.
2. Redis leaderboard.
3. Vapi intelligence assistant.
4. Publish log.

Persona mode should be a fallback-ready stretch. If it works, it is the wow moment. If it does not, Mode A is enough to preserve the Vapi track.

## Recommended Root Doc Changes

Make these root docs align:

- `README.md`: add "Hackathon MVP" section and link `/docs`.
- `DEMO.md`: keep two modes, but label Mode B as stretch/wow.
- `BUILD_PLAN.md`: put Vapi Mode A before Mode B, and give Ghost/cited/x402 a stub fallback.
- `HACKATHON.md`: remove "6 sponsor tools" boast unless all are working; say "3 required, 3 optional depth".
- `ARCHITECTURE.md`: add "MVP architecture" before the full architecture.
- `SETUP.md`: split "Minimum setup" and "optional sponsor setup".

## What I Would Delete Or Move

Move:

- `CLAUDE_CODE_PROMPT.md` to `docs/archive/CLAUDE_CODE_PROMPT.md` after implementation begins.

Delete later:

- Any setup section for integrations you do not actually use in the submitted project.

Do not delete today:

- Existing docs are useful for context until the implementation path is chosen.

