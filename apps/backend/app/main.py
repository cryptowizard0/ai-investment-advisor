from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.models.schemas import MessageCreateRequest, ThreadCreateRequest, ThreadSummary
from app.services.agent_gateway import AgentGateway
from app.services.job_service import JobService
from app.services.report_service import ReportService
from app.services.repository import Repository, SqliteRepository


app = FastAPI(title="Investment Platform Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

default_database_path = Path(
    os.getenv("BACKEND_STATE_DB_PATH", Path.cwd() / "output" / "app-state" / "backend.sqlite3")
)
repository = SqliteRepository(default_database_path)
gateway = AgentGateway()


def get_repository() -> Repository:
    return repository


def get_job_service(repo: Repository = Depends(get_repository)) -> JobService:
    return JobService(repo, gateway)


def get_report_service(repo: Repository = Depends(get_repository)) -> ReportService:
    return ReportService(repo)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "layer": "backend"}


@app.post("/api/threads", response_model=ThreadSummary)
async def create_thread(payload: ThreadCreateRequest, repo: Repository = Depends(get_repository)) -> ThreadSummary:
    thread = ThreadSummary(title=payload.title, user_id=payload.user_id)
    return repo.create_thread(thread)


@app.get("/api/threads")
async def list_threads(repo: Repository = Depends(get_repository)) -> list[dict]:
    return [thread.model_dump(mode="json") for thread in repo.list_threads()]


@app.post("/api/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    payload: MessageCreateRequest,
    background_tasks: BackgroundTasks,
    service: JobService = Depends(get_job_service),
) -> dict[str, str]:
    job = service.queue_analysis_job(thread_id, payload)
    background_tasks.add_task(service.run_analysis_job, job.id)
    return {"job_id": job.id, "status": job.status}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, service: JobService = Depends(get_job_service)) -> dict:
    job = service.get_job(job_id)
    report = service.get_report_for_job(job_id)
    return {
        "job": job.model_dump(mode="json"),
        "report_id": report.id if report else None,
    }


@app.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str, repo: Repository = Depends(get_repository)) -> StreamingResponse:
    if repo.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        last_event_count = 0

        while True:
            events = repo.get_events(job_id)
            if last_event_count < len(events):
                for event in events[last_event_count:]:
                    yield f"data: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                last_event_count = len(events)

            job = repo.get_job(job_id)
            if job and job.status in {"completed", "failed", "canceled"} and last_event_count >= len(events):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str, service: ReportService = Depends(get_report_service)) -> dict:
    report = service.get_report(report_id)
    return report.model_dump(mode="json")


@app.get("/api/library")
async def list_reports(service: ReportService = Depends(get_report_service)) -> list[dict]:
    return [item.model_dump(mode="json") for item in service.list_reports()]


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, service: JobService = Depends(get_job_service)) -> dict:
    return await service.cancel_job(job_id)


@app.get("/api/jobs/{job_id}/artifacts")
async def get_job_artifacts(job_id: str, service: JobService = Depends(get_job_service)) -> list[dict]:
    return await service.get_artifacts(job_id)


@app.post("/api/reports/{report_id}/export")
async def export_report(report_id: str, service: ReportService = Depends(get_report_service)) -> PlainTextResponse:
    report = service.get_report(report_id)
    return PlainTextResponse(report.markdown, media_type="text/markdown; charset=utf-8")
