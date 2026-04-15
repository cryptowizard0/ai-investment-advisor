from __future__ import annotations

from fastapi import HTTPException

from app.models.schemas import ReportRecord
from app.services.repository import Repository


class ReportService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def get_report(self, report_id: str) -> ReportRecord:
        report = self.repository.get_report(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    def list_reports(self) -> list[ReportRecord]:
        return self.repository.list_reports()
