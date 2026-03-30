from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "completed", "failed", "canceled"]
AnalysisMode = Literal["deep_report", "quick_scan", "theme_research"]
TargetType = Literal["ticker", "theme", "question"]
RiskProfile = Literal["conservative", "balanced", "aggressive"]
Language = Literal["zh-CN", "en-US"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ThreadCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    user_id: str = Field(default="demo-user", min_length=1)


class ThreadSummary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str
    created_at: datetime = Field(default_factory=utc_now)


class MessageCreateRequest(BaseModel):
    question: str = Field(min_length=1)
    analysis_mode: AnalysisMode = "deep_report"
    target_type: TargetType = "ticker"
    target_value: str = Field(min_length=1)
    risk_profile: RiskProfile = "balanced"
    preferred_language: Language = "zh-CN"
    selected_skill_profile: str = "chief-investment-advisor"
    user_id: str = Field(default="demo-user", min_length=1)


class AnalysisJobRequest(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    thread_id: str
    analysis_mode: AnalysisMode
    target_type: TargetType
    target_value: str
    question: str
    risk_profile: RiskProfile
    preferred_language: Language
    selected_skill_profile: str


class JobEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    event: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class ReportSummary(BaseModel):
    title: str
    summary: str
    rating: str
    confidence: float = 0.0


class Artifact(BaseModel):
    kind: str
    path: str


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


class AnalysisJobRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    thread_id: str
    user_id: str
    request: AnalysisJobRequest
    status: JobStatus = "queued"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    result: AnalysisResult | None = None


class ReportRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    thread_id: str
    job_id: str
    user_id: str
    title: str
    target_value: str
    analysis_mode: AnalysisMode
    summary: str
    rating: str
    markdown: str
    created_at: datetime = Field(default_factory=utc_now)
