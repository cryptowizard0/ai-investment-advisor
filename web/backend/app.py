"""FastAPI application for browsing local investment reports."""

from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from web.backend.report_index import collect_report_metadata


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

    def reports() -> list[dict[str, str]]:
        metadata = collect_report_metadata(resolved_output_dir)
        items = [
            {
                "id": report_id(report["relative_path"]),
                "category": report["category"],
                "skill": report["skill"],
                "date": report["date"],
                "title": report["title"],
            }
            for report in metadata
        ]
        return sorted(
            items,
            key=lambda report: (report["date"], report["title"], report["id"]),
            reverse=True,
        )

    @app.get("/api/reports")
    def list_reports() -> list[dict[str, str]]:
        return reports()

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
