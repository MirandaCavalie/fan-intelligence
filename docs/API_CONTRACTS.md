# API Contracts

These are the implementation contracts for the hackathon MVP.

## Health

```text
GET /health
```

Response:

```json
{
  "status": "ok",
  "redis": "connected",
  "tinyfish": "configured",
  "mode": "live | demo"
}
```

## Start Scan

```text
POST /scan
```

Request:

```json
{
  "creator_handle": "@lexfridman",
  "platforms": ["x"],
  "demo_mode": false
}
```

Response:

```json
{
  "job_id": "scan_123",
  "creator_handle": "@lexfridman",
  "status": "queued"
}
```

## Scan Events

Use either SSE or polling. SSE is nicer for demo; polling is acceptable.

```text
GET /scan/{job_id}
```

Event examples:

```json
{
  "type": "agent_step",
  "sponsor": "tinyfish",
  "message": "Scanning recent posts",
  "timestamp": "2026-04-24T12:30:00Z"
}
```

```json
{
  "type": "fan_found",
  "sponsor": "redis",
  "fan": {
    "handle": "@airesearcher_sf",
    "display_name": "Alex Chen",
    "score": 847,
    "reason": "14 replies, cross-platform engagement, AI researcher audience"
  }
}
```

## Top Fans

```text
GET /fans/{creator_handle}
```

Response:

```json
{
  "creator_handle": "@lexfridman",
  "total_fans": 15,
  "top_fans": [
    {
      "handle": "@airesearcher_sf",
      "display_name": "Alex Chen",
      "score": 847,
      "platforms": ["x", "linkedin"],
      "reason": "Replies often, has relevant AI audience, appears across platforms",
      "suggested_action": "Invite to a private community Q&A",
      "source_urls": ["https://example.com/post/1"]
    }
  ]
}
```

## Single Fan

```text
GET /fan/{creator_handle}/{fan_handle}
```

Response:

```json
{
  "handle": "@airesearcher_sf",
  "display_name": "Alex Chen",
  "bio": "AI researcher in SF",
  "score": 847,
  "raw_comments": [
    "Loved the episode on scaling laws",
    "Shared this with our research group"
  ],
  "source_urls": ["https://example.com/post/1"],
  "suggested_action": "Invite to a research-focused AMA"
}
```

## Vapi Intelligence Answer

If using custom tools:

```text
POST /vapi/tools
```

Request:

```json
{
  "message": {
    "type": "tool-calls",
    "toolCallList": [
      {
        "id": "call_123",
        "name": "get_top_fans",
        "arguments": {
          "creator_handle": "@lexfridman",
          "limit": 3
        }
      }
    ]
  }
}
```

Response:

```json
{
  "results": [
    {
      "toolCallId": "call_123",
      "result": "Your top fan is Alex Chen, followed by Marco Ruiz and Sarah Chen. Alex is strongest because..."
    }
  ]
}
```

If using custom LLM:

```text
POST /vapi/llm
POST /chat/completions
POST /v1/chat/completions
```

The endpoint injects Redis fan data into the model context and returns an OpenAI-compatible response.

Use `stream: true` for Vapi voice calls. The streaming response is `text/event-stream` with OpenAI-style `chat.completion.chunk` events and a final `data: [DONE]`.

Mode selection:

```json
{"model": "faniq-intelligence"}
```

```json
{"model": "faniq-persona:@lexfridman:@airesearcher_sf"}
```

Browser voice config:

```text
GET /vapi/client-config?creator_handle=@lexfridman&fan_handle=@airesearcher_sf
```

Response includes `VAPI_PUBLIC_KEY` and generated assistant IDs only; it never exposes `VAPI_API_KEY`.

## Redis AI Memory Search

```text
GET /memory/{creator_handle}/search?q=AI%20research
```

Response:

```json
{
  "creator_handle": "@lexfridman",
  "query": "AI research",
  "results": [
    {
      "fan_handle": "@airesearcher_sf",
      "display_name": "Alex Chen",
      "content": "The scaling laws episode clarified why evals need to move faster than capability gains.",
      "match_score": 949,
      "matched_terms": ["research"]
    }
  ]
}
```

This is the Redis AI Incubator-inspired memory layer for the demo. It uses Redis-native keys and can later be upgraded to RedisVL or vector search.

## Publish

```text
POST /publish/{creator_handle}
```

Request:

```json
{
  "mode": "live | demo"
}
```

Response:

```json
{
  "creator_handle": "@lexfridman",
  "published": true,
  "url": "https://cited.md/faniq/lexfridman",
  "payment_enabled": false,
  "fallback_file": "output/published/lexfridman.md"
}
```

## Data Model

```json
{
  "handle": "@fan",
  "display_name": "Fan Name",
  "platforms": ["x"],
  "follower_count": 1200,
  "comment_count": 4,
  "reply_count": 2,
  "cross_platform": false,
  "raw_comments": ["comment text"],
  "source_urls": ["https://..."],
  "score": 123,
  "reason": "why this fan ranks high",
  "suggested_action": "what creator should do next"
}
```
