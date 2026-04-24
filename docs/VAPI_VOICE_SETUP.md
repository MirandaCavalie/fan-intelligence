# Vapi Voice Setup

FanIQ uses Vapi Custom LLM. Vapi should point at the OpenAI-compatible endpoint:

```text
POST {PUBLIC_BASE_URL}/v1/chat/completions
```

## Env

```bash
VAPI_API_KEY=          # private server-side key
VAPI_PUBLIC_KEY=       # public browser Web SDK key
PUBLIC_BASE_URL=       # public HTTPS URL for this FastAPI server
NGROK_URL=             # fallback if PUBLIC_BASE_URL is empty
VAPI_ASSISTANT_A_ID=   # optional env override for Mode A
VAPI_PERSONA_ASSISTANT_ID=  # optional env override for Mode B
```

`VAPI_ASSISTANT_A_ID` and `VAPI_PERSONA_ASSISTANT_ID` are created by Vapi when assistants are created. They are not required before setup.

## Create Assistants

Start FastAPI and expose it with ngrok or another HTTPS tunnel, then run:

```bash
python scripts/setup_vapi.py --creator @lexfridman --persona @airesearcher_sf
```

The script creates:

- Mode A: `faniq-intelligence`
- Mode B: `faniq-persona:@lexfridman:@airesearcher_sf`

Generated assistant IDs are saved to ignored local file:

```text
output/vapi_assistants.json
```

Safe dry run:

```bash
python scripts/setup_vapi.py --creator @lexfridman --persona @airesearcher_sf --dry-run
```

## Local Tests

```bash
python scripts/test_vapi_custom_llm.py
```

Streaming curl:

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"faniq-intelligence","stream":true,"metadata":{"creator_handle":"@lexfridman"},"messages":[{"role":"user","content":"Who are my top fans?"}]}'
```
