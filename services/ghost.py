from __future__ import annotations

import os
import time

import httpx
from jose import jwt

from models.fan import FanProfile


def _ghost_token() -> str:
    key = os.getenv("GHOST_ADMIN_API_KEY", "")
    if ":" not in key:
        raise RuntimeError("GHOST_ADMIN_API_KEY must use {id}:{secret} format")
    key_id, secret = key.split(":", 1)
    payload = {"iat": int(time.time()), "exp": int(time.time()) + 300, "aud": "/admin/"}
    return jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers={"kid": key_id})


async def ghost_upsert_profile(profile: FanProfile) -> None:
    base_url = os.getenv("GHOST_API_URL", "").rstrip("/")
    if not base_url:
        raise RuntimeError("GHOST_API_URL missing")

    email_handle = profile.handle.strip("@").replace(".", "_")
    payload = {
        "members": [
            {
                "email": f"{email_handle}@faniq.local",
                "name": profile.display_name,
                "note": profile.model_dump_json(),
                "labels": [{"name": "faniq"}, {"name": profile.creator_handle.strip("@")}],
            }
        ]
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{base_url}/ghost/api/admin/members/",
            headers={"Authorization": f"Ghost {_ghost_token()}"},
            json=payload,
        )
        response.raise_for_status()
