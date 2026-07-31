"""FastAPI application for browsing local investment reports."""

from __future__ import annotations

import base64
import sqlite3
from collections import Counter
from pathlib import Path
from typing import NotRequired, TypedDict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from web.backend.report_index import collect_report_metadata, duplicate_identity


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"
DEFAULT_FRONTEND_DIST = REPO_ROOT / "web" / "frontend" / "dist"


class ReportItem(TypedDict):
    id: str
    category: str
    skill: str
    date: str
    title: str
    tickers: list[str]
    themes: list[str]
    dupeGroup: str
    isLatestInGroup: bool
    snippet: NotRequired[str]


def report_id(relative_path: str) -> str:
    encoded = base64.urlsafe_b64encode(relative_path.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def create_app(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    frontend_dist: Path = DEFAULT_FRONTEND_DIST,
) -> FastAPI:
    app = FastAPI(title="AI Investment Advisor Report Reader")
    resolved_output_dir = output_dir.resolve()
    search_index = sqlite3.connect(":memory:", check_same_thread=False)
    search_index.execute(
        "CREATE VIRTUAL TABLE report_search "
        "USING fts5(report_id UNINDEXED, body, tokenize='trigram')"
    )
    search_index.executemany(
        "INSERT INTO report_search (report_id, body) VALUES (?, ?)",
        [
            (
                report_id(report["relative_path"]),
                (resolved_output_dir / report["relative_path"]).read_text(
                    encoding="utf-8"
                ),
            )
            for report in collect_report_metadata(resolved_output_dir)
        ],
    )

    def reports() -> list[ReportItem]:
        metadata = collect_report_metadata(resolved_output_dir)
        duplicate_details = [
            duplicate_identity(report["relative_path"]) for report in metadata
        ]
        latest_versions: dict[str, int] = {}
        for group, version in duplicate_details:
            latest_versions[group] = max(
                version,
                latest_versions.get(group, version),
            )
        items = []
        for report, (group, version) in zip(metadata, duplicate_details):
            items.append(
                {
                    "id": report_id(report["relative_path"]),
                    "category": report["category"],
                    "skill": report["skill"],
                    "date": report["date"],
                    "title": report["title"],
                    "tickers": report["tickers"],
                    "themes": report["themes"],
                    "dupeGroup": group,
                    "isLatestInGroup": version == latest_versions[group],
                }
            )
        return sorted(
            items,
            key=lambda report: (report["date"], report["title"], report["id"]),
            reverse=True,
        )

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
            reports(),
            category,
            skill,
            ticker,
            theme,
            date_from,
            date_to,
        )

    @app.get("/api/facets")
    def list_facets() -> dict[str, object]:
        items = reports()
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
        items = reports()
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
        literal_query = '"' + q.strip().replace('"', '""') + '"'
        matches = search_index.execute(
            "SELECT report_id, "
            "snippet(report_search, 1, '<mark>', '</mark>', '…', 24) "
            "FROM report_search "
            "WHERE report_search MATCH ? "
            "ORDER BY bm25(report_search), rowid",
            (literal_query,),
        ).fetchall()
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
        items = reports()
        return {
            "tickers": [report for report in items if not report["tickers"]],
            "themes": [report for report in items if not report["themes"]],
        }

    @app.get("/api/reports/{requested_id}/raw", response_class=PlainTextResponse)
    def read_report(requested_id: str) -> str:
        metadata_by_id = {
            report_id(report["relative_path"]): report
            for report in collect_report_metadata(resolved_output_dir)
        }
        report = metadata_by_id.get(requested_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")

        path = resolved_output_dir / report["relative_path"]
        return path.read_text(encoding="utf-8")

    if frontend_dist.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=frontend_dist, html=True),
            name="frontend",
        )

    return app


app = create_app()
