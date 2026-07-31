"""FastAPI application for browsing local investment reports."""

from __future__ import annotations

import base64
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from web.backend.report_index import collect_report_metadata, duplicate_identity


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"
DEFAULT_FRONTEND_DIST = REPO_ROOT / "web" / "frontend" / "dist"


def report_id(relative_path: str) -> str:
    encoded = base64.urlsafe_b64encode(relative_path.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def create_app(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    frontend_dist: Path = DEFAULT_FRONTEND_DIST,
) -> FastAPI:
    app = FastAPI(title="AI Investment Advisor Report Reader")
    resolved_output_dir = output_dir.resolve()

    def reports() -> list[dict[str, str | bool]]:
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
                    "dupeGroup": group,
                    "isLatestInGroup": version == latest_versions[group],
                }
            )
        return sorted(
            items,
            key=lambda report: (report["date"], report["title"], report["id"]),
            reverse=True,
        )

    @app.get("/api/reports")
    def list_reports(
        category: list[str] | None = Query(default=None),
        skill: list[str] | None = Query(default=None),
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, str | bool]]:
        items = reports()
        if category:
            items = [report for report in items if report["category"] in category]
        if skill:
            items = [report for report in items if report["skill"] in skill]
        if date_from or date_to:
            items = [report for report in items if report["date"]]
        if date_from:
            items = [report for report in items if report["date"] >= date_from]
        if date_to:
            items = [report for report in items if report["date"] <= date_to]
        return items

    @app.get("/api/facets")
    def list_facets() -> dict[str, object]:
        items = reports()
        skill_counts = Counter(report["skill"] for report in items)
        category_counts = Counter(report["category"] for report in items)
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
            "dateRange": {
                "min": min(dates, default=""),
                "max": max(dates, default=""),
            },
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
