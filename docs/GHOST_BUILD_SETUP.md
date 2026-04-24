# Ghost Build Setup

Ghost Build is optional sponsor depth for FanIQ. The MVP works with Redis-only profile storage; Ghost adds agent-oriented tooling through the Ghost CLI and MCP server.

## Manual Install

Run this only when you are ready to install software on the machine:

```bash
curl -fsSL https://install.ghost.build/ | sh
ghost login
ghost mcp install
```

The installer downloads the Ghost binary for the local platform and verifies checksums before installation. `ghost login` opens GitHub OAuth, and `ghost mcp install` installs the Ghost MCP server.

## FanIQ Integration

FanIQ currently supports Ghost in two ways:

- `services/ghost.py`: optional Ghost Admin API profile persistence when `GHOST_API_URL` and `GHOST_ADMIN_API_KEY` are configured.
- `services/ghost_build.py`: non-destructive Ghost CLI readiness check for the Ghost Build path.

## Verification

```bash
python scripts/test_ghost_build.py
```

Do not pitch Ghost as live in the demo unless the CLI/MCP path or Admin API adapter has been verified locally.
