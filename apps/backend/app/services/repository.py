from __future__ import annotations

from typing import Iterable

from app.models.schemas import AnalysisJobRecord, JobEvent, ReportRecord, ThreadSummary, utc_now


class InMemoryRepository:
    def __init__(self) -> None:
        self.threads: dict[str, ThreadSummary] = {}
        self.jobs: dict[str, AnalysisJobRecord] = {}
        self.events: dict[str, list[JobEvent]] = {}
        self.reports: dict[str, ReportRecord] = {}

    def create_thread(self, thread: ThreadSummary) -> ThreadSummary:
        self.threads[thread.id] = thread
        return thread

    def get_thread(self, thread_id: str) -> ThreadSummary | None:
        return self.threads.get(thread_id)

    def list_threads(self) -> list[ThreadSummary]:
        return sorted(self.threads.values(), key=lambda item: item.created_at, reverse=True)

    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        self.jobs[job.id] = job
        self.events[job.id] = []
        return job

    def update_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        job.updated_at = utc_now()
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> AnalysisJobRecord | None:
        return self.jobs.get(job_id)

    def append_events(self, job_id: str, new_events: Iterable[JobEvent]) -> list[JobEvent]:
        items = self.events.setdefault(job_id, [])
        items.extend(new_events)
        return items

    def get_events(self, job_id: str) -> list[JobEvent]:
        return self.events.get(job_id, [])

    def create_report(self, report: ReportRecord) -> ReportRecord:
        self.reports[report.id] = report
        return report

    def get_report(self, report_id: str) -> ReportRecord | None:
        return self.reports.get(report_id)

    def list_reports(self) -> list[ReportRecord]:
        return sorted(self.reports.values(), key=lambda item: item.created_at, reverse=True)
