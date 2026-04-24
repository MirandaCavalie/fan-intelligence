from __future__ import annotations

import shutil
import subprocess


def ghost_cli_status() -> dict[str, str | bool]:
    path = shutil.which("ghost")
    if not path:
        return {
            "installed": False,
            "mcp": "unknown",
            "version": "",
            "detail": "Ghost CLI not found. Install manually with the Ghost Build installer, then run ghost login and ghost mcp install.",
        }

    version = ""
    detail = "Ghost CLI found."
    try:
        result = subprocess.run(
            [path, "version", "--bare", "--version-check=false"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        version = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        if result.returncode != 0:
            detail = result.stderr.strip() or detail
    except Exception as exc:
        detail = f"Ghost CLI found but version check failed: {exc}"

    return {
        "installed": True,
        "mcp": "install manually with ghost mcp install",
        "version": version,
        "detail": detail,
    }
