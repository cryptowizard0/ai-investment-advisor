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

        self.app = create_app(output_dir=self.output_dir)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_lists_metadata_derived_from_report_files(self) -> None:
        response = self.client.get("/api/reports")

        self.assertEqual(200, response.status_code)
        reports = response.json()
        self.assertEqual(3, len(reports))
        self.assertTrue(
            all(
                set(report)
                == {
                    "id",
                    "category",
                    "skill",
                    "date",
                    "title",
                    "tickers",
                    "themes",
                    "dupeGroup",
                    "isLatestInGroup",
                }
                for report in reports
            )
        )
        self.assertEqual(3, len({report["dupeGroup"] for report in reports}))
        self.assertTrue(all(report["isLatestInGroup"] for report in reports))

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

    def test_groups_numbered_revisions_and_marks_the_highest_suffix_latest(
        self,
    ) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-TSLA-2026-07-10(1).md"
        ).write_text("# TSLA 旧版\n", encoding="utf-8")
        (
            research_dir / "research-reportify-TSLA-2026-07-10(2).md"
        ).write_text("# TSLA 新版\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={
                "category": ["research"],
                "skill": ["research-reportify"],
                "date_from": "2026-07-10",
                "date_to": "2026-07-10",
            },
        )

        self.assertEqual(200, response.status_code)
        revisions = {
            report["title"]: report
            for report in response.json()
            if report["title"] in {"TSLA 旧版", "TSLA 新版"}
        }
        self.assertEqual({"TSLA 旧版", "TSLA 新版"}, set(revisions))
        self.assertEqual(2, len(response.json()))
        self.assertEqual(
            revisions["TSLA 旧版"]["dupeGroup"],
            revisions["TSLA 新版"]["dupeGroup"],
        )
        self.assertFalse(revisions["TSLA 旧版"]["isLatestInGroup"])
        self.assertTrue(revisions["TSLA 新版"]["isLatestInGroup"])

    def test_lists_skill_category_counts_and_available_date_range(self) -> None:
        response = self.client.get("/api/facets")

        self.assertEqual(200, response.status_code)
        facets = response.json()
        self.assertEqual(
            {
                "chain-alpha-verification": 1,
                "monitor-us-market": 1,
                "历史/其他": 1,
            },
            {
                item["value"]: item["count"]
                for item in facets["skills"]
            },
        )
        self.assertEqual(
            {
                "chain-alpha": 1,
                "monitor": 1,
                "research": 1,
            },
            {
                item["value"]: item["count"]
                for item in facets["categories"]
            },
        )
        self.assertEqual(
            {"min": "2026-07-29", "max": "2026-07-30"},
            facets["dateRange"],
        )

    def test_filters_reports_by_combined_category_skill_and_date_range(
        self,
    ) -> None:
        chain_dir = self.output_dir / "chain-alpha" / "archive"
        monitor_dir = self.output_dir / "monitor"
        research_dir = self.output_dir / "research"
        (
            monitor_dir
            / "chain-alpha-verification-AMD-2026-07-30.md"
        ).write_text("# AMD 验证报告\n", encoding="utf-8")
        (
            research_dir
            / "chain-alpha-verification-AVGO-2026-07-30.md"
        ).write_text("# AVGO 验证报告\n", encoding="utf-8")
        (
            chain_dir
            / "chain-alpha-monopoly-CPO-2026-07-30.md"
        ).write_text("# CPO 垄断筛选\n", encoding="utf-8")
        (
            chain_dir
            / "chain-alpha-verification-MRVL-2026-07-31.md"
        ).write_text("# MRVL 验证报告\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={
                "category": ["chain-alpha", "monitor"],
                "skill": ["chain-alpha-verification"],
                "date_from": "2026-07-30",
                "date_to": "2026-07-30",
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"NVIDIA 验证报告", "AMD 验证报告"},
            {report["title"] for report in response.json()},
        )

    def test_stacks_ticker_and_theme_with_existing_filters(self) -> None:
        chain_dir = self.output_dir / "chain-alpha" / "archive"
        research_dir = self.output_dir / "research"
        samples = [
            (
                chain_dir
                / "chain-alpha-verification-MRVL-CPO-2026-07-31.md",
                "MRVL CPO 验证",
            ),
            (
                research_dir
                / "chain-alpha-verification-MRVL-CPO-2026-07-31.md",
                "研究目录中的 MRVL CPO",
            ),
            (
                chain_dir
                / "chain-alpha-verification-NVDA-CPO-2026-07-31.md",
                "NVDA CPO 验证",
            ),
            (
                chain_dir
                / "chain-alpha-verification-MRVL-MLCC-2026-07-31.md",
                "MRVL MLCC 验证",
            ),
        ]
        for path, title in samples:
            path.write_text(f"# {title}\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={
                "category": ["chain-alpha"],
                "skill": ["chain-alpha-verification"],
                "ticker": ["MRVL"],
                "theme": ["CPO"],
                "date_from": "2026-07-31",
                "date_to": "2026-07-31",
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"MRVL CPO 验证"},
            {report["title"] for report in response.json()},
        )

    def test_normalizes_ticker_aliases_and_prefers_explicit_h1_ticker(
        self,
    ) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir
            / "research-fundamentals-605376SH-2026-07-31.md"
        ).write_text("# 博迁新材基本面\n", encoding="utf-8")
        (
            research_dir
            / "research-reportify-605376.SH-2026-07-31.md"
        ).write_text("# 博迁新材报告\n", encoding="utf-8")
        (
            research_dir
            / "research-reportify-NVDA-2026-07-31.md"
        ).write_text("# 博迁新材（605376.SH）估值报告\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={"ticker": ["605376.SH"]},
        )

        self.assertEqual(200, response.status_code)
        reports = response.json()
        self.assertEqual(
            {
                "博迁新材基本面",
                "博迁新材报告",
                "博迁新材（605376.SH）估值报告",
            },
            {report["title"] for report in reports},
        )
        self.assertTrue(
            all(report["tickers"] == ["605376.SH"] for report in reports)
        )

    def test_h1_hyphenated_ticker_overrides_filename_ticker(self) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-NVDA-2026-07-31.md"
        ).write_text("# Berkshire Hathaway（BRK-B）报告\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={"ticker": ["BRK.B"]},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"Berkshire Hathaway（BRK-B）报告"},
            {report["title"] for report in response.json()},
        )
        self.assertEqual(["BRK.B"], response.json()[0]["tickers"])

    def test_unknown_h1_ticker_does_not_fallback_to_filename_ticker(
        self,
    ) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-NVDA-2026-07-31.md"
        ).write_text("# 未收录公司（XYZ）报告\n", encoding="utf-8")

        reports = self.client.get("/api/reports").json()
        report = next(
            item for item in reports if item["title"] == "未收录公司（XYZ）报告"
        )
        unresolved = self.client.get("/api/unresolved").json()

        self.assertEqual([], report["tickers"])
        self.assertIn(
            report["id"],
            {item["id"] for item in unresolved["tickers"]},
        )

    def test_non_ticker_h1_parenthetical_uses_filename_ticker(self) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-fundamentals-TER-2026-07-31.md"
        ).write_text("# Teradyne（Fundamental）报告\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={"ticker": ["TER"]},
        )

        self.assertEqual(200, response.status_code)
        self.assertIn(
            "Teradyne（Fundamental）报告",
            {report["title"] for report in response.json()},
        )

    def test_normalizes_exchange_suffix_ticker_variants(self) -> None:
        research_dir = self.output_dir / "research"
        samples = {
            "research-reportify-6981.T-2026-07-31.md": "村田一",
            "research-reportify-6981T-2026-07-30.md": "村田二",
            "research-reportify-009150.KS-2026-07-31.md": "三星电机一",
            "research-reportify-009150KS-2026-07-30.md": "三星电机二",
            "research-reportify-2327TW-2026-07-31.md": "国巨",
            "research-reportify-000660KS-2026-07-31.md": "SK 海力士",
        }
        for filename, title in samples.items():
            (research_dir / filename).write_text(
                f"# {title}\n",
                encoding="utf-8",
            )

        facets = self.client.get("/api/facets").json()

        self.assertEqual(
            {
                "000660.KS": 1,
                "009150.KS": 2,
                "2327.TW": 1,
                "6981.T": 2,
            },
            {
                item["value"]: item["count"]
                for item in facets["tickers"]
                if item["value"]
                in {"000660.KS", "009150.KS", "2327.TW", "6981.T"}
            },
        )

    def test_excludes_false_positive_filename_tokens_from_tickers(self) -> None:
        research_dir = self.output_dir / "research"
        false_positives = ["AI", "CPO", "HBM", "GRID", "TGV", "260731"]
        for token in false_positives:
            (research_dir / f"research-note-{token}-2026-07-31.md").write_text(
                f"# {token} 专题\n",
                encoding="utf-8",
            )

        reports = self.client.get("/api/reports").json()
        by_title = {report["title"]: report for report in reports}

        self.assertTrue(
            all(
                by_title[f"{token} 专题"]["tickers"] == []
                for token in false_positives
            )
        )

    def test_normalizes_theme_fragments_for_filtering_and_facet_counts(
        self,
    ) -> None:
        chain_dir = self.output_dir / "chain-alpha" / "archive"
        (
            chain_dir
            / "chain-alpha-pipeline-MLCC-产业链-2026-07-31.md"
        ).write_text("# MLCC 产业链报告\n", encoding="utf-8")
        (
            chain_dir
            / "chain-alpha-mismatch-MLCC产业-2026-07-31.md"
        ).write_text("# 被动元件供需错配\n", encoding="utf-8")
        (
            chain_dir
            / "chain-alpha-pipeline-具身智能行业-2026-07-31.md"
        ).write_text("# 具身智能行业报告\n", encoding="utf-8")

        response = self.client.get(
            "/api/reports",
            params={"theme": ["MLCC"]},
        )
        facets = self.client.get("/api/facets").json()

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"MLCC 产业链报告", "被动元件供需错配"},
            {report["title"] for report in response.json()},
        )
        self.assertTrue(
            all(report["themes"] == ["MLCC"] for report in response.json())
        )
        self.assertEqual(
            {"MLCC": 2, "具身智能": 1},
            {
                item["value"]: item["count"]
                for item in facets["themes"]
            },
        )

    def test_lists_reports_with_unresolved_tickers_or_themes(self) -> None:
        chain_dir = self.output_dir / "chain-alpha" / "archive"
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-UNKNOWN-2026-07-31.md"
        ).write_text("# 未收录公司报告\n", encoding="utf-8")
        (
            chain_dir / "chain-alpha-pipeline-MLCC-2026-07-31.md"
        ).write_text("# MLCC 产业链报告\n", encoding="utf-8")
        (
            research_dir / "research-reportify-NVDA-2026-07-31.md"
        ).write_text("# NVIDIA 公司报告\n", encoding="utf-8")

        response = self.client.get("/api/unresolved")

        self.assertEqual(200, response.status_code)
        unresolved = response.json()
        unresolved_tickers = {
            report["title"] for report in unresolved["tickers"]
        }
        unresolved_themes = {
            report["title"] for report in unresolved["themes"]
        }
        self.assertIn("未收录公司报告", unresolved_tickers)
        self.assertIn("未收录公司报告", unresolved_themes)
        self.assertIn("MLCC 产业链报告", unresolved_tickers)
        self.assertNotIn("MLCC 产业链报告", unresolved_themes)
        self.assertNotIn("NVIDIA 公司报告", unresolved_tickers)
        self.assertIn("NVIDIA 公司报告", unresolved_themes)

    def test_searches_chinese_body_substrings_with_highlighted_snippets(
        self,
    ) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-MRVL-2026-07-31.md"
        ).write_text(
            "# Marvell 深度报告\n\n"
            "公司正在扩展先进封装产能，以支持下一代互连产品。\n",
            encoding="utf-8",
        )
        client = TestClient(create_app(output_dir=self.output_dir))

        response = client.get("/api/search", params={"q": "先进封装"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["Marvell 深度报告"],
            [report["title"] for report in response.json()],
        )
        self.assertIn(
            "<mark>先进封装</mark>",
            response.json()[0]["snippet"],
        )

    def test_routes_two_letter_ticker_search_to_exact_ticker_match(
        self,
    ) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-MU-2026-07-31.md"
        ).write_text(
            "# Micron 报告\n\n存储周期正在改善。\n",
            encoding="utf-8",
        )
        client = TestClient(create_app(output_dir=self.output_dir))

        response = client.get("/api/search", params={"q": "mu"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["Micron 报告"],
            [report["title"] for report in response.json()],
        )

    def test_stacks_search_with_all_existing_report_filters(self) -> None:
        chain_dir = self.output_dir / "chain-alpha" / "archive"
        research_dir = self.output_dir / "research"
        samples = [
            (
                chain_dir
                / "chain-alpha-verification-MRVL-CPO-2026-07-31.md",
                "目标报告",
            ),
            (
                research_dir
                / "chain-alpha-verification-MRVL-CPO-2026-07-31.md",
                "错误分类",
            ),
            (
                chain_dir
                / "chain-alpha-verification-NVDA-CPO-2026-07-31.md",
                "错误标的",
            ),
            (
                chain_dir
                / "chain-alpha-verification-MRVL-MLCC-2026-07-31.md",
                "错误主题",
            ),
            (
                chain_dir
                / "chain-alpha-verification-MRVL-CPO-2026-07-30.md",
                "错误日期",
            ),
        ]
        for path, title in samples:
            path.write_text(
                f"# {title}\n\n交付验证线索已经出现。\n",
                encoding="utf-8",
            )
        client = TestClient(create_app(output_dir=self.output_dir))

        response = client.get(
            "/api/search",
            params={
                "q": "交付验证",
                "category": ["chain-alpha"],
                "skill": ["chain-alpha-verification"],
                "ticker": ["MRVL"],
                "theme": ["CPO"],
                "date_from": "2026-07-31",
                "date_to": "2026-07-31",
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["目标报告"],
            [report["title"] for report in response.json()],
        )

    def test_orders_search_results_by_bm25_relevance(self) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-AMD-2026-07-31.md"
        ).write_text(
            "# 高相关报告\n\n"
            "供需错配是主线。供需错配仍在扩大，供需错配将延续。\n",
            encoding="utf-8",
        )
        (
            research_dir / "research-reportify-NVDA-2026-07-31.md"
        ).write_text(
            "# 低相关报告\n\n"
            "供需错配出现一次，随后讨论其他大量无关信息与背景。\n",
            encoding="utf-8",
        )
        client = TestClient(create_app(output_dir=self.output_dir))

        response = client.get("/api/search", params={"q": "供需错配"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["高相关报告", "低相关报告"],
            [report["title"] for report in response.json()],
        )

    def test_treats_punctuation_in_search_query_as_literal_text(self) -> None:
        research_dir = self.output_dir / "research"
        (
            research_dir / "research-reportify-AMD-2026-07-31.md"
        ).write_text(
            "# AMD 估值报告\n\n当前 P/E 估值仍低于历史中枢。\n",
            encoding="utf-8",
        )
        client = TestClient(create_app(output_dir=self.output_dir))

        response = client.get("/api/search", params={"q": "P/E"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["AMD 估值报告"],
            [report["title"] for report in response.json()],
        )
        self.assertIn("<mark>P/E</mark>", response.json()[0]["snippet"])

    def test_returns_the_original_markdown_for_a_report_id(self) -> None:
        reports = self.client.get("/api/reports").json()
        report = next(
            item for item in reports if item["title"] == "NVIDIA 验证报告"
        )

        response = self.client.get(f"/api/reports/{report['id']}/raw")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.headers["content-type"].startswith("text/plain"))
        self.assertEqual(self.raw_markdown, response.text)

    def test_incremental_rebuild_syncs_reports_facets_search_and_events(
        self,
    ) -> None:
        self.client.get("/api/reports")
        initial_facets = self.client.get("/api/facets").json()
        initial_tickers = {
            item["value"]: item["count"] for item in initial_facets["tickers"]
        }
        initial_themes = {
            item["value"]: item["count"] for item in initial_facets["themes"]
        }
        report_path = (
            self.output_dir
            / "research"
            / "research-reportify-live-2026-07-31.md"
        )
        report_path.write_text(
            "# Marvell（MRVL）CPO 跟踪\n\n光互连需求持续增长。\n",
            encoding="utf-8",
        )
        events = self.app.state.report_events
        subscriber = events.subscribe()

        added = self.app.state.report_catalog.rebuild_path(report_path)

        self.assertEqual("added", added["type"])
        self.assertEqual("Marvell（MRVL）CPO 跟踪", added["report"]["title"])
        self.assertEqual(added, subscriber.get_nowait())
        reports = self.client.get("/api/reports").json()
        self.assertIn(added["report"]["id"], {report["id"] for report in reports})
        facets = self.client.get("/api/facets").json()
        self.assertEqual(
            initial_tickers.get("MRVL", 0) + 1,
            next(
                item["count"]
                for item in facets["tickers"]
                if item["value"] == "MRVL"
            ),
        )
        self.assertEqual(
            initial_themes.get("CPO", 0) + 1,
            next(
                item["count"]
                for item in facets["themes"]
                if item["value"] == "CPO"
            ),
        )
        self.assertEqual(
            ["Marvell（MRVL）CPO 跟踪"],
            [
                report["title"]
                for report in self.client.get(
                    "/api/search",
                    params={"q": "光互连需求"},
                ).json()
            ],
        )

        report_path.write_text(
            "# NVIDIA（NVDA）MLCC 跟踪\n\n被动元件供需正在改善。\n",
            encoding="utf-8",
        )
        updated = self.app.state.report_catalog.rebuild_path(report_path)

        self.assertEqual("updated", updated["type"])
        self.assertEqual(added["report"]["id"], updated["report"]["id"])
        reports = self.client.get("/api/reports").json()
        current = next(
            report
            for report in reports
            if report["id"] == updated["report"]["id"]
        )
        self.assertEqual("NVIDIA（NVDA）MLCC 跟踪", current["title"])
        facets = self.client.get("/api/facets").json()
        ticker_counts = {
            item["value"]: item["count"] for item in facets["tickers"]
        }
        theme_counts = {
            item["value"]: item["count"] for item in facets["themes"]
        }
        self.assertEqual(
            initial_tickers.get("MRVL", 0),
            ticker_counts.get("MRVL", 0),
        )
        self.assertEqual(
            initial_themes.get("CPO", 0),
            theme_counts.get("CPO", 0),
        )
        self.assertEqual(
            initial_tickers.get("NVDA", 0) + 1,
            ticker_counts["NVDA"],
        )
        self.assertEqual(
            initial_themes.get("MLCC", 0) + 1,
            theme_counts["MLCC"],
        )
        self.assertEqual(
            [],
            self.client.get(
                "/api/search",
                params={"q": "光互连需求"},
            ).json(),
        )
        self.assertEqual(
            ["NVIDIA（NVDA）MLCC 跟踪"],
            [
                report["title"]
                for report in self.client.get(
                    "/api/search",
                    params={"q": "被动元件供需"},
                ).json()
            ],
        )

        report_path.unlink()
        removed = self.app.state.report_catalog.rebuild_path(report_path)

        self.assertEqual("removed", removed["type"])
        self.assertEqual(updated["report"]["id"], removed["report"]["id"])
        self.assertNotIn(
            removed["report"]["id"],
            {
                report["id"]
                for report in self.client.get("/api/reports").json()
            },
        )
        facets = self.client.get("/api/facets").json()
        self.assertEqual(
            initial_tickers,
            {
                item["value"]: item["count"]
                for item in facets["tickers"]
            },
        )
        self.assertEqual(
            initial_themes,
            {
                item["value"]: item["count"]
                for item in facets["themes"]
            },
        )
        self.assertEqual(
            [],
            self.client.get(
                "/api/search",
                params={"q": "被动元件供需"},
            ).json(),
        )
        self.app.state.report_events.unsubscribe(subscriber)

    def test_incremental_rebuild_updates_duplicate_group_latest_marker(
        self,
    ) -> None:
        base_path = (
            self.output_dir
            / "research"
            / "research-reportify-TSLA-2026-07-31.md"
        )
        revision_path = base_path.with_name(
            "research-reportify-TSLA-2026-07-31(1).md"
        )
        base_path.write_text("# TSLA 初版\n", encoding="utf-8")
        self.client.get("/api/reports")

        revision_path.write_text("# TSLA 修订版\n", encoding="utf-8")
        self.app.state.report_catalog.rebuild_path(revision_path)

        reports = {
            report["title"]: report
            for report in self.client.get("/api/reports").json()
        }
        self.assertFalse(reports["TSLA 初版"]["isLatestInGroup"])
        self.assertTrue(reports["TSLA 修订版"]["isLatestInGroup"])
        self.assertEqual(
            reports["TSLA 初版"]["dupeGroup"],
            reports["TSLA 修订版"]["dupeGroup"],
        )

        revision_path.unlink()
        self.app.state.report_catalog.rebuild_path(revision_path)

        reports = {
            report["title"]: report
            for report in self.client.get("/api/reports").json()
        }
        self.assertTrue(reports["TSLA 初版"]["isLatestInGroup"])


if __name__ == "__main__":
    unittest.main()
