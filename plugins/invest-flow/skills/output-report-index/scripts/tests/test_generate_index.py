"""Tests for the output report index generator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "generate_index.py"


def load_generator_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"Generator script is missing: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("generate_index", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load generator script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateIndexTests(unittest.TestCase):
    def test_legacy_category_names_are_mapped_to_canonical_sections(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            legacy_monitor_dir = output_dir / "daily-us-market-scan"
            legacy_research_dir = output_dir / "fundamental-analysis"
            legacy_chain_dir = output_dir / "chain-alpha-mismatch-discovery"
            legacy_ai_infra_dir = output_dir / "ai-infrastructure-sector-discovery"
            legacy_monitor_dir.mkdir()
            legacy_research_dir.mkdir()
            legacy_chain_dir.mkdir()
            legacy_ai_infra_dir.mkdir()

            legacy_monitor_report = legacy_monitor_dir / "us-market-close-daily-2026-01-11.md"
            legacy_monitor_report.write_text(
                "# Legacy monitor report\n\nHistory should remain searchable.",
                encoding="utf-8",
            )
            legacy_research_report = legacy_research_dir / "fundamental-analysis-TSLA-2026-01-12.md"
            legacy_research_report.write_text(
                "# Legacy research report\n\nHistory should remain searchable.",
                encoding="utf-8",
            )
            legacy_chain_report = legacy_chain_dir / "chain-alpha-mismatch-discovery-MLCC-2026-01-13.md"
            legacy_chain_report.write_text(
                "# Legacy chain report\n\nHistory should remain searchable.",
                encoding="utf-8",
            )
            legacy_ai_infra_report = legacy_ai_infra_dir / "ai-infrastructure-sector-discovery-2026-01-14.md"
            legacy_ai_infra_report.write_text(
                "# Legacy AI infrastructure report\n\nHistory should remain searchable.",
                encoding="utf-8",
            )

            result_path = generator.generate_index(output_dir=output_dir)
            index_text = result_path.read_text(encoding="utf-8")
            html_path = output_dir / "index.html"
            html_text = html_path.read_text(encoding="utf-8")

            self.assertIn("## monitor-us-market", index_text)
            self.assertIn("## research-fundamentals", index_text)
            self.assertIn("## chain-alpha-mismatch", index_text)
            self.assertIn("## monitor-ai-infrastructure", index_text)
            self.assertIn(
                "| 2026-01-11 | Legacy monitor report | [原文](./daily-us-market-scan/us-market-close-daily-2026-01-11.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-12 | Legacy research report | [原文](./fundamental-analysis/fundamental-analysis-TSLA-2026-01-12.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-13 | Legacy chain report | [原文](./chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-MLCC-2026-01-13.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-14 | Legacy AI infrastructure report | [原文](./ai-infrastructure-sector-discovery/ai-infrastructure-sector-discovery-2026-01-14.md) |",
                index_text,
            )
            self.assertIn('"category": "monitor-us-market"', html_text)
            self.assertIn('"category": "research-fundamentals"', html_text)
            self.assertIn('"category": "chain-alpha-mismatch"', html_text)
            self.assertIn('"category": "monitor-ai-infrastructure"', html_text)
            self.assertIn("\"daily-us-market-scan/us-market-close-daily-2026-01-11.md\"", html_text)
            self.assertIn("\"ai-infrastructure-sector-discovery/ai-infrastructure-sector-discovery-2026-01-14.md\"", html_text)
            self.assertEqual(
                generator.LEGACY_CATEGORY_ALIASES["daily-us-market-scan"],
                "monitor-us-market",
            )

            self.assertEqual(
                generator.LEGACY_CATEGORY_ALIASES["ai-infrastructure-sector-discovery"],
                "monitor-ai-infrastructure",
            )

            # Compatibility allowlist is explicit and centrally maintained in module constant.
            self.assertIn(
                "fundamental-analysis",
                generator.LEGACY_CATEGORY_ALIASES,
            )

    def test_writes_categorized_index_with_titles_links_and_ascending_dates(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            fundamental_dir = output_dir / "research-fundamentals"
            daily_dir = output_dir / "monitor-us-market"
            institutional_dir = output_dir / "research-institutional"
            fundamental_dir.mkdir()
            daily_dir.mkdir()
            institutional_dir.mkdir()

            old_report = fundamental_dir / "AAA-Old-2026-01-02.md"
            old_report.write_text(
                "# Old Fundamental Report\n\nPrivate old report body should not be embedded.",
                encoding="utf-8",
            )
            new_report = fundamental_dir / "BBB-New-2026-01-05.md"
            new_report.write_text(
                "# New Fundamental Report\n\nPrivate new report body should not be embedded.",
                encoding="utf-8",
            )
            untitled_report = daily_dir / "us market close 2026-01-03.md"
            untitled_report.write_text("No level one title\n", encoding="utf-8")
            compact_date_report = institutional_dir / "机构操作分析-20260104-测试(1).md"
            compact_date_report.write_text("# 机构测试报告\n", encoding="utf-8")
            no_date_report = daily_dir / "no-date-report.md"
            no_date_report.write_text("# No Date Report\n", encoding="utf-8")

            index_path = output_dir / "index.md"
            index_path.write_text("# Old manual index\n", encoding="utf-8")

            result_path = generator.generate_index(output_dir=output_dir)
            index_text = result_path.read_text(encoding="utf-8")
            index_bytes = result_path.read_bytes()
            html_path = output_dir / "index.html"
            html_text = html_path.read_text(encoding="utf-8")

            self.assertEqual(result_path, index_path)
            self.assertTrue(index_bytes.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(html_path.exists())
            self.assertIn("# Output 报告索引", index_text)
            self.assertIn("## monitor-us-market", index_text)
            self.assertIn("## research-fundamentals", index_text)
            self.assertIn("## research-institutional", index_text)
            self.assertIn("| 日期 | 标题 | 原文链接 |", index_text)
            self.assertIn(
                "| 2026-01-02 | Old Fundamental Report | [原文](./research-fundamentals/AAA-Old-2026-01-02.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-05 | New Fundamental Report | [原文](./research-fundamentals/BBB-New-2026-01-05.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-03 | us market close 2026-01-03 | [原文](./monitor-us-market/us%20market%20close%202026-01-03.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-04 | 机构测试报告 | [原文](./research-institutional/机构操作分析-20260104-测试(1).md) |",
                index_text,
            )
            self.assertNotIn("Old manual index", index_text)
            self.assertNotIn("[原文](./index.md)", index_text)

            no_date_position = index_text.index("|  | No Date Report |")
            dated_daily_position = index_text.index("| 2026-01-03 | us market close 2026-01-03 |")
            old_position = index_text.index("| 2026-01-02 | Old Fundamental Report |")
            new_position = index_text.index("| 2026-01-05 | New Fundamental Report |")
            self.assertLess(no_date_position, dated_daily_position)
            self.assertLess(old_position, new_position)

            self.assertIn("<title>Reports by AI Investment Advisor</title>", html_text)
            self.assertIn("<h1>Reports by AI Investment Advisor</h1>", html_text)
            self.assertIn('<div class="sidebar-header">', html_text)
            self.assertIn('<div class="sidebar-content">', html_text)
            self.assertIn('class="sidebar-toggle"', html_text)
            self.assertIn('id="sidebarToggle"', html_text)
            self.assertIn('aria-label="收起侧边栏"', html_text)
            self.assertNotIn("topbar-actions", html_text)
            self.assertLess(
                html_text.index('<aside class="sidebar"'),
                html_text.index('id="sidebarToggle"'),
            )
            self.assertIn(".app-shell.sidebar-collapsed", html_text)
            self.assertIn("toggleSidebar", html_text)
            self.assertIn("sidebarToggle.addEventListener", html_text)
            self.assertIn("grid-template-columns: minmax(280px, 380px) minmax(0, 1fr)", html_text)
            self.assertIn("grid-template-columns: 52px minmax(0, 1fr)", html_text)
            self.assertIn(".app-shell.sidebar-collapsed .sidebar-content", html_text)
            self.assertIn(".app-shell.sidebar-collapsed .reader", html_text)
            self.assertIn("height: 100vh", html_text)
            self.assertIn("overflow: hidden", html_text)
            self.assertIn(".reader {", html_text)
            self.assertIn("overflow: auto", html_text)
            self.assertIn('class="category-items"', html_text)
            self.assertIn("category-section.collapsed .category-items", html_text)
            self.assertIn('aria-expanded="true"', html_text)
            self.assertIn("toggleCategorySection", html_text)
            self.assertIn("报告总数", html_text)
            self.assertIn("分类总数", html_text)
            self.assertIn("最新日期", html_text)
            self.assertIn("最新报告", html_text)
            self.assertIn('<span class="metric-value">5</span>', html_text)
            self.assertIn('<span class="metric-value">3</span>', html_text)
            self.assertIn('<span class="metric-value">2026-01-05</span>', html_text)
            self.assertIn("New Fundamental Report", html_text)
            self.assertIn(
                '<a class="metric-value metric-link" href="#research-fundamentals/BBB-New-2026-01-05.md">New Fundamental Report</a>',
                html_text,
            )
            self.assertIn("const REPORTS =", html_text)
            self.assertIn("BBB-New-2026-01-05.md", html_text)
            self.assertIn("fetch(report.path)", html_text)
            self.assertIn("renderMarkdown(markdown)", html_text)
            self.assertIn("location.hash", html_text)
            self.assertIn("decodeURIComponent", html_text)
            self.assertIn("href=\"#research-fundamentals/BBB-New-2026-01-05.md\"", html_text)
            self.assertIn(
                "href=\"./research-fundamentals/BBB-New-2026-01-05.md\"",
                html_text,
            )
            self.assertIn("function renderMarkdown", html_text)
            self.assertIn("function renderTable", html_text)
            self.assertIn("function escapeHtml", html_text)
            self.assertNotIn("Private old report body should not be embedded.", html_text)
            self.assertNotIn("Private new report body should not be embedded.", html_text)

            generated_html_reports = [
                path
                for path in output_dir.rglob("*.html")
                if path.name != "index.html"
            ]
            self.assertEqual(generated_html_reports, [])


if __name__ == "__main__":
    unittest.main()
