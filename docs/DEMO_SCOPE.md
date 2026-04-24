# Demo Scope

This is the scope lock for the hackathon.

## One Sentence

FanIQ helps creators find the fans who actually matter, scores them live, and lets the creator ask a voice agent why those fans are valuable.

## Demo Thesis

Creator analytics usually show audience size. FanIQ shows relationship value.

The demo should feel like this:

1. Enter a creator handle.
2. Watch an agent discover fan signals.
3. See a Redis-backed leaderboard update.
4. Ask a Vapi voice agent who the best fans are and why.
5. Show fan intelligence published out of the app for other agents to consume.

## MVP Demo Path

### 0:00-0:25 - Hook

Show the UI with one handle input and a Scan button.

Say:

> Creators know follower count, but they do not know who their actual fans are. FanIQ finds high-signal fans across the web, scores them live, and lets creators talk to that intelligence layer.

### 0:25-1:15 - Discovery

Click Scan on a prepared creator handle.

Show:

- TinyFish activity stream.
- Fan cards appearing.
- Redis score values changing.
- "source" links for each fan signal.

If live crawl is slow, show a seeded run and narrate that the live run is still progressing.

### 1:15-2:15 - Voice

Start the Vapi assistant.

Ask:

> Who are my top three fans right now, and what should I do with them?

Expected answer:

- Names the top fans.
- Mentions concrete reasons from profile data.
- Suggests one creator action per fan.

This is the required Vapi moment.

### 2:15-2:45 - Publish

Show a publish log:

- profile saved
- profile published to cited.md/Senso
- profile available for agent consumption
- optional x402 payment event if real integration exists

Do not spend time configuring cited.md live.

### 2:45-3:00 - Close

Say:

> FanIQ turns passive audience analytics into an autonomous fan intelligence layer: discover, score, speak, and publish.

## The Real MVP

Must build:

- `POST /scan`
- `GET /scan/{job_id}` or polling event endpoint
- `GET /fans/{creator_handle}`
- Redis sorted set leaderboard
- seeded demo data script
- TinyFish adapter with a working test path
- Vapi assistant that answers from Redis data
- minimal frontend
- cited.md/Senso publish stub or live publish
- Shipables skill files

Nice to have:

- LinkedIn crawl
- second Vapi "fan persona" assistant
- Ghost/TigerData persistence
- real x402 payment rail
- WebSocket updates
- full cross-platform dedupe

## Demo Dataset

Seed data is not cheating. It is the safety layer.

Seed fan profiles should include:

- handle
- display name
- platform
- score
- follower count
- reason for score
- 2-3 real-looking engagement snippets
- source URL
- suggested creator action

The UI should make seeded data visually indistinguishable from live data, but logs should label whether the row came from `tinyfish_live` or `seed`.

## Hard Rule

If a feature cannot be shown or mentioned in the 3-minute demo, it should not be implemented before the demo works end to end.

