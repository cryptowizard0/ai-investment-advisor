"""FastAPI application for browsing local investment reports."""

from __future__ import annotations

import json
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from queue import Empty
from typing import AsyncIterator, Iterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileSystemMovedEvent,
)
from watchdog.observers.polling import PollingObserver

from web.backend.report_catalog import (
    ReportCatalog,
    ReportEvents,
    ReportItem,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"
DEFAULT_FRONTEND_DIST = REPO_ROOT / "web" / "frontend" / "dist"


class ReportWatchHandler(FileSystemEventHandler):
    def __init__(self, catalog: ReportCatalog) -> None:
        self.catalog = catalog

    @staticmethod
    def _path(value: str | bytes) -> Path:
        return Path(value.decode() if isinstance(value, bytes) else value)

    def _rebuild(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.catalog.rebuild_path(self._path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        self._rebuild(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._rebuild(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._rebuild(event)

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        self._rebuild(event)
        if not event.is_directory:
            self.catalog.rebuild_path(self._path(event.dest_path))


def create_app(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    frontend_dist: Path = DEFAULT_FRONTEND_DIST,
) -> FastAPI:
    resolved_output_dir = output_dir.resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    report_events = ReportEvents()
    report_catalog = ReportCatalog(resolved_output_dir, report_events)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        observer = PollingObserver(timeout=0.2)
        observer.schedule(
            ReportWatchHandler(report_catalog),
            str(resolved_output_dir),
            recursive=True,
        )
        observer.start()
        try:
            report_catalog.load()
            yield
        finally:
            observer.stop()
            observer.join()
            report_catalog.close()

    app = FastAPI(
        title="AI Investment Advisor Report Reader",
        lifespan=lifespan,
    )
    app.state.report_catalog = report_catalog
    app.state.report_events = report_events

    def filter_reports(
        items: list[ReportItem],
        category: list[str] | None = None,
        skill: list[str] | None = None,
        ticker: list[str] | None = None,
        theme: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ReportItem]:
        if category:
            items = [report for report in items if report["category"] in category]
        if skill:
            items = [report for report in items if report["skill"] in skill]
        if ticker:
            items = [
                report
                for report in items
                if any(value in report["tickers"] for value in ticker)
            ]
        if theme:
            items = [
                report
                for report in items
                if any(value in report["themes"] for value in theme)
            ]
        if date_from or date_to:
            items = [report for report in items if report["date"]]
        if date_from:
            items = [report for report in items if report["date"] >= date_from]
        if date_to:
            items = [report for report in items if report["date"] <= date_to]
        return items

    @app.get("/api/reports")
    def list_reports(
        category: list[str] | None = Query(default=None),
        skill: list[str] | None = Query(default=None),
        ticker: list[str] | None = Query(default=None),
        theme: list[str] | None = Query(default=None),
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ReportItem]:
        return filter_reports(
            report_catalog.reports(),
            category,
            skill,
            ticker,
            theme,
            date_from,
            date_to,
        )

    @app.get("/api/facets")
    def list_facets() -> dict[str, object]:
        items = report_catalog.reports()
        skill_counts = Counter(report["skill"] for report in items)
        category_counts = Counter(report["category"] for report in items)
        ticker_counts = Counter(
            ticker
            for report in items
            for ticker in report["tickers"]
        )
        theme_counts = Counter(
            theme
            for report in items
            for theme in report["themes"]
        )
        dates = [report["date"] for report in items if report["date"]]
        return {
            "skills": [
                {"value": value, "count": skill_counts[value]}
                for value in sorted(skill_counts)
            ],
            "categories": [
                {"value": value, "count": category_counts[value]}
                for value in sorted(category_counts)
            ],
            "tickers": [
                {"value": value, "count": ticker_counts[value]}
                for value in sorted(ticker_counts)
            ],
            "themes": [
                {"value": value, "count": theme_counts[value]}
                for value in sorted(theme_counts)
            ],
            "dateRange": {
                "min": min(dates, default=""),
                "max": max(dates, default=""),
            },
        }

    @app.get("/api/search")
    def search_reports(
        q: str,
        category: list[str] | None = Query(default=None),
        skill: list[str] | None = Query(default=None),
        ticker: list[str] | None = Query(default=None),
        theme: list[str] | None = Query(default=None),
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ReportItem]:
        items = report_catalog.reports()
        normalized_query = q.strip().upper()
        if len(normalized_query) < 3:
            ticker_matches = [
                {**report, "snippet": ""}
                for report in items
                if normalized_query in report["tickers"]
            ]
            return filter_reports(
                ticker_matches,
                category,
                skill,
                ticker,
                theme,
                date_from,
                date_to,
            )

        items_by_id = {report["id"]: report for report in items}
        matches = report_catalog.search(q.strip())
        search_items = [
            {**items_by_id[requested_id], "snippet": snippet}
            for requested_id, snippet in matches
            if requested_id in items_by_id
        ]
        return filter_reports(
            search_items,
            category,
            skill,
            ticker,
            theme,
            date_from,
            date_to,
        )

    @app.get("/api/unresolved")
    def list_unresolved() -> dict[str, list[ReportItem]]:
        items = report_catalog.reports()
        return {
            "tickers": [report for report in items if not report["tickers"]],
            "themes": [report for report in items if not report["themes"]],
        }

    @app.get("/api/reports/{requested_id}/raw", response_class=PlainTextResponse)
    def read_report(requested_id: str) -> str:
        path = report_catalog.path_for_id(requested_id)
        if path is None or not path.is_file():
            raise HTTPException(status_code=404, detail="Report not found")

        return path.read_text(encoding="utf-8")

    @app.get("/api/events")
    def stream_report_events() -> StreamingResponse:
        def event_stream() -> Iterator[str]:
            subscriber = report_events.subscribe()
            try:
                yield "retry: 1000\n\n"
                while True:
                    try:
                        event = subscriber.get(timeout=1)
                    except Empty:
                        yield ": keep-alive\n\n"
                        continue
                    if event is None:
                        return
                    yield (
                        "data: "
                        + json.dumps(event, ensure_ascii=False)
                        + "\n\n"
                    )
            finally:
                report_events.unsubscribe(subscriber)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    if frontend_dist.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=frontend_dist, html=True),
            name="frontend",
        )

    return app


app = create_app()
