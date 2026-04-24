# FanIQ — Environment Setup

> Complete this during Block 1 (11:00–11:30 AM). All 4 team members go through this together.
> Goal: every integration test green before 11:30 AM.

---

## Required env vars

Create `.env` in the project root:

```bash
# Tinyfish — sign up at agent.tinyfish.ai
TINYFISH_API_KEY=

# Ghost / TigerData — get from your Ghost instance admin panel
GHOST_API_URL=https://YOUR_GHOST_INSTANCE.ghost.io
GHOST_ADMIN_API_KEY=     # format: {id}:{secret} from Ghost Admin > Integrations

# Redis
REDIS_URL=redis://localhost:6379   # or Upstash URL if using cloud

# Vapi — sign up at vapi.ai
VAPI_API_KEY=
VAPI_PHONE_NUMBER_ID=    # from Vapi dashboard > Phone Numbers
VAPI_ASSISTANT_A_ID=     # created after setup
VAPI_ASSISTANT_B_ID=     # created after setup

# Anthropic Claude
ANTHROPIC_API_KEY=       # platform.anthropic.com

# Senso / cited.md
SENSO_API_KEY=           # from senso.ai dashboard

# ngrok (set after you start ngrok)
NGROK_URL=https://YOUR_ID.ngrok.io   # no trailing slash

# App config
PORT=8000
CREATOR_HANDLE=@lexfridman   # default handle for demo
```

---

## Account setup — step by step

### 1. Tinyfish (10 min)

1. Go to https://agent.tinyfish.ai — sign up with GitHub
2. Copy your API key from the dashboard
3. Test immediately:
```bash
curl -N -X POST https://agent.tinyfish.ai/v1/automation/run-sse \
  -H "X-API-Key: $TINYFISH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://agentql.com", "goal": "Find all pricing plans and their prices. Return JSON."}'
```
You should see SSE steps streaming. Final line contains the JSON result.

4. Verify the 500 free steps are available (no credit card needed for hackathon usage)

---

### 2. Ghost / TigerData (10 min)

**Option A: TigerData provides a Ghost instance (check with their team at the hackathon)**

**Option B: Ghost Cloud free trial**
1. Go to https://ghost.org → Start free trial
2. Create a new publication
3. Go to Settings > Integrations > Add custom integration
4. Name it "FanIQ" → copy the Admin API Key (format: `id:secret`)
5. Copy your site URL (e.g., `https://my-faniq.ghost.io`)

Test:
```bash
python scripts/test_ghost.py
# Should print: "Ghost OK — test member created"
```

---

### 3. Redis (5 min)

**Option A: Local Docker (recommended for hackathon)**
```bash
docker run -d -p 6379:6379 --name faniq-redis redis:alpine
```

**Option B: Upstash (free tier, cloud Redis)**
1. https://upstash.com → create free Redis database
2. Copy the `UPSTASH_REDIS_REST_URL` → use as `REDIS_URL`

Test:
```bash
python scripts/test_redis.py
# Should print: "Redis OK — PING returned PONG"
```

---

### 4. Vapi (15 min)

1. Go to https://vapi.ai → sign up
2. Go to Dashboard > Phone Numbers → buy or get a test number → copy ID
3. Create Assistant A (FanIQ Intelligence):
   - Name: "FanIQ Intelligence"
   - LLM: Custom LLM → URL: `http://placeholder.com/vapi/llm` (update after ngrok)
   - Model name: `faniq-intelligence`
   - Voice: 11labs, voice ID: `21m00Tcm4TlvDq8ikWAM` (Rachel — clear and professional)
   - First message: "Hey! I'm FanIQ. Ask me anything about your fans."
   - Copy assistant ID → `VAPI_ASSISTANT_A_ID`
4. Create Assistant B (Fan Persona) — same LLM URL, model: `faniq-persona:default`
   - Voice: `AZnzlk1XvdvUeBnXmlld` (different voice)
   - First message: "Hey, what's up?"
   - Copy assistant ID → `VAPI_ASSISTANT_B_ID`

**After ngrok is running**, update both assistants' LLM URL to `$NGROK_URL/vapi/llm`

Test (after server is running):
```bash
# From Vapi dashboard > Test your assistant
# Ask: "Who are my top fans?"
# Should get a response (even if no fans are seeded yet)
```

---

### 5. Senso / cited.md (5 min)

1. Go to https://docs.senso.ai/docs/hello-world
2. Follow the 5-minute quickstart
3. Get your API key → `SENSO_API_KEY`
4. Test with the hello-world example from their docs

---

### 6. Anthropic Claude (2 min)

1. https://platform.anthropic.com → create API key
2. Recommended model: `claude-sonnet-4-5` (fast, good for voice latency)

