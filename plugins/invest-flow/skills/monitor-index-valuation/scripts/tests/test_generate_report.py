"""Tests for the index PE sensitivity report generator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "generate_report.py"

ANCHORS = [
    (36.31, 0.0),
    (43.26, 20.0),
    (83.91, 50.0),
    (159.29, 80.0),
    (232.51, 98.07),
    (263.72, 100.0),
]


def load_generator_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"Generator script is missing: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("index_pe_generate_report", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load generator script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEMPLATE = "\n".join(
    [
        "# {{指数名}}({{代码}})指数估值敏感性分析",
        "数据源:{{数据源}}",
        "指标:{{指标}}",
        "日期:{{分析日期}}",
        "当前值:{{基准值}}",
        "当前分位:{{当前分位}}",
        "方法:{{分位方法}}",
        "## 敏感性表",
        "{{敏感性表格}}",
    ]
)


class ComputationTests(unittest.TestCase):
    def test_parse_moves_includes_zero_sorted_desc(self) -> None:
        generator = load_generator_module()
        self.assertEqual(
            generator.parse_moves("0.10,0.05,-0.05,-0.10"),
            [0.1, 0.05, 0.0, -0.05, -0.1],
        )

    def test_interp_percentile_between_anchors(self) -> None:
        generator = load_generator_module()
        # 209.26 sits between the 80% (159.29) and 98.07% (232.51) anchors.
        self.assertAlmostEqual(generator.interp_percentile(209.26, ANCHORS), 92.33, places=1)
        # Clamps outside the anchor range.
        self.assertEqual(generator.interp_percentile(10.0, ANCHORS), 0.0)
        self.assertEqual(generator.interp_percentile(999.0, ANCHORS), 100.0)

    def test_empirical_percentile_weak_rank(self) -> None:
        generator = load_generator_module()
        self.assertEqual(generator.empirical_percentile(25.0, [10, 20, 30, 40]), 50.0)
        self.assertEqual(generator.empirical_percentile(40.0, [10, 20, 30, 40]), 100.0)


class CreateReportTests(unittest.TestCase):
    def test_writes_table_and_numbers_duplicate_paths(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            template_path = output_dir / "template.md"
            template_path.write_text(TEMPLATE, encoding="utf-8")

            kwargs = dict(
                index_name="科创50",
                code="000688",
                source="理杏仁·整体法",
                metric="TTM P/E",
                window="5年",
                base=232.51,
                moves=generator.parse_moves("0.10,0.05,-0.05,-0.10"),
                report_date=date(2026, 7, 15),
                output_dir=output_dir,
                template_path=template_path,
                anchors=ANCHORS,
                current_pct=98.07,
            )

            first_path = generator.create_report(**kwargs)
            second_path = generator.create_report(**kwargs)

            self.assertEqual(first_path.name, "monitor-index-valuation-000688-2026-07-15.md")
            self.assertEqual(second_path.name, "monitor-index-valuation-000688-2026-07-15(1).md")

            text = first_path.read_text(encoding="utf-8")
            self.assertIn("科创50(000688)指数估值敏感性分析", text)
            self.assertIn("当前分位:98.1%", text)
            # Current row is bolded with the base multiple.
            self.assertIn("**232.5**", text)
            # +10% row: 232.51 * 1.10 = 255.8 -> ~99.5 percentile.
            self.assertIn("255.8", text)
            self.assertIn("99.5%", text)
            # -10% row: 232.51 * 0.90 = 209.3 -> ~92.3 percentile, delta vs current.
            self.assertIn("209.3", text)
            self.assertIn("92.3%", text)
            self.assertIn("-5.7pt", text)

    def test_percentile_placeholder_without_source(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            template_path = output_dir / "template.md"
            template_path.write_text(TEMPLATE, encoding="utf-8")

            path = generator.create_report(
                index_name="纳斯达克100",
                code="NDX",
                source="Choice",
                metric="TTM P/E",
                window="5年",
                base=37.0,
                moves=generator.parse_moves("0.05,-0.05"),
                report_date=date(2026, 7, 14),
                output_dir=output_dir,
                template_path=template_path,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("monitor-index-valuation-NDX-2026-07-14.md", path.name)
            self.assertIn("待填写", text)

    def test_validates_inputs(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            template_path = output_dir / "template.md"
            template_path.write_text(TEMPLATE, encoding="utf-8")

            with self.assertRaises(ValueError):
                generator.create_report(
                    index_name="",
                    code="000688",
                    source="s",
                    metric="TTM P/E",
                    window="5年",
                    base=232.51,
                    moves=[0.0],
                    report_date=date(2026, 7, 15),
                    output_dir=output_dir,
                    template_path=template_path,
                    anchors=ANCHORS,
                )

            with self.assertRaises(ValueError):
                generator.create_report(
                    index_name="科创50",
                    code="000688",
                    source="s",
                    metric="TTM P/E",
                    window="5年",
                    base=0.0,
                    moves=[0.0],
                    report_date=date(2026, 7, 15),
                    output_dir=output_dir,
                    template_path=template_path,
                    anchors=ANCHORS,
                )


if __name__ == "__main__":
    unittest.main()
