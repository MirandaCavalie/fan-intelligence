# FanIQ — 3-Minute Demo Script

> This document is the north star of the project. Every technical decision serves this demo.
> If a feature doesn't appear here, it doesn't get built today.

Current implementation note: the reliable demo path is Tinyfish-visible scan events, Redis leaderboard, Vapi Mode A, and a publish log/local artifact. Vapi Mode B, LinkedIn, live cited.md, and x402 are stretch moments only if they are verified before rehearsal.

---

## The single sentence

"Creators have millions of followers but don't know who their actual fans are —
FanIQ finds them across every platform, scores them live, and lets you talk to them."

---

## Screen layout during demo

Split screen: left = terminal/SSE stream (shows agent working), right = FanIQ UI (leaderboard + voice)

---

## The 3-minute script

### 0:00–0:30 — Hook

**Say:** "Right now, if you're a content creator, you know your follower count. You don't know
who your *fans* are — the people who comment on every post, share your content, mention you
across platforms. That's the problem. FanIQ solves it."

**Show:** The FanIQ home screen. Clean. Just a handle input field and platform checkboxes.

**Say:** "I'm going to type in a creator handle, select X and LinkedIn, and hit Scan."

**Action:** Type `@lexfridman`, check X and LinkedIn, click **Scan**.

---

### 0:30–1:30 — Live discovery (Tinyfish + Redis)

**Show:** The SSE stream panel lights up on the left. Real agent steps scrolling:
```
[Tinyfish] Navigating to twitter.com/@lexfridman...
[Tinyfish] Loading replies on post #1...
[Tinyfish] Extracted commenter @airesearcher_sf (12.4k followers)
[Tinyfish] Extracted commenter @ml_nerd_42 (8.1k followers)
[Tinyfish] Navigating to LinkedIn search...
[Tinyfish] Found mention by Sarah Chen, AI Engineer @ Google...
```

**Say:** "That's Tinyfish — a web agent that navigates real sites the way a human would.
No X API, no LinkedIn approval needed. It's just browsing and extracting, in real-time."

**Show:** On the right, fan cards pop into the leaderboard as they're scored.
The live counter updates: "23 fans found... 31... 47..."

**Say:** "Every fan discovered goes into Ghost as a persistent profile, and their engagement
score hits Redis instantly. Watch the leaderboard — this is all live."

**Show:** The top 5 fans ranked, scores updating, cross-platform fans highlighted with a badge.

---

### 1:30–2:30 — Voice (Vapi — the killer moment)

**Say:** "Now here's what makes FanIQ different. I can talk to my fan intelligence layer."

**Action:** Click **Ask FanIQ** → voice call starts (Vapi).

**Say into mic:** "Who is my number one fan right now and why?"

**Vapi responds (Claude-powered):** "Your top fan is @airesearcher_sf — score 847.
They've replied to 14 of your posts this month, have 12,400 followers on X, and their bio
says they're an AI researcher in San Francisco. They're also following you on LinkedIn."

**Say:** "That's Mode A — talking to the intelligence layer. But here's Mode B."

**Action:** Click on **@airesearcher_sf** in the leaderboard → click **Talk to this fan**.

**Say:** "I'm now going to have a conversation with a voice persona built entirely from
this person's real comments and bio."

**Say into mic:** "Hey, what did you think of Lex's last podcast episode?"

**Vapi responds (in character):** "Oh man, the one with Andrej? I actually tweeted about
that — I thought the part about scaling laws was fascinating. Lex pushed back in a way
nobody else does. I shared it to like three different Slack channels."

**Say:** "That's a synthetic fan persona grounded in collected engagement history.
The important part is that the answers stay tied to source snippets we captured."

---

### 2:30–3:00 — Autonomy + monetization (cited.md)

**Show:** The "Published" badge next to each fan profile.

**Say:** "Every profile FanIQ generates is automatically published to cited.md via
Senso's context layer. That means other agents can discover and consume this fan
intelligence. And when they do..."

**Show:** The activity log: `[publish] Fan intelligence artifact generated`

**Say:** "FanIQ turns fan intelligence into an artifact other agents can consume. If the
x402 rail is enabled, that artifact can become a paid endpoint."

**Show:** Final leaderboard — 47 fans, top 10 visible, scores, platform badges.

**Say:** "FanIQ. Know your fans. Not just your follower count."

---

## What's on screen at each moment

| Time | Left panel | Right panel |
|---|---|---|
| 0:00 | Nothing | FanIQ home, handle input |
| 0:20 | — | User types handle, clicks Scan |
| 0:30 | Tinyfish SSE stream starts | "Scanning..." spinner |
| 0:45 | Agent steps scrolling | First fan card appears |
| 1:00 | More agent steps | Leaderboard: 15+ fans, scores updating |
| 1:20 | Stream slowing | 47 fans, leaderboard settled |
| 1:30 | — | Voice panel opens, Vapi call active |
| 1:45 | — | Vapi waveform + transcript |
| 2:00 | — | Fan card selected, persona call active |
| 2:20 | — | Persona conversation transcript |
| 2:30 | — | cited.md publish log |
| 2:45 | — | x402 micro-payment activity |
| 3:00 | — | Final leaderboard |

---

## Sponsor visibility in the demo

| Time | Sponsor | How it appears |
|---|---|---|
| 0:30–1:20 | **Tinyfish** | Live SSE stream showing agent steps |
| 0:45–1:20 | **Ghost/TigerData** | "Profile saved" toast per fan |
| 0:45–1:20 | **Redis** | Live score counter, sorted leaderboard |
| 1:30–2:30 | **Vapi** | Voice waveform, both modes |
| 2:30–3:00 | **cited.md/Senso** | Publish log + payment activity |

---

## Backup plan — if Tinyfish is slow

**Always run `scripts/seed_demo_data.py` before presenting.**

If the live crawl is taking too long during the demo:
1. Say: "The agent is still running in the background — let me show you what it looks like
   when it's complete." Switch to the pre-seeded dataset.
2. The leaderboard is already populated. The demo continues from 1:20 onward.
3. Come back to the live stream at the end: "...and the live crawl just finished."

Pre-seeded handles: `@airesearcher_sf`, `@ml_nerd_42`, `@sarah_chen_ai`, `@devrel_marco`,
`@ux_nerd_kira`, `@podcast_fan_jay`, `@llm_builder_2`, `@techwriter_ally`, and 7 more.

---

## What NOT to show

- Do not show the admin panel / Ghost dashboard — wastes time
- Do not explain the Redis key schema — no one cares during a demo
- Do not show the code — it's there if a judge asks, don't volunteer it
- Do not show LinkedIn results separately from X — the merged leaderboard is the story
- Do not let the voice call run over 45 seconds per interaction
- Do not demo cited.md setup — just show the earned payments log

---

## Rehearsal checklist

- [ ] `seed_demo_data.py` has been run and leaderboard is pre-populated
- [ ] Vapi Mode A assistant is live and responding (test with "who are my top fans")
- [ ] Vapi Mode A is working from Redis-backed fan data
- [ ] Publish log or cited.md publish is wired — profiles show "Published" badge
- [ ] ngrok is running and Vapi webhook URL is updated
- [ ] Microphone is working, no echo, quiet environment
- [ ] Demo is timed: must finish by 2:55 to leave buffer
- [ ] Backup dataset is loaded and leaderboard looks good
