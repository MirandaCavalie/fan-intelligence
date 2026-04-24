# Sponsor Docs Notes

These notes summarize the official docs and what matters for FanIQ. They are intentionally implementation-focused.

## Sources Checked

- Devpost: https://ship-to-prod.devpost.com/
- TinyFish docs: https://docs.tinyfish.ai/
- TinyFish API key docs: https://docs.tinyfish.ai/authentication
- TinyFish endpoints: https://docs.tinyfish.ai/key-concepts/endpoints
- Vapi custom LLM server docs: https://docs.vapi.ai/customization/custom-llm/using-your-server
- Vapi custom tools docs: https://docs.vapi.ai/tools/custom-tools
- Redis sorted sets docs: https://redis.io/docs/latest/develop/data-types/sorted-sets/
- Redis vector search docs: https://redis.io/docs/latest/develop/ai/search-and-query/vectors/
- Ghost Admin API docs: https://ghost.org/docs/admin-api/
- Shipables skill docs: https://shipables.dev/docs/publishing/creating-a-skill
- Senso docs entrypoint: https://docs.senso.ai/

## TinyFish

FanIQ should use TinyFish as the visible web-agent layer.

Relevant docs facts:

- TinyFish has Agent, Search, Fetch, and Browser API surfaces.
- REST auth uses `X-API-Key`.
- SDKs can read `TINYFISH_API_KEY`.
- Agent endpoints include sync, async, and SSE-style run patterns.
- SSE is valuable for demo because it provides visible progress.

MVP recommendation:

- Use one reliable TinyFish path first.
- Prefer a controlled target or public page for the first demo run.
- Store every discovered fan signal with a source URL and `source_tool`.
- If LinkedIn or X is flaky, seed the result while still showing one TinyFish test run in the UI.

Do not block the demo on:

- crawling both X and LinkedIn live.
- perfect profile enrichment.
- parsing arbitrary social UIs perfectly.

## Redis

FanIQ has a clean Redis story: real-time leaderboards.

Relevant docs facts:

- Sorted sets map members to scores.
- Sorted set commands are the natural primitive for leaderboards.
- Redis docs explicitly call out leaderboards as a use case for sorted sets.

MVP recommendation:

- Use `ZADD fans:{creator}` to update scores.
- Use `ZREVRANGE fans:{creator} 0 9 WITHSCORES` or equivalent client API to fetch top fans.
- Use hashes for profile data.
- Use lists or streams for event feed.

Minimum demo proof:

- Show score updates in UI.
- Add a small "Redis trace" panel:
  - `ZADD`
  - `HSET`
  - `ZREVRANGE`
  - count of scored fans

Stretch:

- Redis vector search over fan bios/comments.
- semantic search like "which fans care about AI safety?"

## Vapi

FanIQ should keep Vapi simple.

Relevant docs facts:

- Vapi supports custom LLM servers using OpenAI-compatible request/response formats.
- Vapi also supports custom tools.
- For this project, a custom LLM endpoint is useful if the assistant needs to answer from Redis context.

MVP recommendation:

- Build one Vapi assistant first: FanIQ Intelligence.
- It answers questions using top fan data injected from Redis.
- Keep responses short for voice.

Suggested query:

> Who are my top three fans and what should I do with them?

Stretch:

- second assistant for synthetic fan persona.
- tool calls that trigger a scan.
- dynamic assistant creation per selected fan.

Risk:

- Custom LLM streaming can burn time. If it is hard, use a Vapi custom tool that calls `/vapi/fan-answer` and returns a concise answer.

## Ghost / TigerData

Ghost can be useful as a persistent member/profile store, but it is not required for the first visible demo.

MVP recommendation:

- Keep Redis as the source of truth for the hackathon demo.
- Add a Ghost adapter only if account setup is already working.
- If Ghost is used, write fan profiles as members or content records with metadata.

Fallback:

- `services/profile_store.py` writes to Redis only.
- UI still shows "profile persisted".

Pitch framing:

- "Ghost/TigerData is the durable fan intelligence store" only if implemented.

## cited.md / Senso

Devpost-level materials mention publishing agent output and cited.md/Senso. Treat this as a demo requirement if confirmed by sponsor instructions on-site.

MVP recommendation:

- Implement `POST /publish/{creator}` as a publish abstraction.
- If live Senso/cited.md credentials work, call the real API.
- If not, create a publish log and `published_url` stub that is visibly marked as demo mode.

Do not block the core demo on real x402 payments.

Minimum proof:

- One top fan profile becomes a structured public-facing markdown document.
- UI shows `published` status.
- If x402 is not real, show "payment rail pending" rather than pretending.

## Shipables

Shipables requires a skill package mindset.

MVP recommendation:

- Create `skill/SKILL.md`.
- Create `skill/shipables.json`.
- Make the skill explain how an agent runs FanIQ:
  - discover fan signals
  - score with Redis
  - answer with Vapi
  - publish summary

Do this early enough that submission does not depend on last-minute writing.

## Practical Sponsor Priority

MVP sponsor stack:

1. TinyFish
2. Redis
3. Vapi
4. Shipables

Secondary if working:

5. cited.md/Senso
6. Ghost/TigerData

This keeps the project eligible even if the optional sponsor integrations are not fully stable.

