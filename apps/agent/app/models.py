from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "completed", "failed", "canceled"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisJobRequest(BaseModel):
    run_id: str
    user_id: str
    thread_id: str
    analysis_mode: str
    target_type: str
    target_value: str
    question: str
    risk_profile: str
    preferred_language: str
    selected_skill_profile: str


class JobEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    event: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class Artifact(BaseModel):
    kind: str
    path: str


class ReportSummary(BaseModel):
    title: str
    summary: str
    rating: str
    confidence: float


class AnalysisResult(BaseModel):
    run_id: str
    status: JobStatus
    events: list[JobEvent]
    artifacts: list[Artifact]
    report_summary: ReportSummary
    raw_markdown_path: str | None = None
    raw_json_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
