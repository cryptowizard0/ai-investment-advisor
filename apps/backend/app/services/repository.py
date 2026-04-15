from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterable, Protocol, TypeVar

from pydantic import BaseModel

from app.models.schemas import AnalysisJobRecord, JobEvent, ReportRecord, ThreadSummary, utc_now


class Repository(Protocol):
    def create_thread(self, thread: ThreadSummary) -> ThreadSummary: ...
    def get_thread(self, thread_id: str) -> ThreadSummary | None: ...
    def list_threads(self) -> list[ThreadSummary]: ...
    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord: ...
    def update_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord: ...
    def get_job(self, job_id: str) -> AnalysisJobRecord | None: ...
    def append_events(self, job_id: str, new_events: Iterable[JobEvent]) -> list[JobEvent]: ...
    def get_events(self, job_id: str) -> list[JobEvent]: ...
    def create_report(self, report: ReportRecord) -> ReportRecord: ...
    def get_report(self, report_id: str) -> ReportRecord | None: ...
    def list_reports(self) -> list[ReportRecord]: ...


ModelT = TypeVar("ModelT", bound=BaseModel)


class SqliteRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._lock, self.connection:
            self.connection.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_job_created
                ON events(job_id, created_at);

                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_reports_created
                ON reports(created_at);
                """
            )

    def create_thread(self, thread: ThreadSummary) -> ThreadSummary:
        with self._lock, self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO threads (id, created_at, payload)
                VALUES (?, ?, ?)
                """,
                (thread.id, thread.created_at.isoformat(), thread.model_dump_json()),
            )
        return thread

    def get_thread(self, thread_id: str) -> ThreadSummary | None:
        row = self._fetchone("SELECT payload FROM threads WHERE id = ?", (thread_id,))
        return self._deserialize(ThreadSummary, row["payload"]) if row else None

    def list_threads(self) -> list[ThreadSummary]:
        rows = self._fetchall("SELECT payload FROM threads ORDER BY created_at DESC", ())
        return [self._deserialize(ThreadSummary, row["payload"]) for row in rows]

    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        with self._lock, self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO jobs (id, thread_id, status, created_at, updated_at, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.thread_id,
                    job.status,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                ),
            )
        return job

    def update_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        job.updated_at = utc_now()
        with self._lock, self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO jobs (id, thread_id, status, created_at, updated_at, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.thread_id,
                    job.status,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                ),
            )
        return job

    def get_job(self, job_id: str) -> AnalysisJobRecord | None:
        row = self._fetchone("SELECT payload FROM jobs WHERE id = ?", (job_id,))
        return self._deserialize(AnalysisJobRecord, row["payload"]) if row else None

    def append_events(self, job_id: str, new_events: Iterable[JobEvent]) -> list[JobEvent]:
        events = list(new_events)
        if not events:
            return self.get_events(job_id)

        with self._lock, self.connection:
            self.connection.executemany(
                """
                INSERT OR REPLACE INTO events (id, job_id, created_at, payload)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (event.id, job_id, event.created_at.isoformat(), event.model_dump_json())
                    for event in events
                ],
            )
        return self.get_events(job_id)

    def get_events(self, job_id: str) -> list[JobEvent]:
        rows = self._fetchall(
            "SELECT payload FROM events WHERE job_id = ? ORDER BY created_at ASC",
            (job_id,),
        )
        return [self._deserialize(JobEvent, row["payload"]) for row in rows]

    def create_report(self, report: ReportRecord) -> ReportRecord:
        with self._lock, self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO reports (id, job_id, thread_id, created_at, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report.id,
                    report.job_id,
                    report.thread_id,
                    report.created_at.isoformat(),
                    report.model_dump_json(),
                ),
            )
        return report

    def get_report(self, report_id: str) -> ReportRecord | None:
        row = self._fetchone("SELECT payload FROM reports WHERE id = ?", (report_id,))
        return self._deserialize(ReportRecord, row["payload"]) if row else None

    def list_reports(self) -> list[ReportRecord]:
        rows = self._fetchall("SELECT payload FROM reports ORDER BY created_at DESC", ())
        return [self._deserialize(ReportRecord, row["payload"]) for row in rows]

    def _fetchone(self, query: str, params: tuple[object, ...]) -> sqlite3.Row | None:
        with self._lock:
            cursor = self.connection.execute(query, params)
            return cursor.fetchone()

    def _fetchall(self, query: str, params: tuple[object, ...]) -> list[sqlite3.Row]:
        with self._lock:
            cursor = self.connection.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def _deserialize(model: type[ModelT], payload: str) -> ModelT:
        return model.model_validate_json(payload)
