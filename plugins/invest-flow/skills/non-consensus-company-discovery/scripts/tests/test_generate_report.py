"""Tests for the non-consensus company discovery report generator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "generate_report.py"


def load_generator_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"Generator script is missing: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("generate_report", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load generator script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateReportTests(unittest.TestCase):
    def test_writes_rendered_report_and_numbers_duplicate_paths(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            template_path = output_dir / "template.md"
            template_path.write_text(
                "\n".join(
                    [
                        "# {{主题}}非共识公司发现报告",
                        "作者：{{作者}}",
                        "分析日期：{{YYYY年MM月DD日}}",
                        "默认市场：{{市场}}",
                        "Top N：{{TopN}}",
                    ]
                ),
                encoding="utf-8",
            )

            first_path = generator.create_report(
                theme="AI 数据中心电力",
                market="US-listed equities/ADRs",
                top_n=3,
                report_date=date(2026, 5, 28),
                output_dir=output_dir,
                template_path=template_path,
            )
            second_path = generator.create_report(
                theme="AI 数据中心电力",
                market="US-listed equities/ADRs",
                top_n=3,
                report_date=date(2026, 5, 28),
                output_dir=output_dir,
                template_path=template_path,
            )

            self.assertEqual(
                first_path.name,
                "non-consensus-company-discovery-AI-数据中心电力-2026-05-28.md",
            )
            self.assertEqual(
                second_path.name,
                "non-consensus-company-discovery-AI-数据中心电力-2026-05-28(1).md",
            )
            first_text = first_path.read_text(encoding="utf-8")
            self.assertIn("作者：InvestmentFlow", first_text)
            self.assertIn("默认市场：US-listed equities/ADRs", first_text)


if __name__ == "__main__":
    unittest.main()
