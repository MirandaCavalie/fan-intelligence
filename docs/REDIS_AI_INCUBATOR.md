# Redis AI Incubator Integration

Redis is the core sponsor primitive for FanIQ. The MVP uses sorted sets for the visible leaderboard; the Redis AI Incubator angle adds agent memory and context retrieval over fan comments.

Reference: https://redis.io/ai-incubator/

## Redis Cloud Connection

Use one of these forms in `.env`.

Single URL:

```bash
REDIS_URL=redis://default:YOUR_PASSWORD@redis-10864.c13.us-east-1-3.ec2.cloud.redislabs.com:10864
```

Discrete variables:

```bash
REDIS_HOST=redis-10864.c13.us-east-1-3.ec2.cloud.redislabs.com
REDIS_PORT=10864
REDIS_USERNAME=default
REDIS_PASSWORD=YOUR_PASSWORD
REDIS_SSL=false
```

If the Redis Cloud database requires TLS, use `rediss://` in `REDIS_URL` or set `REDIS_SSL=true`.

## FanIQ Redis Usage

Leaderboard:

- `fans:{creator}` sorted set
- `fan_profile:{creator}:{fan}` JSON profile

Agent memory:

- `fan_memory:{creator}:{fan}:{index}` JSON memory snippet
- `fan_memory_scores:{creator}` sorted set for fallback retrieval
- `fan_memory_index:{creator}:{token}` sets for lightweight keyword retrieval

The memory path is intentionally module-light for hackathon reliability. It gives judges a visible Redis AI story without requiring RediSearch/vector modules before the core demo works.

## Demo Talking Point

Say:

> Redis is not just the leaderboard. We also index every fan comment into a Redis-backed agent memory layer, so Vapi can answer from the fan graph plus retrieved context snippets.