---

### 7. ngrok (5 min)

```bash
# Install if needed
brew install ngrok  # or download from ngrok.com

# Start tunnel
ngrok http 8000

# Copy the https URL (e.g. https://abc123.ngrok.io)
# → paste into NGROK_URL in .env
# → update Vapi assistant serverUrl to https://abc123.ngrok.io/vapi/llm
```

**Important:** ngrok URL changes every restart. If you restart ngrok, update `.env` AND Vapi.

---

### 8. Shipables.dev (5 min)

1. Go to https://shipables.dev → sign in with GitHub
2. Search for "tinyfish" → install the Tinyfish skill
3. Note: publish FanIQ as a skill before 4:30 PM submission

---

## Python environment

```bash
# Create virtualenv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### requirements.txt
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
redis[asyncio]==5.0.0
httpx==0.27.0
anthropic==0.34.0
python-dotenv==1.0.0
pydantic==2.8.0
websockets==13.0
aiohttp==3.10.0
python-jose==3.3.0
```

---

## Integration test scripts

### `scripts/test_tinyfish.py`
```python
import asyncio, os, httpx
from dotenv import load_dotenv
load_dotenv()

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST",
            "https://agent.tinyfish.ai/v1/automation/run-sse",
            headers={"X-API-Key": os.getenv("TINYFISH_API_KEY")},
            json={"url": "https://agentql.com",
                  "goal": "Find all pricing plans. Return JSON array with name and price."}
        ) as r:
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    print(line)
    print("Tinyfish OK")

asyncio.run(test())
```

### `scripts/test_redis.py`
```python
import asyncio, redis.asyncio as redis, os
from dotenv import load_dotenv
load_dotenv()

async def test():
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    pong = await r.ping()
    assert pong, "Redis not responding"
    await r.zadd("test:faniq", {"@testfan": 100})
    result = await r.zrevrange("test:faniq", 0, 0, withscores=True)
    assert result[0][0] == b"@testfan"
    await r.delete("test:faniq")
    await r.aclose()
    print("Redis OK — PING returned PONG, sorted set operations work")

asyncio.run(test())
```

### `scripts/test_ghost.py`
```python
import requests, os, jwt, time
from dotenv import load_dotenv
load_dotenv()

def get_ghost_token():
    key = os.getenv("GHOST_ADMIN_API_KEY")
    key_id, secret = key.split(":")
    payload = {"iat": int(time.time()), "exp": int(time.time()) + 300, "aud": "/admin/"}
    token = jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers={"kid": key_id})
    return token

url = os.getenv("GHOST_API_URL")
token = get_ghost_token()
r = requests.post(f"{url}/ghost/api/admin/members/",
    headers={"Authorization": f"Ghost {token}"},
    json={"members": [{"email": "test@faniq.local", "name": "FanIQ Test", "note": "integration test"}]})
print(f"Ghost status: {r.status_code}")
assert r.status_code in [200, 201], f"Ghost error: {r.text}"
print("Ghost OK — test member created")
```

---

## Running the server

```bash
# Activate venv
source venv/bin/activate

# Load env and start
uvicorn main:app --reload --port 8000

# Verify
curl http://localhost:8000/health
# → {"status": "ok", "redis": "connected", "ghost": "connected"}
```

---

## Common errors + fixes

| Error | Cause | Fix |
|---|---|---|
| `GHOST_ADMIN_API_KEY invalid` | Wrong format | Must be `{id}:{secret}` with colon |
| `Tinyfish 429 Too Many Requests` | Rate limited | Use `run-async` instead of `run-sse` |
| `Vapi webhook timeout` | ngrok URL stale | Restart ngrok, update Vapi assistant |
| `Redis WRONGTYPE` | Key type mismatch | `redis-cli FLUSHDB` to reset dev data |
| `Vapi LLM 500` | Claude API error | Check `ANTHROPIC_API_KEY`, check model name |
| `ngrok session expired` | Free ngrok limit | Upgrade or restart (update Vapi URL again) |
| `Ghost member already exists` | Duplicate handle | Use upsert: check by email first |
| `Tinyfish empty result` | Goal too vague | Make goal more specific, add "Return JSON array" |

---

## Demo backup — pre-seed command

Run this before the demo to ensure the leaderboard is populated:

```bash
python scripts/seed_demo_data.py --creator @lexfridman
# Inserts 15 realistic fan profiles into Ghost + Redis
# Prints: "Seeded 15 fans for @lexfridman — leaderboard ready"
```

Verify with:
```bash
curl http://localhost:8000/fans/@lexfridman | python -m json.tool
# Should show top 10 fans with scores
```
