---
name: faniq
description: Discover, score, and summarize high-signal fans for a creator using web-agent discovery, Redis ranking, and voice access.
license: MIT
metadata:
  version: "0.1.0"
---

# FanIQ

Use this skill when a creator wants to identify and act on their highest-signal fans.

## Workflow

1. Start a scan for a creator handle.
2. Collect fan signals from live web sources or seeded demo data.
3. Score fans with Redis sorted sets.
4. Return top fans with source-backed reasons and suggested creator actions.
5. Optionally publish the fan intelligence summary.

## Output

Return:

- top fans
- score explanations
- source URLs
- suggested actions
- publish status
