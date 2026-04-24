from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ghost_build import ghost_cli_status


if __name__ == "__main__":
    status = ghost_cli_status()
    print(json.dumps(status, indent=2))
    if not status["installed"]:
        print("Ghost Build setup is optional for MVP. Install only when ready:")
        print("curl -fsSL https://install.ghost.build/ | sh")
        print("ghost login")
        print("ghost mcp install")
