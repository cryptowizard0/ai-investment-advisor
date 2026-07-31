"""HTTP contract tests for the local report reader backend."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from web.backend.app import create_app


class ReportApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"

        chain_dir = self.output_dir / "chain-alpha" / "archive"
        monitor_dir = self.output_dir / "monitor"
        research_dir = self.output_dir / "research"
        chain_dir.mkdir(parents=True)
        monitor_dir.mkdir(parents=True)
        research_dir.mkdir(parents=True)

        self.raw_markdown = (
            "# NVIDIA 验证报告\n\n"
            "市值为 $195B，目标价为 $4,000。<br>\n\n"
            "| 指标 | 结果 |\n"
            "| --- | --- |\n"
            "| `margin` | 通过 |\n"
        )
        (
            chain_dir
            / "chain-alpha-verification-NVDA-20260701-2026-07-30.md"
        ).write_text(self.raw_markdown, encoding="utf-8")
        (
            monitor_dir / "us-market-close-daily-20260729.md"
        ).write_text(
            "前言\n\n# 美股收盘扫描\n",
            encoding="utf-8",
        )
        (
            research_dir / "custom-note-no-date.md"
        ).write_text(
            "正文没有一级标题。\n",
            encoding="utf-8",
        )

        self.client = TestClient(create_app(output_dir=self.output_dir))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_lists_metadata_derived_from_report_files(self) -> None:
        response = self.client.get("/api/reports")

        self.assertEqual(200, response.status_code)
        reports = response.json()
        self.assertEqual(3, len(reports))
        self.assertTrue(
            all(
                set(report) == {"id", "category", "skill", "date", "title"}
                for report in reports
            )
        )

        by_title = {report["title"]: report for report in reports}
        self.assertEqual(
            {
                "category": "chain-alpha",
                "skill": "chain-alpha-verification",
                "date": "2026-07-30",
            },
            {
                key: by_title["NVIDIA 验证报告"][key]
                for key in ("category", "skill", "date")
            },
        )
        self.assertEqual(
            {
                "category": "monitor",
                "skill": "monitor-us-market",
                "date": "2026-07-29",
            },
            {
                key: by_title["美股收盘扫描"][key]
                for key in ("category", "skill", "date")
            },
        )
        self.assertEqual(
            {
                "category": "research",
                "skill": "历史/其他",
                "date": "",
                "title": "custom-note-no-date",
            },
            {
                key: by_title["custom-note-no-date"][key]
                for key in ("category", "skill", "date", "title")
            },
        )

    def test_returns_the_original_markdown_for_a_report_id(self) -> None:
        reports = self.client.get("/api/reports").json()
        report = next(
            item for item in reports if item["title"] == "NVIDIA 验证报告"
        )

        response = self.client.get(f"/api/reports/{report['id']}/raw")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.headers["content-type"].startswith("text/plain"))
        self.assertEqual(self.raw_markdown, response.text)


if __name__ == "__main__":
    unittest.main()
