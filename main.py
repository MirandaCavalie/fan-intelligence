from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import fans, health, publish, scan, vapi
from services.redis_service import redis_service

load_dotenv()

app = FastAPI(title="FanIQ", description="Demo-first fan intelligence platform", version="0.1.0")

app.include_router(health.router)
app.include_router(scan.router)
app.include_router(fans.router)
app.include_router(vapi.router)
app.include_router(publish.router)

frontend_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.on_event("shutdown")
async def shutdown() -> None:
    await redis_service.close()
