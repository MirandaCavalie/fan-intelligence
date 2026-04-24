# Shipables Skill Plan

FanIQ should include a small skill package for submission and reuse.

## Skill Goal

Teach an agent how to run the FanIQ workflow:

1. collect fan signals
2. score fans in Redis
3. answer fan intelligence questions by voice
4. publish the output

## Folder

```text
skill/
  SKILL.md
  shipables.json
  references/
    workflow.md
    api-contracts.md
```

## `SKILL.md` Draft

```markdown
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
4. Return the top fans with reasons and suggested creator actions.
5. Optionally publish the fan intelligence summary.

## Output

Return:

- top fans
- score explanations
- source URLs
- suggested actions
- publish status
```

## `shipables.json` Draft

```json
{
  "version": "0.1.0",
  "keywords": ["fan-intelligence", "creator-tools", "redis", "vapi", "tinyfish"],
  "categories": ["agents", "creator-tools", "analytics"],
  "config": {
    "env": [
      {
        "name": "TINYFISH_API_KEY",
        "description": "TinyFish API key for web-agent discovery.",
        "required": true,
        "secret": true
      },
      {
        "name": "REDIS_URL",
        "description": "Redis connection string for scoring and profile state.",
        "required": true,
        "secret": true
      },
      {
        "name": "VAPI_API_KEY",
        "description": "Vapi API key for voice assistant integration.",
        "required": false,
        "secret": true
      }
    ]
  }
}
```

## Submission Checklist

- [ ] `skill/SKILL.md`
- [ ] `skill/shipables.json`
- [ ] no real secrets committed
- [ ] README links the skill folder
- [ ] dry-run publish if CLI/account allows it

