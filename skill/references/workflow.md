# FanIQ Workflow

FanIQ is built around a demo-safe creator intelligence pipeline.

1. A creator handle starts a scan.
2. TinyFish live discovery or demo-visible scan events produce fan signals.
3. Redis stores fan profiles and updates `fans:{creator}` sorted sets.
4. Vapi calls `/vapi/llm` to answer from Redis-backed fan context.
5. `/publish/{creator}` writes an agent-consumable report.

The core demo can run from seeded data. Live integrations add sponsor depth but should not block the flow.
