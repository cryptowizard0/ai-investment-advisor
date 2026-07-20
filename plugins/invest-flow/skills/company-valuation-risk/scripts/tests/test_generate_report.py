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
        "## 建仓计划",
        "{{建仓计划}}",
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


class PositionPlanTests(unittest.TestCase):
    def _plan(self, generator, **overrides):
        kwargs = dict(
            potential_risk=-40.0,
            fallback_drawdown=None,
            drawdown_budget=2.0,
            grade=None,
            elastic=False,
            alert_triggered=False,
            span_insufficient=False,
        )
        kwargs.update(overrides)
        return generator.compute_position_plan(**kwargs)

    @staticmethod
    def _row(plan, budget):
        for row in plan.rows:
            if abs(row.budget - budget) < 1e-9:
                return row
        raise AssertionError(f"No ladder row for budget {budget}")

    def test_ladder_covers_all_budgets(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator)
        self.assertEqual([r.budget for r in plan.rows], [2, 5, 10, 20, 30, 50, 70])

    def test_basic_formula_per_rung(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator)  # risk 40%
        self.assertAlmostEqual(self._row(plan, 2).final_cap, 5.0)
        self.assertAlmostEqual(self._row(plan, 10).final_cap, 25.0)
        self.assertAlmostEqual(self._row(plan, 50).final_cap, 125.0)
        self.assertAlmostEqual(plan.primary_final_cap, 5.0)

    def test_custom_primary_budget_merged_and_flagged(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, drawdown_budget=3.0)
        self.assertIn(3.0, [r.budget for r in plan.rows])
        self.assertAlmostEqual(self._row(plan, 3.0).final_cap, 7.5)
        self.assertAlmostEqual(plan.primary_final_cap, 7.5)

    def test_grade_elastic_and_span_discounts_stack(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, grade="通过", elastic=True, span_insufficient=True)
        self.assertAlmostEqual(plan.discount, 0.125)
        self.assertAlmostEqual(self._row(plan, 2).base_cap, 5.0)
        self.assertAlmostEqual(self._row(plan, 2).final_cap, 5.0 * 0.125)
        self.assertAlmostEqual(plan.primary_final_cap, 0.625)

    def test_blocked_grades_give_no_position(self) -> None:
        generator = load_generator_module()
        for grade in ("待验证", "剔除"):
            plan = self._plan(generator, grade=grade)
            self.assertEqual(plan.rows, [], msg=grade)
            self.assertIsNone(plan.primary_final_cap, msg=grade)
            self.assertIn("不给仓位", plan.blocked_reason)

    def test_alert_zeroes_but_keeps_ladder(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, grade="金池子", alert_triggered=True)
        self.assertTrue(plan.alert_zeroed)
        self.assertEqual(plan.primary_final_cap, 0.0)
        # ladder formula values are retained for reference.
        self.assertAlmostEqual(self._row(plan, 2).final_cap, 5.0)

    def test_alert_release_halves_instead_of_zeroing(self) -> None:
        generator = load_generator_module()
        plan = self._plan(
            generator, grade="金池子", alert_triggered=True, alert_released=True,
            alert_line=100.0, forward_value=90.0, alert_evidence="公司指引 + 在手订单/产能锁定",
        )
        self.assertFalse(plan.alert_zeroed)
        self.assertAlmostEqual(plan.alert_factor, 0.5)
        self.assertAlmostEqual(plan.signal_factor, 0.5)
        # base 5.0 (金池子 x1) x alert-release 0.5 = 2.5 deployable.
        self.assertAlmostEqual(plan.primary_final_cap, 2.5)

    def test_alert_release_without_trigger_is_noop(self) -> None:
        generator = load_generator_module()
        # No evidence/forward needed when the alert line is not triggered.
        plan = self._plan(generator, alert_triggered=False, alert_released=True)
        self.assertAlmostEqual(plan.alert_factor, 1.0)
        self.assertAlmostEqual(plan.primary_final_cap, 5.0)

    def test_alert_release_requires_evidence(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            self._plan(
                generator, alert_triggered=True, alert_released=True,
                alert_line=100.0, forward_value=90.0,  # evidence missing
            )

    def test_alert_release_requires_forward_multiple(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            self._plan(
                generator, alert_triggered=True, alert_released=True,
                alert_line=100.0, alert_evidence="公司指引",  # forward missing
            )

    def test_alert_release_rejected_when_forward_still_above_line(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            self._plan(
                generator, alert_triggered=True, alert_released=True,
                alert_line=100.0, forward_value=120.0, alert_evidence="公司指引",  # not inside
            )

    def test_digestion_overpriced_halves(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, digestion="透支")
        self.assertTrue(plan.digestion_overpriced)
        self.assertAlmostEqual(plan.digestion_factor, 0.5)
        self.assertAlmostEqual(plan.primary_final_cap, 2.5)

    def test_non_overpriced_digestion_no_change(self) -> None:
        generator = load_generator_module()
        for verdict in ("合理低估", "可消化", "部分消化"):
            plan = self._plan(generator, digestion=verdict)
            self.assertAlmostEqual(plan.digestion_factor, 1.0, msg=verdict)
            self.assertAlmostEqual(plan.primary_final_cap, 5.0, msg=verdict)

    def test_signal_factors_compound(self) -> None:
        generator = load_generator_module()
        plan = self._plan(
            generator, grade="通过", alert_triggered=True, alert_released=True, digestion="透支",
            alert_line=100.0, forward_value=90.0, alert_evidence="delivery-tracking L4 已点亮",
        )
        # discount 0.5 (通过) -> base 2.5; signal 0.5 (alert) x 0.5 (透支) = 0.25.
        self.assertAlmostEqual(plan.signal_factor, 0.25)
        self.assertAlmostEqual(plan.primary_final_cap, 2.5 * 0.25)

    def test_invalid_digestion_raises(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            self._plan(generator, digestion="未知判定")

    def test_fallback_used_when_risk_unavailable(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, potential_risk=None, fallback_drawdown=50.0)
        self.assertAlmostEqual(self._row(plan, 2).base_cap, 4.0)
        self.assertIn("兜底", plan.risk_source)

    def test_no_risk_and_no_fallback_blocks(self) -> None:
        generator = load_generator_module()
        plan = self._plan(generator, potential_risk=None)
        self.assertEqual(plan.rows, [])
        self.assertIsNone(plan.primary_final_cap)
        self.assertIn("--fallback-drawdown", plan.blocked_reason)

    def test_invalid_inputs_raise(self) -> None:
        generator = load_generator_module()
        with self.assertRaises(ValueError):
            self._plan(generator, drawdown_budget=0.0)
        with self.assertRaises(ValueError):
            self._plan(generator, grade="未知档")
        with self.assertRaises(ValueError):
            self._plan(generator, fallback_drawdown=-5.0)


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
            # Industry-and-company context note is mandatory and informational only.
            self.assertIn("特别提示（不影响公式计算与结论）", text)
            self.assertIn("行业×公司定性判断：待填写", text)
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
            # Context note also present on the gate-fail path (e.g. storage under industry fear).
            self.assertIn("特别提示（不影响公式计算与结论）", text)

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

    def test_pe_alert_line_warns_but_continues(self) -> None:
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
            # Prominent warning in both the conclusion and the alert check.
            self.assertIn("警戒线触发：当前 TTM PE 120.00 > 100 倍", text)
            self.assertIn("触发重点提示（不停止）", text)
            self.assertIn("降置信度", text)
            self.assertNotIn("流程停止", text)
            # Flow continues: percentile band and risk legs are still computed.
            self.assertIn("**当前 (100.0%)**", text)
            self.assertIn("50% 分位", text)
            # Potential risk takes the worse leg: ref 35.4 vs current 120 -> -70.5%.
            self.assertIn("-70.5%", text)
            self.assertIn("参考点腿", text)

    def test_ps_alert_line_warns_and_downgrades(self) -> None:
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
            self.assertIn("分位与风险读数降置信度", text)
            # Band still computed: midrank of 45 in [10,20,30,45] -> 87.5%.
            self.assertIn("**当前 (87.5%)**", text)

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

    def test_position_plan_with_grade_in_report(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="NVDA",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=100.0,
                max_loss_streak=0,
                ref_pe=35.4,
                grade="通过",
            )
            text = path.read_text(encoding="utf-8")
            # risk 64.6% -> budget-2 base 2/64.6 = 3.1%, 通过 x0.5 -> 1.5% (primary, bolded).
            self.assertIn("3.1%", text)
            self.assertIn("**1.5%**", text)
            self.assertIn("通过 ×0.5", text)
            self.assertIn("回撤预算", text)
            # Full ladder rendered: budget-10 base 10/64.6 = 15.5%, final 7.7%; budget-70 present.
            self.assertIn("15.5%", text)
            self.assertIn("| 70% |", text)
            self.assertIn("其它回撤预算档位（2/5/10/20/30/50/70%）见第七节表", text)

    def test_position_blocked_for_pending_grade(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="WAIT",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=100.0,
                max_loss_streak=0,
                ref_pe=35.4,
                grade="待验证",
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("不给仓位", text)
            self.assertIn("仓位上限：不适用", text)

    def test_alert_zeroes_new_position(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="HYPE",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=120.0,
                pe_median=60.0,
                max_loss_streak=0,
                ref_pe=35.4,
                grade="金池子",
            )
            text = path.read_text(encoding="utf-8")
            # ref leg 35.4/120-1 = -70.5% -> budget-2 formula 2/70.5 = 2.8%, zeroed by alert.
            self.assertIn("0%（公式 2.8%）", text)
            self.assertIn("0%（警戒线触发且未放宽，不建新仓", text)
            self.assertIn("警戒线触发且未放宽：新建仓一律归零", text)

    def test_alert_release_half试仓_in_report(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="NVDA23",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=120.0,
                pe_median=60.0,
                max_loss_streak=0,
                ref_pe=35.4,
                grade="金池子",
                alert_release=True,
                alert_release_evidence="公司指引 + 在手订单/产能锁定",
                forward_pe=90.0,
            )
            text = path.read_text(encoding="utf-8")
            # ref leg 35.4/120-1 = -70.5% -> budget-2 formula 2.8%, x0.5 released = 1.4%.
            self.assertIn("警戒线放宽 ×0.5", text)
            self.assertIn("1.4%（公式 2.8%）", text)
            self.assertNotIn("警戒线触发且未放宽", text)
            # Release evidence + forward reading are rendered as auditable fields.
            self.assertIn("公司指引 + 在手订单/产能锁定", text)
            self.assertIn("forward TTM PE 90.00", text)

    def test_alert_release_rejected_without_evidence_in_report(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                generator.create_report(
                    ticker="NOEV",
                    company_type="成长",
                    report_date=date(2026, 7, 20),
                    output_dir=output_dir,
                    template_path=self._template(output_dir),
                    pe_series=[float(v) for v in range(10, 110)],
                    current_pe=120.0,
                    pe_median=60.0,
                    max_loss_streak=0,
                    ref_pe=35.4,
                    grade="金池子",
                    alert_release=True,  # triggered alert + no evidence/forward -> rejected
                )

    def test_digestion_overpriced_in_report(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="RICH",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=95.0,
                max_loss_streak=0,
                ref_pe=35.4,
                grade="通过",
                digestion="透支",
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("增速消化透支 ×0.5", text)
            # primary deployable: base 2/62.7*100=3.19 x0.5(通过) x0.5(透支)=0.8%.
            self.assertIn("透支 ×0.5", text)

    def test_gate_fail_position_uses_fallback_drawdown(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="MU",
                company_type="周期",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                grade="通过",
                fallback_drawdown=50.0,
            )
            text = path.read_text(encoding="utf-8")
            # base 2/50 = 4.0%, 通过 x0.5 -> 2.0%.
            self.assertIn("人工回撤兜底", text)
            self.assertIn("4.0%", text)
            self.assertIn("**2.0%**", text)

    def test_standalone_mode_notes_missing_grade(self) -> None:
        generator = load_generator_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            path = generator.create_report(
                ticker="SOLO",
                company_type="成长",
                report_date=date(2026, 7, 20),
                output_dir=output_dir,
                template_path=self._template(output_dir),
                pe_series=[float(v) for v in range(10, 110)],
                current_pe=100.0,
                max_loss_streak=0,
                ref_pe=35.4,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("未接入 chain-alpha 档位", text)

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
