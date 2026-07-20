"""Tests for the company valuation & risk report generator."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "generate_report.py"


def load_generator_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"Generator script is missing: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location(
        "company_valuation_risk_generate_report", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load generator script: {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass can resolve postponed annotations.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TEMPLATE = "\n".join(
    [
        "# {{公司名}} ({{TICKER}})",
        "市场:{{市场}}",
        "数据源:{{数据源}}",
        "窗口:{{窗口}}",
        "日期:{{分析日期}}",
        "方法:{{分位方法}}",
        "尺子:{{尺子标签}}",
        "## 结论",
        "{{结论块}}",
        "## 闸门",
        "{{类型闸门表}}",
        "## 尺子",
        "{{尺子选择表}}",
        "## 分位风险表",
        "{{分位风险表}}",
        "{{分位备注}}",
        "## 读数",
        "{{风险读数}}",
    ]
)

ANCHORS = [(8.5, 0.0), (12.3, 25.0), (16.8, 50.0), (24.5, 75.0), (41.2, 100.0)]


class PercentileMathTests(unittest.TestCase):
    def test_percentile_value_linear_interpolation(self) -> None:
        generator = load_generator_module()
        values = [40.0, 10.0, 30.0, 20.0]
        self.assertEqual(generator.percentile_value(values, 0), 10.0)
        self.assertEqual(generator.percentile_value(values, 100), 40.0)
        self.assertEqual(generator.percentile_value(values, 50), 25.0)
        self.assertEqual(generator.percentile_value(values, 25), 17.5)

    def test_percentile_rank_midrank(self) -> None:
        generator = load_generator_module()
        values = [10.0, 20.0, 30.0, 40.0]
        self.assertEqual(generator.percentile_rank(values, 25.0), 50.0)
        self.assertEqual(generator.percentile_rank(values, 20.0), 37.5)
        self.assertEqual(generator.percentile_rank(values, 5.0), 0.0)

    def test_anchor_interpolation_both_directions(self) -> None:
        generator = load_generator_module()
        # value -> pct
        self.assertAlmostEqual(generator.interp_pct_from_value(14.55, ANCHORS), 37.5)
        self.assertEqual(generator.interp_pct_from_value(5.0, ANCHORS), 0.0)
        # pct -> value (inverse)
        self.assertAlmostEqual(generator.interp_value_from_pct(37.5, ANCHORS), 14.55)
        self.assertAlmostEqual(generator.interp_value_from_pct(12.5, ANCHORS), 10.4)
        self.assertEqual(generator.interp_value_from_pct(100.0, ANCHORS), 41.2)


class DecideMetricTests(unittest.TestCase):
    def test_healthy_company_uses_pe(self) -> None:
        generator = load_generator_module()
        decision = generator.decide_metric(
            pe_median=30.0, current_pe=25.0, max_loss_streak=0, ref_pe=15.0
        )
        self.assertEqual(decision.metric, "pe")
        self.assertEqual(decision.unknowns, 0)
        self.assertEqual(decision.triggered_count, 0)

    def test_each_condition_triggers_ps(self) -> None:
        generator = load_generator_module()
        base = dict(pe_median=30.0, current_pe=25.0, max_loss_streak=0, ref_pe=15.0)
        for override in (
            {"pe_median": 150.0},
            {"current_pe": -5.0},
            {"max_loss_streak": 4},
            {"ref_pe": -2.0},
        ):
            decision = generator.decide_metric(**{**base, **override})
            self.assertEqual(decision.metric, "ps", msg=str(override))
            self.assertEqual(decision.triggered_count, 1, msg=str(override))

    def test_unknown_conditions_counted_but_pe_still_chosen(self) -> None:
        generator = load_generator_module()
        decision = generator.decide_metric(
            pe_median=None, current_pe=25.0, max_loss_streak=None, ref_pe=15.0
        )
        self.assertEqual(decision.metric, "pe")
        self.assertEqual(decision.unknowns, 2)
        self.assertIn("未触发 PS 条件", decision.reason)

    def test_all_unknown_raises(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            generator.decide_metric(
                pe_median=None, current_pe=None, max_loss_streak=None, ref_pe=None
            )

    def test_forced_metric_overrides(self) -> None:
        generator = load_generator_module()
        decision = generator.decide_metric(
            pe_median=30.0, current_pe=25.0, max_loss_streak=0, ref_pe=15.0, forced="ps"
        )
        self.assertEqual(decision.metric, "ps")
        self.assertTrue(decision.forced)
        self.assertIn("人工指定", decision.reason)


class CreateReportTests(unittest.TestCase):
    def _template(self, tmpdir: Path) -> Path:
        template_path = tmpdir / "template.md"
        template_path.write_text(TEMPLATE, encoding="utf-8")
        return template_path

    def test_series_mode_writes_band_and_numbers_duplicates(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            kwargs = dict(
                ticker="NVDA",
                company="NVIDIA",
                company_type="成长",
                type_basis="数据中心持续高增长",
                market="美股",
                source="macrotrends",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=100.0,
                current_price=200.0,
                max_loss_streak=0,
                ref_pe=35.4,
            )
            first_path = generator.create_report(**kwargs)
            second_path = generator.create_report(**kwargs)

            self.assertEqual(first_path.name, "company-valuation-risk-NVDA-2026-07-17.md")
            self.assertEqual(second_path.name, "company-valuation-risk-NVDA-2026-07-17(1).md")

            text = first_path.read_text(encoding="utf-8")
            # Current percentile: 90 below + 0.5*1 equal out of 100 -> 90.5%.
            self.assertIn("90.5%", text)
            self.assertIn("高估/透支区", text)
            # p50 of 10..109 = 59.5 -> -40.5% and implied price 200*59.5/100 = 119.00.
            self.assertIn("59.50", text)
            self.assertIn("-40.5%", text)
            self.assertIn("119.00", text)
            self.assertIn("使用 PE", text)
            self.assertIn("**当前 (90.5%)**", text)
            # Potential risk takes the worse leg: ref 35.4 vs current 100 -> -64.6%.
            self.assertIn("-64.6%", text)
            self.assertIn("参考点腿", text)
            # Alert line checked but not triggered (100.0 <= 100).
            self.assertIn("未触发。", text)
            self.assertIn("警戒线检查", text)

    def test_pe_series_drops_negative_observations_with_note(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="ACME",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[-5.0, -3.0, 20.0, 30.0, 40.0, 50.0],
                current_pe=45.0,
                max_loss_streak=0,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("已剔除非正观测 2 点", text)
            self.assertIn("非正观测占比超过 20%", text)

    def test_anchor_mode_uses_vendor_percentile(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="688017",
                company="绿的谐波",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                ps_anchors=ANCHORS,
                current_ps=28.6,
                current_price=98.5,
                current_percentile=82.0,
                metric="ps",
                pe_median=30.0,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("锚点分段线性插值", text)
            self.assertIn("82.0%", text)
            self.assertIn("TTM PS", text)
            self.assertIn("人工指定", text)

    def test_gate_fail_skips_analysis(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="MU",
                company="Micron",
                company_type="周期",
                type_basis="存储强周期",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("类型闸门：未通过 → 排除", text)
            self.assertIn("类型闸门未通过", text)
            self.assertIn("本节不适用", text)
            self.assertIn("替代框架", text)

    def test_ps_chosen_without_ps_data_raises(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="LOSS",
                    company_type="成长",
                    report_date=date(2026, 7, 17),
                    output_dir=output_dir,
                    template_path=self._template(output_dir),
                    current_pe=-10.0,
                )

    def test_forced_pe_with_negative_current_raises(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="LOSS",
                    company_type="成长",
                    report_date=date(2026, 7, 17),
                    output_dir=output_dir,
                    template_path=self._template(output_dir),
                    pe_series=[10.0, 20.0, 30.0],
                    current_pe=-5.0,
                    metric="pe",
                )

    def test_pe_alert_line_stops_before_percentiles(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="HYPE",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=120.0,
                pe_median=60.0,
                max_loss_streak=0,
                ref_pe=35.4,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("警戒线触发：当前 TTM PE 120.00 > 100 倍", text)
            self.assertIn("流程停止于第 2 步", text)
            self.assertIn("本节不适用", text)
            # No percentile band was computed.
            self.assertNotIn("50% 分位 |", text)

    def test_ps_alert_line_stops(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="MOON",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                ps_series=[10.0, 20.0, 30.0, 45.0],
                current_ps=45.0,
                metric="ps",
                pe_median=30.0,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("警戒线触发：当前 TTM PS 45.00 > 40 倍", text)

    def test_below_reference_point_highlighted(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="CHEAP",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=30.0,
                max_loss_streak=0,
                ref_pe=35.4,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("已低于重要参考点", text)
            # Both legs positive -> no valuation-only downside.
            self.assertIn("两腿均无下行", text)

    def test_missing_reference_leg_noted(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="NOREF",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=100.0,
                max_loss_streak=0,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("参考点腿未提供", text)
            self.assertIn("仅按 50% 分位腿计", text)
            # Median leg still reported as the potential risk.
            self.assertIn("-40.5%", text)

    def test_ps_ruler_uses_ref_ps_leg(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="LOSSY",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                ps_series=[4.0, 6.0, 8.0, 10.0, 12.0],
                current_ps=12.0,
                current_pe=-5.0,
                ref_ps=6.0,
                metric="auto",
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("使用 PS", text)
            # ref leg: 6/12 - 1 = -50% beats median leg 8/12 - 1 = -33.3%.
            self.assertIn("-50.0%", text)
            self.assertIn("参考点腿", text)

    def test_short_history_prominent_warning(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="IPO",
                company_type="成长",
                report_date=date(2026, 7, 17),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[20.0, 25.0, 30.0, 35.0, 40.0],
                current_pe=40.0,
                max_loss_streak=0,
                ref_pe=22.0,
                data_span_years=2.0,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("历史数据不足", text)
            self.assertIn("2.0 年", text)
            self.assertIn("降置信度", text)

    def test_invalid_company_type_raises(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="NVDA",
                    company_type="未知",
                    report_date=date(2026, 7, 17),
                    output_dir=output_dir,
                    template_path=self._template(output_dir),
                )


if __name__ == "__main__":
    unittest.main()
