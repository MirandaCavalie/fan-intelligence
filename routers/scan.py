from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from models.fan import FanProfile, normalize_handle
from models.job import ScanEvent, ScanJob
from services.profile_store import profile_store
from services.redis_service import dumps, redis_service
from services.tinyfish import demo_scan_stream, live_tinyfish_probe

router = APIRouter()


async def _record_job_event(job_id: str, job: ScanJob, event: ScanEvent) -> None:
    await redis_service.push_scan_event(job_id, event)
    await redis_service.push_event(job.creator_handle, event)


async def run_scan_job(job: ScanJob) -> None:
    job.status = "running"
    job.updated_at = datetime.now(timezone.utc)
    await redis_service.save_scan_job(job)
    stream = demo_scan_stream(job.creator_handle) if job.demo_mode else live_tinyfish_probe(job.creator_handle)
    total = 0
    try:
        async for item in stream:
            if isinstance(item, FanProfile):
                await profile_store.upsert_profile(item)
                total += 1
                await _record_job_event(
                    job.job_id,
                    job,
                    ScanEvent(
                        type="fan_found",
                        sponsor="redis",
                        message=f"Ranked {item.handle} with score {item.score}",
                        fan={
                            "handle": item.handle,
                            "display_name": item.display_name,
                            "score": item.score,
                            "reason": item.reason,
                        },
                    ),
                )
            else:
                await _record_job_event(job.job_id, job, item)
        job.status = "done"
        job.total_fans = total
        job.updated_at = datetime.now(timezone.utc)
        await redis_service.save_scan_job(job)
        await _record_job_event(
            job.job_id,
            job,
            ScanEvent(type="done", sponsor="faniq", message="Scan complete", total_fans=total),
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.updated_at = datetime.now(timezone.utc)
        await redis_service.save_scan_job(job)
        await _record_job_event(
            job.job_id,
            job,
            ScanEvent(type="error", sponsor="faniq", message=str(exc)),
        )


@router.post("/scan")
async def start_scan(body: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, str]:
    creator = normalize_handle(body.get("creator_handle") or "@lexfridman")
    await redis_service.clear_creator(creator)
    job = ScanJob(
        job_id=f"scan_{uuid.uuid4().hex[:10]}",
        creator_handle=creator,
        platforms=body.get("platforms") or ["x"],
        demo_mode=bool(body.get("demo_mode", True)),
    )
    await redis_service.save_scan_job(job)
    background_tasks.add_task(run_scan_job, job)
    return {"job_id": job.job_id, "creator_handle": creator, "status": job.status}


@router.get("/scan/{job_id}")
async def scan_events(job_id: str) -> StreamingResponse:
    job = await redis_service.get_scan_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="scan job not found")

    async def stream():
        index = 0
        while True:
            events = await redis_service.scan_events(job_id, index)
            for scan_event in events:
                index += 1
                yield f"data: {dumps(scan_event.model_dump(mode='json'))}\n\n"
            current = await redis_service.get_scan_job(job_id)
            if current and current.status in {"done", "failed"} and not events:
                break
            await asyncio.sleep(0.25)

    return StreamingResponse(stream(), media_type="text/event-stream")
