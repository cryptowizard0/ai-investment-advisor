"""Tests for the company buyability score report generator."""

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
                        "# {{公司名}}（{{Ticker}}）买入可行性评分报告",
                        "作者：{{作者}}",
                        "分析日期：{{YYYY年MM月DD日}}",
                        "交易所：{{交易所}}",
                        "币种：{{币种}}",
                        "## 评分表",
                        "## 风险与负面因素",
                    ]
                ),
                encoding="utf-8",
            )

            first_path = generator.create_report(
                ticker="BRK/B",
                company="Berkshire Hathaway",
                exchange="NYSE",
                currency="USD",
                report_date=date(2026, 6, 4),
                output_dir=output_dir,
                template_path=template_path,
            )
            second_path = generator.create_report(
                ticker="BRK/B",
                company="Berkshire Hathaway",
                exchange="NYSE",
                currency="USD",
                report_date=date(2026, 6, 4),
                output_dir=output_dir,
                template_path=template_path,
            )

            self.assertEqual(
                first_path.name,
                "company-buyability-score-BRK-B-2026-06-04.md",
            )
            self.assertEqual(
                second_path.name,
                "company-buyability-score-BRK-B-2026-06-04(1).md",
            )
            first_text = first_path.read_text(encoding="utf-8")
            self.assertIn("Berkshire Hathaway（BRK/B）买入可行性评分报告", first_text)
            self.assertIn("作者：InvestmentFlow", first_text)
            self.assertIn("分析日期：2026年06月04日", first_text)
            self.assertIn("交易所：NYSE", first_text)
            self.assertIn("币种：USD", first_text)
            self.assertIn("## 评分表", first_text)
            self.assertIn("## 风险与负面因素", first_text)

    def test_validates_ticker_and_required_fields(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            template_path = output_dir / "template.md"
            template_path.write_text("# {{Ticker}}\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="",
                    company="NVIDIA",
                    exchange="NASDAQ",
                    currency="USD",
                    report_date=date(2026, 6, 4),
                    output_dir=output_dir,
                    template_path=template_path,
                )

            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="bad ticker!",
                    company="NVIDIA",
                    exchange="NASDAQ",
                    currency="USD",
                    report_date=date(2026, 6, 4),
                    output_dir=output_dir,
                    template_path=template_path,
                )

            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="NVDA",
                    company="",
                    exchange="NASDAQ",
                    currency="USD",
                    report_date=date(2026, 6, 4),
                    output_dir=output_dir,
                    template_path=template_path,
                )


if __name__ == "__main__":
    unittest.main()
