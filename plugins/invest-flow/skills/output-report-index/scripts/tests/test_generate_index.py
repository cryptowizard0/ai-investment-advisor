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
    def test_writes_categorized_index_with_titles_links_and_ascending_dates(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            fundamental_dir = output_dir / "fundamental-analysis"
            daily_dir = output_dir / "daily-us-market-scan"
            institutional_dir = output_dir / "institutional-accumulation-analysis"
            fundamental_dir.mkdir()
            daily_dir.mkdir()
            institutional_dir.mkdir()

            old_report = fundamental_dir / "AAA-Old-2026-01-02.md"
            old_report.write_text("# Old Fundamental Report\n\nBody", encoding="utf-8")
            new_report = fundamental_dir / "BBB-New-2026-01-05.md"
            new_report.write_text("# New Fundamental Report\n\nBody", encoding="utf-8")
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

            self.assertEqual(result_path, index_path)
            self.assertIn("# Output 报告索引", index_text)
            self.assertIn("## daily-us-market-scan", index_text)
            self.assertIn("## fundamental-analysis", index_text)
            self.assertIn("## institutional-accumulation-analysis", index_text)
            self.assertIn("| 日期 | 标题 | 原文链接 |", index_text)
            self.assertIn(
                "| 2026-01-02 | Old Fundamental Report | [原文](./fundamental-analysis/AAA-Old-2026-01-02.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-05 | New Fundamental Report | [原文](./fundamental-analysis/BBB-New-2026-01-05.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-03 | us market close 2026-01-03 | [原文](./daily-us-market-scan/us%20market%20close%202026-01-03.md) |",
                index_text,
            )
            self.assertIn(
                "| 2026-01-04 | 机构测试报告 | [原文](./institutional-accumulation-analysis/机构操作分析-20260104-测试(1).md) |",
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


if __name__ == "__main__":
    unittest.main()
