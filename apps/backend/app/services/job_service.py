from __future__ import annotations

from fastapi import HTTPException

from app.models.schemas import (
    AnalysisJobRecord,
    AnalysisJobRequest,
    JobEvent,
    MessageCreateRequest,
    ReportRecord,
)
from app.services.agent_gateway import AgentGateway
from app.services.repository import Repository


class JobService:
    def __init__(self, repository: Repository, gateway: AgentGateway) -> None:
        self.repository = repository
        self.gateway = gateway

    def queue_analysis_job(self, thread_id: str, message: MessageCreateRequest) -> AnalysisJobRecord:
        thread = self.repository.get_thread(thread_id)
        if thread is None:
            raise HTTPException(status_code=404, detail="Thread not found")

        request = AnalysisJobRequest(
            user_id=message.user_id,
            thread_id=thread_id,
            analysis_mode=message.analysis_mode,
            target_type=message.target_type,
            target_value=message.target_value,
            question=message.question,
            risk_profile=message.risk_profile,
            preferred_language=message.preferred_language,
            selected_skill_profile=message.selected_skill_profile,
        )
        record = AnalysisJobRecord(thread_id=thread_id, user_id=message.user_id, request=request)
        self.repository.create_job(record)
        self.repository.append_events(
            record.id,
            [JobEvent(event="job.created", message=f"Job {record.id} created for {message.target_value}")],
        )
        self.repository.update_job(record)
        return record

    async def run_analysis_job(self, job_id: str) -> AnalysisJobRecord:
        record = self.get_job(job_id)
        record.status = "running"
        self.repository.append_events(
            record.id,
            [JobEvent(event="job.started", message=f"Running analysis for {record.request.target_value}")],
        )
        self.repository.update_job(record)

        try:
            result = await self.gateway.run_analysis(record.request)
            record.status = result.status
            record.result = result
            self.repository.append_events(record.id, result.events)
            self.repository.update_job(record)

            if result.raw_markdown_path:
                summary = result.report_summary
                report = ReportRecord(
                    thread_id=record.thread_id,
                    job_id=record.id,
                    user_id=record.user_id,
                    title=summary.title,
                    target_value=record.request.target_value,
                    analysis_mode=record.request.analysis_mode,
                    summary=summary.summary,
                    rating=summary.rating,
                    markdown=_load_markdown(result.raw_markdown_path),
                )
                self.repository.create_report(report)
        except Exception as exc:
            record.status = "failed"
            self.repository.append_events(
                record.id,
                [JobEvent(event="run.failed", message=f"Analysis failed: {exc}")],
            )
            self.repository.update_job(record)

        return record

    def get_job(self, job_id: str) -> AnalysisJobRecord:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    async def cancel_job(self, job_id: str) -> dict:
        job = self.get_job(job_id)
        result = await self.gateway.cancel(job.request.run_id)
        job.status = "canceled"
        self.repository.append_events(
            job.id,
            [JobEvent(event="job.canceled", message=f"Job {job.id} canceled")],
        )
        self.repository.update_job(job)
        return result

    async def get_artifacts(self, job_id: str) -> list[dict]:
        job = self.get_job(job_id)
        return await self.gateway.get_artifacts(job.request.run_id)

    def get_report_for_job(self, job_id: str) -> ReportRecord | None:
        for report in self.repository.list_reports():
            if report.job_id == job_id:
                return report
        return None


def _load_markdown(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return "# Report unavailable\n\nThe markdown artifact could not be loaded."
