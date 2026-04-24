from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from models.fan import normalize_handle

load_dotenv()

VAPI_API_URL = "https://api.vapi.ai"
ASSISTANT_STORE_PATH = Path("output") / "vapi_assistants.json"
INTELLIGENCE_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
PERSONA_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"


def public_base_url() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or os.getenv("NGROK_URL") or "").rstrip("/")


def vapi_model_base_url(base_url: str | None = None) -> str:
    base = (base_url or public_base_url()).rstrip("/")
    return f"{base}/v1" if base else ""


def load_assistant_store(path: Path = ASSISTANT_STORE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"creators": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"creators": {}}


def save_assistant_store(store: dict[str, Any], path: Path = ASSISTANT_STORE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")


def vapi_setup_errors(require_public_key: bool = True) -> list[str]:
    errors: list[str] = []
    if not os.getenv("VAPI_API_KEY"):
        errors.append("VAPI_API_KEY is required to create assistants through the Vapi API.")
    if require_public_key and not os.getenv("VAPI_PUBLIC_KEY"):
        errors.append("VAPI_PUBLIC_KEY is required for the browser Web SDK voice buttons.")
    if not public_base_url():
        errors.append("PUBLIC_BASE_URL or NGROK_URL must point to the public HTTPS tunnel for this FastAPI server.")
    return errors


def intelligence_assistant_payload(creator_handle: str, base_url: str | None = None) -> dict[str, Any]:
    creator = normalize_handle(creator_handle)
    return {
        "name": f"FanIQ Intel {creator}"[:40],
        "firstMessage": "Hey, I'm FanIQ. Ask me who your highest-signal fans are.",
        "maxDurationSeconds": 180,
        "model": {
            "provider": "custom-llm",
            "url": vapi_model_base_url(base_url),
            "model": "faniq-intelligence",
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"creator_handle={creator}. You are FanIQ Intelligence. "
                        "Answer from Redis fan data in short spoken sentences."
                    ),
                }
            ],
        },
        "voice": {"provider": "11labs", "voiceId": INTELLIGENCE_VOICE_ID},
    }


def persona_assistant_payload(
    creator_handle: str,
    fan_handle: str,
    display_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    creator = normalize_handle(creator_handle)
    fan = normalize_handle(fan_handle)
    name = display_name or fan
    return {
        "name": f"FanIQ Persona {fan}"[:40],
        "firstMessage": f"I am a synthetic FanIQ persona based on {name}'s public engagement, not the real person.",
        "maxDurationSeconds": 180,
        "model": {
            "provider": "custom-llm",
            "url": vapi_model_base_url(base_url),
            "model": f"faniq-persona:{creator}:{fan}",
            "temperature": 0.35,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"creator_handle={creator}; fan_handle={fan}. "
                        "You are a synthetic persona grounded in FanIQ Redis profile data. "
                        "Always disclose synthetic status and never claim to be the real person."
                    ),
                }
            ],
        },
        "voice": {"provider": "11labs", "voiceId": PERSONA_VOICE_ID},
    }


def assistant_payloads(
    creator_handle: str,
    fan_handle: str,
    display_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        "intelligence": intelligence_assistant_payload(creator_handle, base_url=base_url),
        "persona": persona_assistant_payload(creator_handle, fan_handle, display_name, base_url=base_url),
    }


async def create_vapi_assistant(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        raise RuntimeError("VAPI_API_KEY is required.")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{VAPI_API_URL}/assistant",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def create_vapi_assistants(
    creator_handle: str,
    fan_handle: str,
    display_name: str | None = None,
    require_public_key: bool = True,
) -> dict[str, Any]:
    errors = vapi_setup_errors(require_public_key=require_public_key)
    if errors:
        raise RuntimeError(" ".join(errors))

    creator = normalize_handle(creator_handle)
    fan = normalize_handle(fan_handle)
    payloads = assistant_payloads(creator, fan, display_name)
    intelligence = await create_vapi_assistant(payloads["intelligence"])
    persona = await create_vapi_assistant(payloads["persona"])

    store = load_assistant_store()
    creators = store.setdefault("creators", {})
    creator_data = creators.setdefault(creator, {"persona_assistants": {}})
    creator_data["intelligence_assistant_id"] = intelligence["id"]
    creator_data.setdefault("persona_assistants", {})[fan] = persona["id"]
    creator_data["public_base_url"] = public_base_url()
    creator_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_assistant_store(store)

    return {
        "creator_handle": creator,
        "fan_handle": fan,
        "intelligence_assistant_id": intelligence["id"],
        "persona_assistant_id": persona["id"],
        "public_base_url": public_base_url(),
        "store_path": str(ASSISTANT_STORE_PATH),
    }


def get_vapi_client_config(creator_handle: str, fan_handle: str | None = None) -> dict[str, Any]:
    creator = normalize_handle(creator_handle)
    fan = normalize_handle(fan_handle) if fan_handle else None
    store = load_assistant_store()
    creator_data = store.get("creators", {}).get(creator, {})
    persona_assistants = creator_data.get("persona_assistants", {})

    intelligence_id = (
        os.getenv("VAPI_ASSISTANT_A_ID")
        or creator_data.get("intelligence_assistant_id")
        or ""
    )
    persona_id = ""
    if fan:
        persona_id = persona_assistants.get(fan, "")
    persona_id = os.getenv("VAPI_PERSONA_ASSISTANT_ID") or os.getenv("VAPI_ASSISTANT_B_ID") or persona_id

    public_key = os.getenv("VAPI_PUBLIC_KEY", "")
    missing = []
    if not public_key:
        missing.append("VAPI_PUBLIC_KEY")
    if not intelligence_id:
        missing.append("VAPI_ASSISTANT_A_ID or output/vapi_assistants.json")
    if fan and not persona_id:
        missing.append(f"persona assistant for {fan}")

    return {
        "creator_handle": creator,
        "fan_handle": fan,
        "public_key": public_key,
        "intelligence_assistant_id": intelligence_id,
        "persona_assistant_id": persona_id,
        "configured": not missing,
        "missing": missing,
        "setup_hint": "Run scripts/setup_vapi.py after PUBLIC_BASE_URL or NGROK_URL points at this server.",
    }
