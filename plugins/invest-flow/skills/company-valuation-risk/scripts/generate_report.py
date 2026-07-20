#!/usr/bin/env python3
"""Generate a company valuation & risk (percentile-band) report.

Method (matches the skill's methodology):
  1. Company-type gate: only 成长/现金牛/收费站 pass; 周期/脉冲/资产困境 stop
     (percentile-band valuation systematically misleads on the excluded types).
  2. Ruler selection: switch from PE to PS when any distortion condition
     triggers (5y median TTM PE > 100, current TTM PE negative, >=4
     consecutive loss-making quarters within 5y, negative TTM PE at the
     bear-market reference date). Then an alert-line check: current TTM PE
     above 100x (or TTM PS above 40x) raises a prominent warning; the flow
     continues, with every percentile and risk readout downgraded to low
     confidence. Insufficient history (late listing) raises a prominent
     low-confidence warning.
  3. Percentile band: current TTM PE/PS percentile within the company's own
     N-year distribution plus key percentile values (10/20/25/50/60/75/80/90/95).
  4. Potential risk: the worse of two drawdowns — reversion to the 50th
     percentile vs reversion to the reference-point multiple; if the current
     multiple already sits below the reference point, highlight prominently.
     Implied prices assume a static TTM denominator (price move == multiple
     move, valuation-only).
  5. Position plan (chain-alpha step 4): position cap = drawdown budget /
     potential risk, tabulated across a budget ladder (2/5/10/20/30/50/70%),
     where the drawdown budget is the max account-level drawdown (% of total
     assets) one name may inflict. Structural discounts stack: grade (金池子
     x1 / 通过 x0.5; 待验证/剔除 no position), elastic x0.5, short-history
     x0.5. Two signal-layer factors then apply on top (always <=1, only
     tighten or unlock, never amplify): a triggered alert line zeroes new
     entries unless released to x0.5 (tier-1 forward evidence + forward PE
     back inside the line), and a 透支 digestion verdict adds x0.5.

Percentiles come either from a historical value series (empirical, midrank)
or from vendor quantile anchors (piecewise-linear interpolation).
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


KEY_PERCENTILES = [10.0, 20.0, 25.0, 50.0, 60.0, 75.0, 80.0, 90.0, 95.0]
TABLE_PERCENTILES = [0.0] + KEY_PERCENTILES + [100.0]
ALLOWED_TYPES = ("成长", "现金牛", "收费站")
EXCLUDED_TYPES = ("周期", "脉冲", "资产困境")
DEFAULT_REF_DATE = "2026-03-31"
DEFAULT_REF_LABEL = "上轮熊市低点"
DEFAULT_WINDOW = "5年"
DEFAULT_PE_ALERT = 100.0
DEFAULT_PS_ALERT = 40.0
MIN_DATA_SPAN_YEARS = 5.0
DEFAULT_DRAWDOWN_BUDGET = 2.0
DRAWDOWN_BUDGET_LADDER = [2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 70.0]
GRADE_FACTORS = {"金池子": 1.0, "通过": 0.5}
BLOCKED_GRADES = ("待验证", "剔除")
ALERT_RELEASE_FACTOR = 0.5  # released alert -> half试仓 instead of zero
DIGESTION_OVERPRICED_FACTOR = 0.5  # digestion verdict 透支 -> extra x0.5
DIGESTION_VERDICTS = ("合理低估", "可消化", "部分消化", "透支")
PLACEHOLDER = "待填写"
NA_TEXT = "类型闸门未通过，本节不适用。"

INDUSTRY_CONTEXT_NOTE = (
    "- ⚠️ 特别提示（不影响公式计算与结论）：PE 分位必须结合行业与公司基本面解读——"
    "高分位若逢行业与公司双强（如 NVDA TTM PE 248 期），不构成卖出依据；"
    "低分位若逢行业担忧发酵（如存储板块杀估值），不构成买入依据。"
    "本标的行业×公司定性判断：待填写"
)

GATE_FAIL_NOTE = (
    "类型闸门未通过：`{ctype}` 属排除类型，估值分位法在此类公司上会系统性误导——\n"
    "周期型低 PE 常出现在盈利顶部、高 PE 常出现在底部；脉冲型 TTM 含一次性损益，分母不可外推；\n"
    "资产困境型 E 与 S 同时恶化，历史分位失去参照意义。\n\n"
    "替代框架：周期型改用 PB 分位或席勒化（周期平均）利润重算；脉冲型剔除一次性损益后重算 TTM；\n"
    "资产困境型改用资产/清算价值与偿债能力框架。"
)


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def parse_values(value: str) -> list[float]:
    """Parse an inline comma list of numeric values."""
    values: list[float] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        values.append(float(token))
    if not values:
        raise argparse.ArgumentTypeError("No numeric values parsed.")
    return values


def load_series(path: Path) -> list[float]:
    """Load a numeric series; accepts "value" or "date,value" per line."""
    values: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split(",")[-1].strip()
        try:
            values.append(float(token))
        except ValueError:
            continue
    if not values:
        raise ValueError(f"No numeric values parsed from series file: {path}")
    return values


def parse_anchors(value: str) -> list[tuple[float, float]]:
    """Parse "multiple:percentile,..." anchors, sorted ascending by multiple."""
    anchors: list[tuple[float, float]] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise argparse.ArgumentTypeError(
                f"Invalid anchor '{token}'. Use multiple:percentile, e.g. 16.8:50."
            )
        ratio_str, pct_str = token.split(":", 1)
        anchors.append((float(ratio_str), float(pct_str)))
    if len(anchors) < 2:
        raise argparse.ArgumentTypeError("Need at least two anchors for interpolation.")
    return sorted(anchors, key=lambda item: item[0])


def _interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Piecewise-linear interpolation with clamping outside the range."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y1
            return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
    return ys[-1]


def interp_pct_from_value(value: float, anchors: list[tuple[float, float]]) -> float:
    return _interp(value, [a[0] for a in anchors], [a[1] for a in anchors])


def interp_value_from_pct(pct: float, anchors: list[tuple[float, float]]) -> float:
    by_pct = sorted(anchors, key=lambda item: item[1])
    return _interp(pct, [a[1] for a in by_pct], [a[0] for a in by_pct])


def percentile_value(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (type-7): rank = pct/100 * (n-1)."""
    if not values:
        raise ValueError("Empty series.")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0.0, min(100.0, pct)) / 100.0 * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def percentile_rank(values: list[float], target: float) -> float:
    """Midrank percentile: (#below + 0.5 * #equal) / n * 100."""
    if not values:
        raise ValueError("Empty series.")
    below = sum(1 for v in values if v < target)
    equal = sum(1 for v in values if v == target)
    return (below + 0.5 * equal) / len(values) * 100.0


def median(values: list[float]) -> float:
    return percentile_value(values, 50.0)


def band_label(pct: float) -> str:
    if pct >= 90:
        return "高估/透支区"
    if pct >= 75:
        return "偏高区"
    if pct >= 50:
        return "中性偏高"
    if pct >= 25:
        return "中性偏低"
    if pct >= 10:
        return "低估区"
    return "极低估区"


@dataclass
class RulerDecision:
    metric: str  # "pe" | "ps"
    rows: list[tuple[str, str, str]]  # (condition label, reading, verdict)
    forced: bool
    unknowns: int

    @property
    def triggered_count(self) -> int:
        return sum(1 for _, _, verdict in self.rows if verdict == "触发")

    @property
    def reason(self) -> str:
        if self.forced:
            return "人工指定（覆盖自动判定）"
        if self.triggered_count:
            return f"自动判定：触发 {self.triggered_count} 项 PS 条件"
        suffix = f"，{self.unknowns} 项未提供需人工补查" if self.unknowns else ""
        return f"自动判定：未触发 PS 条件{suffix}"


def decide_metric(
    *,
    pe_median: float | None,
    current_pe: float | None,
    max_loss_streak: int | None,
    ref_pe: float | None,
    ref_date: str = DEFAULT_REF_DATE,
    ref_label: str = DEFAULT_REF_LABEL,
    window: str = DEFAULT_WINDOW,
    forced: str | None = None,
) -> RulerDecision:
    """Apply the four PE-distortion conditions; any trigger switches to PS."""

    def check(reading: float | int | None, hit: bool, text: str) -> tuple[str, str]:
        if reading is None:
            return "未提供", "未提供（需人工确认）"
        return text, ("触发" if hit else "未触发")

    rows: list[tuple[str, str, str]] = []
    reading, verdict = check(
        pe_median, pe_median is not None and pe_median > 100,
        f"中位数 {pe_median:.1f}" if pe_median is not None else "",
    )
    rows.append((f"过去 {window} TTM PE 中位数 > 100", reading, verdict))

    reading, verdict = check(
        current_pe, current_pe is not None and current_pe < 0,
        f"当前 PE {current_pe:.1f}" if current_pe is not None else "",
    )
    rows.append(("当前 TTM PE 为负", reading, verdict))

    reading, verdict = check(
        max_loss_streak, max_loss_streak is not None and max_loss_streak >= 4,
        f"最长连亏 {max_loss_streak} 季" if max_loss_streak is not None else "",
    )
    rows.append((f"过去 {window} 存在连续 ≥4 个季度净利润为负", reading, verdict))

    reading, verdict = check(
        ref_pe, ref_pe is not None and ref_pe < 0,
        f"参考点 PE {ref_pe:.1f}" if ref_pe is not None else "",
    )
    rows.append((f"重要参考点 {ref_date}（{ref_label}）TTM PE 为负", reading, verdict))

    unknowns = sum(1 for _, _, verdict in rows if verdict.startswith("未提供"))
    triggered = any(verdict == "触发" for _, _, verdict in rows)

    if forced in ("pe", "ps"):
        return RulerDecision(metric=forced, rows=rows, forced=True, unknowns=unknowns)
    if triggered:
        return RulerDecision(metric="ps", rows=rows, forced=False, unknowns=unknowns)
    if unknowns == len(rows):
        raise ValueError(
            "无法自动选尺子：四个 PE 失真条件全部未提供。请至少提供 --pe-median / "
            "--current-pe / --max-loss-streak / --ref-pe 之一，或用 --metric 显式指定。"
        )
    return RulerDecision(metric="pe", rows=rows, forced=False, unknowns=unknowns)


def build_ruler_table(decision: RulerDecision) -> str:
    lines = [
        "| 条件（任一满足 → 改用 PS） | 读数 | 判定 |",
        "|---|---|:---:|",
    ]
    for label, reading, verdict in decision.rows:
        lines.append(f"| {label} | {reading} | {verdict} |")
    lines.append(
        f"| **结论** | {decision.reason} | **使用 {decision.metric.upper()}** |"
    )
    return "\n".join(lines)


def build_alert_check(
    *,
    metric_label: str,
    current_value: float | None,
    alert_line: float,
    pe_alert: float,
    ps_alert: float,
    triggered: bool,
) -> str:
    caption = (
        f"**警戒线检查**（PE > {pe_alert:g} 倍 或 PS > {ps_alert:g} 倍 → 重点提示，不停止）："
    )
    if current_value is None:
        detail = f"- 当前 {metric_label} 未提供，无法检查警戒线（补数后必须复核）。"
    elif triggered:
        detail = (
            f"- ⚠️ **当前 {metric_label} {current_value:.2f} > {alert_line:g} 倍警戒线 → 触发重点提示"
            "（不停止）：估值已进入极端区，历史分位的下行参照意义大幅减弱；"
            "建议先降风险敞口，后续分位与风险读数全部降置信度使用**"
        )
    else:
        detail = f"- 当前 {metric_label} {current_value:.2f} ≤ {alert_line:g} 倍警戒线，未触发。"
    return caption + "\n" + detail


def build_type_gate_table(company_type: str, type_basis: str, passed: bool) -> str:
    conclusion = (
        "**通过 → 进入第 2 步选尺子**" if passed else "**未通过 → 停止，本方法不适用**"
    )
    return "\n".join(
        [
            "| 项目 | 内容 |",
            "|---|---|",
            f"| 公司类型 | {company_type} |",
            f"| 可分析类型 | {' / '.join(ALLOWED_TYPES)} |",
            f"| 排除类型 | {' / '.join(EXCLUDED_TYPES)} |",
            f"| 判定依据 | {type_basis or PLACEHOLDER} |",
            f"| **闸门结论** | {conclusion} |",
        ]
    )


@dataclass
class RiskSummary:
    """Potential risk = the worse of the two drawdown legs (percent numbers)."""

    v50: float
    leg_median: float
    ref_value: float | None
    leg_ref: float | None
    ref_date: str
    ref_label: str
    below_ref: bool
    potential_risk: float | None
    driver: str


def compute_risk_summary(
    *,
    current_value: float,
    v50: float,
    ref_value: float | None,
    ref_date: str,
    ref_label: str,
) -> RiskSummary:
    leg_median = (v50 / current_value - 1) * 100
    leg_ref: float | None = None
    below_ref = False
    if ref_value is not None and ref_value > 0:
        leg_ref = (ref_value / current_value - 1) * 100
        below_ref = current_value < ref_value
    candidates = [("50% 分位腿", leg_median)]
    if leg_ref is not None:
        candidates.append(("参考点腿", leg_ref))
    downside = [(name, chg) for name, chg in candidates if chg < 0]
    if downside:
        driver, potential = min(downside, key=lambda item: item[1])
    else:
        driver, potential = "", None
    return RiskSummary(
        v50=v50,
        leg_median=leg_median,
        ref_value=ref_value,
        leg_ref=leg_ref,
        ref_date=ref_date,
        ref_label=ref_label,
        below_ref=below_ref,
        potential_risk=potential,
        driver=driver,
    )


@dataclass
class PositionRow:
    """One drawdown-budget rung: base cap before discounts, final after."""

    budget: float
    base_cap: float
    final_cap: float  # post-discount deployable cap (before any alert-line zeroing)


@dataclass
class PositionPlan:
    """Position cap = drawdown budget / potential risk, across a budget ladder.

    Drawdown budget = the maximum account-level drawdown (% of total assets)
    a single name is allowed to inflict. Each ladder rung yields its own cap;
    the primary budget (default 2%) is highlighted and used in the conclusion.
    All caps are percent-of-portfolio.
    """

    primary_budget: float
    risk_pct: float | None
    risk_source: str
    discount: float
    grade: str | None
    elastic: bool
    span_halved: bool
    alert_triggered: bool
    alert_released: bool
    digestion: str | None
    alert_factor: float
    digestion_factor: float
    signal_factor: float
    rows: list[PositionRow]
    blocked_reason: str

    @property
    def alert_zeroed(self) -> bool:
        return self.alert_triggered and not self.alert_released

    @property
    def digestion_overpriced(self) -> bool:
        return self.digestion == "透支"

    @property
    def primary_row(self) -> PositionRow | None:
        for row in self.rows:
            if abs(row.budget - self.primary_budget) < 1e-9:
                return row
        return None

    @property
    def primary_final_cap(self) -> float | None:
        """Deployable primary cap after structural discounts AND signal factors."""
        row = self.primary_row
        if row is None:
            return None
        return row.final_cap * self.signal_factor


def compute_position_plan(
    *,
    potential_risk: float | None,
    fallback_drawdown: float | None,
    drawdown_budget: float,
    grade: str | None,
    elastic: bool,
    alert_triggered: bool,
    span_insufficient: bool,
    alert_released: bool = False,
    digestion: str | None = None,
) -> PositionPlan:
    if drawdown_budget <= 0:
        raise ValueError("Drawdown budget must be positive.")
    if grade is not None and grade not in GRADE_FACTORS and grade not in BLOCKED_GRADES:
        raise ValueError(
            f"Unknown grade '{grade}'. Use one of: "
            f"{', '.join(tuple(GRADE_FACTORS) + BLOCKED_GRADES)}."
        )
    if fallback_drawdown is not None and fallback_drawdown <= 0:
        raise ValueError("Fallback drawdown must be a positive percent, e.g. 45 for -45%.")
    if digestion is not None and digestion not in DIGESTION_VERDICTS:
        raise ValueError(
            f"Unknown digestion verdict '{digestion}'. Use one of: {', '.join(DIGESTION_VERDICTS)}."
        )

    if potential_risk is not None and potential_risk < 0:
        risk_pct, risk_source = abs(potential_risk), "潜在风险（两腿取大）"
    elif fallback_drawdown is not None:
        risk_pct, risk_source = fallback_drawdown, "人工回撤兜底（--fallback-drawdown）"
    else:
        risk_pct, risk_source = None, ""

    discount = 1.0
    if grade in GRADE_FACTORS:
        discount *= GRADE_FACTORS[grade]
    if elastic:
        discount *= 0.5
    if span_insufficient:
        discount *= 0.5

    # Signal-layer factors: always <= 1, only tighten or unlock, never amplify.
    if alert_triggered:
        alert_factor = ALERT_RELEASE_FACTOR if alert_released else 0.0
    else:
        alert_factor = 1.0
    digestion_factor = DIGESTION_OVERPRICED_FACTOR if digestion == "透支" else 1.0
    signal_factor = alert_factor * digestion_factor

    plan = PositionPlan(
        primary_budget=drawdown_budget,
        risk_pct=risk_pct,
        risk_source=risk_source,
        discount=discount,
        grade=grade,
        elastic=elastic,
        span_halved=span_insufficient,
        alert_triggered=alert_triggered,
        alert_released=alert_released,
        digestion=digestion,
        alert_factor=alert_factor,
        digestion_factor=digestion_factor,
        signal_factor=signal_factor,
        rows=[],
        blocked_reason="",
    )
    if grade in BLOCKED_GRADES:
        plan.blocked_reason = f"chain-alpha 档位为「{grade}」，不给仓位（升档后再定仓）"
        return plan
    if risk_pct is None:
        plan.blocked_reason = (
            "潜在风险不可用（两腿均无下行或分位分析未完成），"
            "需人工复核后用 --fallback-drawdown 提供回撤再定仓"
        )
        return plan

    budgets = sorted(set(DRAWDOWN_BUDGET_LADDER) | {drawdown_budget})
    for budget in budgets:
        base = budget / risk_pct * 100
        plan.rows.append(PositionRow(budget=budget, base_cap=base, final_cap=base * discount))
    if plan.alert_zeroed:
        plan.blocked_reason = "警戒线触发且未放宽——不建新仓，档位表折后值仅作回线内复评参考"
    return plan


def _discount_caption(plan: PositionPlan) -> str:
    bits = []
    if plan.grade:
        bits.append(f"档位 {plan.grade} ×{GRADE_FACTORS[plan.grade]:g}")
    else:
        bits.append("未接入 chain-alpha 档位 ×1（独立使用，未经第三步验证）")
    if plan.elastic:
        bits.append("弹性标的 ×0.5")
    if plan.span_halved:
        bits.append("数据不足 ×0.5")
    return "；".join(bits) + f"（合计 ×{plan.discount:g}）"


def _signal_bits(plan: PositionPlan) -> list[str]:
    """Human-readable signal-layer factor bits (alert + digestion)."""
    bits = []
    if plan.alert_triggered:
        if plan.alert_released:
            bits.append("警戒线放宽 ×0.5（已举证一档硬证据 + forward PE 回线内，半仓试仓）")
        else:
            bits.append("警戒线触发 ×0（未放宽，不建新仓）")
    if plan.digestion_overpriced:
        bits.append("增速消化透支 ×0.5")
    return bits


def build_position_section(plan: PositionPlan) -> str:
    if not plan.rows:
        risk_cell = "—" if plan.risk_pct is None else f"{plan.risk_pct:.1f}%"
        return "\n".join(
            [
                f"- 潜在风险：{risk_cell}（{plan.risk_source or '不可用'}）",
                f"- 仓位上限：**不适用**（{plan.blocked_reason}）",
            ]
        )

    two_col = abs(plan.discount - 1.0) > 1e-9
    signal_bits = _signal_bits(plan)
    lines = [
        f"- 潜在风险：{plan.risk_pct:.1f}%（{plan.risk_source}）",
        f"- 结构折扣：{_discount_caption(plan)}",
    ]
    if signal_bits:
        lines.append(
            f"- 信号层系数：{'；'.join(signal_bits)}（信号层合计 ×{plan.signal_factor:g}）"
        )
    lines.append("")
    if two_col:
        lines.append("| 回撤预算 | 基础仓位上限 | 折后仓位上限 |")
        lines.append("|---:|---:|---:|")
    else:
        lines.append("| 回撤预算 | 仓位上限 |")
        lines.append("|---:|---:|")

    has_over_100 = False
    for row in plan.rows:
        is_primary = abs(row.budget - plan.primary_budget) < 1e-9
        if max(row.base_cap, row.final_cap) > 100:
            has_over_100 = True
        deployable = row.final_cap * plan.signal_factor
        budget_cell = f"{row.budget:g}%"
        base_cell = f"{row.base_cap:.1f}%"
        if abs(plan.signal_factor - 1.0) < 1e-9:
            final_cell = f"{row.final_cap:.1f}%"
        elif plan.signal_factor == 0.0:
            final_cell = f"0%（公式 {row.final_cap:.1f}%）"
        else:
            final_cell = f"{deployable:.1f}%（公式 {row.final_cap:.1f}%）"
        if is_primary:
            budget_cell = f"**{budget_cell}**"
            base_cell = f"**{base_cell}**"
            final_cell = f"**{final_cell}**"
        if two_col:
            lines.append(f"| {budget_cell} | {base_cell} | {final_cell} |")
        else:
            lines.append(f"| {budget_cell} | {final_cell} |")

    lines.append("")
    lines.append(f"- 回撤预算 = 单只标的最多允许给整个账户带来的回撤（占总资产 %）；主档 **{plan.primary_budget:g}%**（加粗行）。")
    if signal_bits:
        lines.append("- 折后仓位上限 = 结构折扣后；括号内为信号层调整前的公式值，最终新建仓以信号层调整后为准。")
    lines.append("- 仓位为组合占比上限，不是建议买入量；与计价币种无关；信号层系数只向保守/解锁，永不放大（≤1）。")
    if plan.alert_zeroed:
        lines.append("- ⚠️ 警戒线触发且未放宽：新建仓一律归零，上表折后值仅作回到警戒线内的复评参考。")
    elif plan.alert_triggered and plan.alert_released:
        lines.append("- ⚠️ 警戒线触发但已放宽：仅限半仓试仓（×0.5），须已举证一档硬证据（公司指引 + 在手订单/产能锁定，或 delivery-tracking 已点亮 L4 入表）且 forward PE 已回到警戒线内。")
    if plan.digestion is None:
        lines.append("- 提示：未提供增速消化判定（--digestion）；若第六节判定为透支，新建仓需再 ×0.5，请据此复核。")
    if has_over_100:
        lines.append("- 注：仓位 >100% 表示该回撤预算已超过标的单杀空间（需杠杆才能达到），仅作参照。")
    lines.append(
        "- 潜在风险为估值单杀口径；若分母（E/S）同步下修为双杀，实际回撤可能超过回撤预算——"
        "建仓后交给 chain-alpha-delivery-tracking 按季跟踪。"
    )
    return "\n".join(lines)


def position_conclusion_line(plan: PositionPlan) -> str:
    if not plan.rows:
        return f"- 仓位上限：不适用（{plan.blocked_reason}）"
    if plan.alert_zeroed:
        return "- 仓位上限：**0%（警戒线触发且未放宽，不建新仓）**；各回撤预算档位公式值见第七节表"
    cap = plan.primary_final_cap
    factors = []
    if plan.grade:
        factors.append(f"{plan.grade} ×{GRADE_FACTORS[plan.grade]:g}")
    if plan.elastic:
        factors.append("弹性 ×0.5")
    if plan.span_halved:
        factors.append("数据不足 ×0.5")
    if plan.alert_triggered and plan.alert_released:
        factors.append("警戒线放宽 ×0.5")
    if plan.digestion_overpriced:
        factors.append("透支 ×0.5")
    suffix = f"，{'、'.join(factors)}" if factors else ""
    return (
        f"- 仓位上限（回撤预算 {plan.primary_budget:g}%）：**{cap:.1f}%**"
        f"（回撤预算 {plan.primary_budget:g}% ÷ 潜在风险 {plan.risk_pct:.1f}%{suffix}）；"
        "其它回撤预算档位（2/5/10/20/30/50/70%）见第七节表"
    )


def _pct_row_label(pct: float) -> str:
    if pct <= 0:
        return "历史最低 (0%)"
    if pct >= 100:
        return "历史最高 (100%)"
    return f"{pct:g}% 分位"


def build_band_table(
    *,
    metric_label: str,
    current_value: float,
    current_pct: float,
    values_by_pct: dict[float, float],
    current_price: float | None,
) -> str:
    def implied_price(value: float) -> str:
        if current_price is None:
            return PLACEHOLDER
        return f"{current_price * value / current_value:.2f}"

    rows: list[tuple[float, int, str]] = []
    for pct in sorted(values_by_pct):
        value = values_by_pct[pct]
        change = value / current_value - 1
        rows.append(
            (
                pct,
                0,
                f"| {_pct_row_label(pct)} | {value:.2f} | {implied_price(value)} | {change * 100:+.1f}% |",
            )
        )
    current_price_cell = f"**{current_price:.2f}**" if current_price is not None else PLACEHOLDER
    rows.append(
        (
            current_pct,
            1,
            f"| **当前 ({current_pct:.1f}%)** | **{current_value:.2f}** | {current_price_cell} | — |",
        )
    )
    rows.sort(key=lambda item: (item[0], item[1]), reverse=True)

    lines = [
        f"| 分位情景 | {metric_label} | 隐含价格 | 较当前 |",
        "|---|---|---|---|",
    ]
    lines.extend(row for _, _, row in rows)
    return "\n".join(lines)


def build_risk_readouts(
    *,
    current_value: float,
    values_by_pct: dict[float, float],
    denom_label: str,
    metric_label: str,
    risk: RiskSummary,
) -> str:
    def change(pct: float) -> float:
        return (values_by_pct[pct] / current_value - 1) * 100

    def aux_line(pct: float) -> str:
        return f"  - 至 {_pct_row_label(pct)}（{values_by_pct[pct]:.2f}）：{change(pct):+.1f}%"

    lines: list[str] = []
    if risk.potential_risk is not None:
        lines.append(
            f"- **潜在风险（跌回 50% 分位 vs 跌回重要参考点，取大）：{risk.potential_risk:+.1f}%"
            f"（{risk.driver}）**"
        )
    else:
        lines.append(
            "- **潜在风险：两腿均无下行——当前已低于 50% 分位与重要参考点，"
            "需重点复核是极端低估还是参考系失效**"
        )
    lines.append(f"  - 跌回 50% 分位（{risk.v50:.2f}）：{risk.leg_median:+.1f}%")
    if risk.leg_ref is not None:
        lines.append(
            f"  - 跌回重要参考点 {risk.ref_date}（{risk.ref_label}，{metric_label} "
            f"{risk.ref_value:.2f}）：{risk.leg_ref:+.1f}%"
        )
    else:
        lines.append(
            f"  - 跌回重要参考点：未提供参考点 {metric_label}（--ref-pe / --ref-ps），"
            "此腿缺失，潜在风险仅按 50% 分位腿计"
        )
    if risk.below_ref:
        lines.append(
            f"  - ⚠️ **重点提示：当前 {metric_label} {current_value:.2f} 已低于重要参考点"
            f" {risk.ref_date}（{risk.ref_label}）的 {risk.ref_value:.2f}——"
            "要么极端低估，要么参考点已失效（分母口径变化），必须人工复核**"
        )

    lines.append(f"- 辅助向下情景（估值单杀，TTM {denom_label}不变）：")
    for pct in (25.0, 10.0, 0.0):
        lines.append(aux_line(pct))
    lines.append("- 向上情景（估值扩张）：")
    for pct in (75.0, 90.0, 100.0):
        lines.append(aux_line(pct))

    downside = change(25.0)
    upside = change(90.0)
    if downside < 0 and upside > 0:
        ratio = upside / abs(downside)
        lines.append(f"- 风险收益比（至 90% 分位涨幅 ÷ 至 25% 分位跌幅）：{ratio:.2f}")
    else:
        lines.append("- 风险收益比：不适用（当前分位已在 25%-90% 带外侧）")
    lines.append(
        f"- 双杀提示：以上为 TTM {denom_label}不变的静态测算；若{denom_label}同步下修即为双杀，"
        "实际跌幅将大于表中数值，反之为双击。"
    )
    return "\n".join(lines)


def build_conclusion_pass(
    *,
    company_type: str,
    decision: RulerDecision,
    metric_label: str,
    window: str,
    current_value: float,
    current_pct: float,
    values_by_pct: dict[float, float],
    risk: RiskSummary,
    position_line: str,
    prominent: list[str],
) -> str:
    def change(pct: float) -> float:
        return (values_by_pct[pct] / current_value - 1) * 100

    if risk.leg_ref is not None:
        legs_text = f"跌回 50% 分位 {risk.leg_median:+.1f}% vs 跌回参考点 {risk.leg_ref:+.1f}%"
    else:
        legs_text = f"跌回 50% 分位 {risk.leg_median:+.1f}%；参考点腿未提供"
    if risk.potential_risk is not None:
        risk_line = f"- 潜在风险（{legs_text}，取大）：**{risk.potential_risk:+.1f}%**"
    else:
        risk_line = f"- 潜在风险（{legs_text}）：两腿均无下行，当前处于历史低位——需重点复核"

    lines = [
        f"- 公司类型：{company_type}（类型闸门：通过）",
        f"- 估值尺子：{metric_label}（{decision.reason}）",
        f"- 当前 {metric_label}：{current_value:.2f}，位于{window}第 **{current_pct:.1f}%** 分位 —— **{band_label(current_pct)}**",
        risk_line,
        position_line,
        f"- 估值扩张空间：至 90% 分位 {change(90.0):+.1f}%",
    ]
    lines.extend(f"- {item}" for item in prominent)
    lines.append(INDUSTRY_CONTEXT_NOTE)
    lines.append(f"- 一句话判断：{PLACEHOLDER}")
    return "\n".join(lines)


def build_conclusion_fail(company_type: str, position_line: str) -> str:
    return "\n".join(
        [
            f"- 公司类型：{company_type}（类型闸门：未通过 → 排除）",
            "- 结论：本方法不适用，流程停止于第 1 步，不输出估值分位与风险测算",
            position_line,
            INDUSTRY_CONTEXT_NOTE,
            f"- 一句话判断：{PLACEHOLDER}",
        ]
    )


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^\w一-鿿.-]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-._")
    return value or "company"


def find_unique_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    stem, suffix, parent = base_path.stem, base_path.suffix, base_path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def render_template(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered


def create_report(
    *,
    ticker: str,
    company: str = "",
    company_type: str,
    type_basis: str = "",
    market: str = "",
    source: str = "",
    window: str = DEFAULT_WINDOW,
    report_date: date,
    output_dir: Path,
    template_path: Path,
    pe_series: list[float] | None = None,
    ps_series: list[float] | None = None,
    pe_anchors: list[tuple[float, float]] | None = None,
    ps_anchors: list[tuple[float, float]] | None = None,
    pe_median: float | None = None,
    current_pe: float | None = None,
    current_ps: float | None = None,
    current_price: float | None = None,
    max_loss_streak: int | None = None,
    ref_date: str = DEFAULT_REF_DATE,
    ref_label: str = DEFAULT_REF_LABEL,
    ref_pe: float | None = None,
    ref_ps: float | None = None,
    metric: str = "auto",
    current_percentile: float | None = None,
    pe_alert: float = DEFAULT_PE_ALERT,
    ps_alert: float = DEFAULT_PS_ALERT,
    data_span_years: float | None = None,
    grade: str | None = None,
    elastic: bool = False,
    drawdown_budget: float = DEFAULT_DRAWDOWN_BUDGET,
    fallback_drawdown: float | None = None,
    alert_release: bool = False,
    digestion: str | None = None,
) -> Path:
    ticker = ticker.strip()
    if not ticker:
        raise ValueError("Ticker cannot be empty.")
    company = company.strip() or ticker
    if company_type not in ALLOWED_TYPES + EXCLUDED_TYPES:
        raise ValueError(
            f"Unknown company type '{company_type}'. "
            f"Use one of: {', '.join(ALLOWED_TYPES + EXCLUDED_TYPES)}."
        )
    if metric not in ("auto", "pe", "ps"):
        raise ValueError("metric must be one of: auto, pe, ps.")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    if current_percentile is not None and not 0 <= current_percentile <= 100:
        raise ValueError("current_percentile must be within [0, 100].")

    if current_pe is None and pe_series:
        current_pe = pe_series[-1]
    if current_ps is None and ps_series:
        current_ps = ps_series[-1]
    if pe_median is None and pe_series:
        pe_median = median(pe_series)

    gate_passed = company_type in ALLOWED_TYPES
    notes: list[str] = []
    prominent: list[str] = []
    span_insufficient = data_span_years is not None and data_span_years < MIN_DATA_SPAN_YEARS
    if span_insufficient:
        prominent.append(
            f"⚠️ **历史数据不足：分位样本仅覆盖约 {data_span_years:.1f} 年"
            f"（不足 {MIN_DATA_SPAN_YEARS:g} 年窗口，如上市较晚）——分位带参照性差，"
            "全部分位结论必须降置信度**"
        )
        notes.append(
            f"- ⚠️ 历史数据不足：样本仅约 {data_span_years:.1f} 年，分位结论降置信度。"
        )

    if not gate_passed:
        plan = compute_position_plan(
            potential_risk=None,
            fallback_drawdown=fallback_drawdown,
            drawdown_budget=drawdown_budget,
            grade=grade,
            elastic=elastic,
            alert_triggered=False,
            span_insufficient=span_insufficient,
            alert_released=alert_release,
            digestion=digestion,
        )
        if fallback_drawdown is not None and plan.rows:
            position_block = (
                "类型闸门未通过——分位法潜在风险不可用，以下仓位基于人工回撤兜底（--fallback-drawdown）：\n\n"
                + build_position_section(plan)
            )
        else:
            position_block = (
                "类型闸门未通过，分位法仓位框架不适用；"
                "如需仓位，请人工评估最大回撤后用 --fallback-drawdown 重跑。"
            )
        replacements = {
            "{{结论块}}": build_conclusion_fail(company_type, position_conclusion_line(plan)),
            "{{类型闸门表}}": build_type_gate_table(company_type, type_basis, False),
            "{{尺子选择表}}": NA_TEXT,
            "{{分位风险表}}": NA_TEXT,
            "{{分位备注}}": GATE_FAIL_NOTE.format(ctype=company_type),
            "{{风险读数}}": NA_TEXT,
            "{{建仓计划}}": position_block,
            "{{尺子标签}}": "—",
            "{{分位方法}}": "—",
        }
    else:
        decision = decide_metric(
            pe_median=pe_median,
            current_pe=current_pe,
            max_loss_streak=max_loss_streak,
            ref_pe=ref_pe,
            ref_date=ref_date,
            ref_label=ref_label,
            window=window,
            forced=None if metric == "auto" else metric,
        )
        chosen = decision.metric
        metric_label = "TTM PE" if chosen == "pe" else "TTM PS"
        denom_label = "每股盈利（E）" if chosen == "pe" else "每股营收（S）"
        series = pe_series if chosen == "pe" else ps_series
        anchors = pe_anchors if chosen == "pe" else ps_anchors
        current_value = current_pe if chosen == "pe" else current_ps
        ref_value = ref_pe if chosen == "pe" else ref_ps
        alert_line = pe_alert if chosen == "pe" else ps_alert

        alert_triggered = current_value is not None and current_value > alert_line
        ruler_block = build_ruler_table(decision) + "\n\n" + build_alert_check(
            metric_label=metric_label,
            current_value=current_value,
            alert_line=alert_line,
            pe_alert=pe_alert,
            ps_alert=ps_alert,
            triggered=alert_triggered,
        )

        if alert_triggered:
            prominent.insert(
                0,
                f"⚠️ **警戒线触发：当前 {metric_label} {current_value:.2f} > {alert_line:g} 倍——"
                "估值已进入极端区，历史分位的下行参照意义大幅减弱；"
                "先降风险敞口，全部分位与风险读数降置信度使用**",
            )
            notes.append(
                f"- ⚠️ 警戒线触发：当前 {metric_label} {current_value:.2f} > {alert_line:g} 倍，"
                "分位与风险读数降置信度。"
            )

        if series:
            filtered = [v for v in series if v > 0]
            dropped = len(series) - len(filtered)
            if not filtered:
                raise ValueError(f"{metric_label} 序列没有正值观测，无法计算分位。")
            if current_value is None:
                raise ValueError(f"缺少当前 {metric_label} 值。")
            if current_value <= 0:
                raise ValueError(
                    f"当前 {metric_label} 为非正值，不能用 {chosen.upper()} 尺子；"
                    "请改用 PS（--metric ps 并提供 PS 数据）。"
                )
            current_pct = (
                current_percentile
                if current_percentile is not None
                else percentile_rank(filtered, current_value)
            )
            values_by_pct = {p: percentile_value(filtered, p) for p in TABLE_PERCENTILES}
            method_label = f"{len(filtered)} 点历史序列经验分位（midrank）"
            notes.append(
                f"- 分位样本：{len(filtered)} 点历史序列"
                + (f"；已剔除非正观测 {dropped} 点" if dropped else "")
                + "。"
            )
            if dropped > 0.2 * len(series):
                notes.append(
                    "- ⚠️ 非正观测占比超过 20%，PE 分位参考性差——请复核第 2 步换 PS 条件是否应触发。"
                )
        elif anchors:
            if current_value is None:
                raise ValueError(
                    f"锚点模式必须显式提供当前 {metric_label} 值（--current-{chosen}）。"
                )
            if current_value <= 0:
                raise ValueError(
                    f"当前 {metric_label} 为非正值，不能用 {chosen.upper()} 尺子；"
                    "请改用 PS（--metric ps 并提供 PS 数据）。"
                )
            current_pct = (
                current_percentile
                if current_percentile is not None
                else interp_pct_from_value(current_value, anchors)
            )
            values_by_pct = {p: interp_value_from_pct(p, anchors) for p in TABLE_PERCENTILES}
            method_label = "分位锚点分段线性插值（顶/底部区间较粗略）"
            notes.append("- 分位值由锚点分段线性插值，锚点覆盖不到的分位按端点截断，较粗略。")
        else:
            raise ValueError(
                f"尺子判定为 {chosen.upper()}，但未提供 {metric_label} 数据："
                f"请提供 --{chosen}-file / --{chosen}-values 或 --{chosen}-anchors。"
            )

        risk = compute_risk_summary(
            current_value=current_value,
            v50=values_by_pct[50.0],
            ref_value=ref_value,
            ref_date=ref_date,
            ref_label=ref_label,
        )
        if risk.below_ref:
            prominent.append(
                f"⚠️ **重点提示：当前 {metric_label} {current_value:.2f} 已低于重要参考点"
                f" {ref_date}（{ref_label}）的 {risk.ref_value:.2f}——"
                "极端低估或参考点失效，需人工复核**"
            )
        if risk.leg_ref is None:
            notes.append(
                f"- 参考点 {metric_label} 未提供（--ref-pe / --ref-ps），"
                "潜在风险仅按 50% 分位腿计算。"
            )

        if current_percentile is not None:
            notes.append(
                f"- 当前分位使用外部数据源报告值 {current_percentile:.1f}%（覆盖计算值）。"
            )
        if current_price is None:
            notes.append("- 未提供当前价格，隐含价格列留待填写（--current-price）。")

        plan = compute_position_plan(
            potential_risk=risk.potential_risk,
            fallback_drawdown=fallback_drawdown,
            drawdown_budget=drawdown_budget,
            grade=grade,
            elastic=elastic,
            alert_triggered=alert_triggered,
            span_insufficient=span_insufficient,
            alert_released=alert_release,
            digestion=digestion,
        )

        replacements = {
            "{{结论块}}": build_conclusion_pass(
                company_type=company_type,
                decision=decision,
                metric_label=metric_label,
                window=window,
                current_value=current_value,
                current_pct=current_pct,
                values_by_pct=values_by_pct,
                risk=risk,
                position_line=position_conclusion_line(plan),
                prominent=prominent,
            ),
            "{{类型闸门表}}": build_type_gate_table(company_type, type_basis, True),
            "{{尺子选择表}}": ruler_block,
            "{{分位风险表}}": build_band_table(
                metric_label=metric_label,
                current_value=current_value,
                current_pct=current_pct,
                values_by_pct=values_by_pct,
                current_price=current_price,
            ),
            "{{分位备注}}": "\n".join(notes) if notes else "- 无",
            "{{风险读数}}": build_risk_readouts(
                current_value=current_value,
                values_by_pct=values_by_pct,
                denom_label=denom_label,
                metric_label=metric_label,
                risk=risk,
            ),
            "{{建仓计划}}": build_position_section(plan),
            "{{尺子标签}}": metric_label,
            "{{分位方法}}": method_label,
        }

    replacements.update(
        {
            "{{TICKER}}": ticker,
            "{{公司名}}": company,
            "{{市场}}": market.strip() or PLACEHOLDER,
            "{{数据源}}": source.strip() or PLACEHOLDER,
            "{{窗口}}": window,
            "{{分析日期}}": report_date.isoformat(),
        }
    )

    report_body = render_template(template_path.read_text(encoding="utf-8"), replacements)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"company-valuation-risk-{slugify(ticker).upper()}-{report_date.isoformat()}.md"
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a company valuation & risk (percentile-band) Markdown report."
    )
    parser.add_argument("ticker", help="Ticker, e.g. NVDA or 688017.")
    parser.add_argument("--company", default="", help="Company display name.")
    parser.add_argument(
        "--company-type",
        required=True,
        choices=ALLOWED_TYPES + EXCLUDED_TYPES,
        help="Company type per the gate: 成长/现金牛/收费站 pass; 周期/脉冲/资产困境 stop.",
    )
    parser.add_argument("--type-basis", default="", help="One-line basis for the type call.")
    parser.add_argument("--market", default="", help="Listing market, e.g. 美股 / A股 / 港股.")
    parser.add_argument("--source", default="", help="Data source / caliber label.")
    parser.add_argument("--window", default=DEFAULT_WINDOW, help=f"Percentile window label. Default: {DEFAULT_WINDOW}.")
    parser.add_argument("--pe-file", default="", help="Path to a TTM PE series file (value or date,value per line).")
    parser.add_argument("--pe-values", default="", help="Inline comma list of TTM PE values (oldest -> newest).")
    parser.add_argument("--pe-anchors", default="", help='TTM PE percentile anchors "multiple:pct,...", e.g. "18.2:0,33.1:50,88.0:100".')
    parser.add_argument("--ps-file", default="", help="Path to a TTM PS series file.")
    parser.add_argument("--ps-values", default="", help="Inline comma list of TTM PS values (oldest -> newest).")
    parser.add_argument("--ps-anchors", default="", help='TTM PS percentile anchors "multiple:pct,...".')
    parser.add_argument("--pe-median", default=None, type=float, help="5y median TTM PE (if not derivable from the series).")
    parser.add_argument("--current-pe", default=None, type=float, help="Current TTM PE. Defaults to the last PE series value.")
    parser.add_argument("--current-ps", default=None, type=float, help="Current TTM PS. Defaults to the last PS series value.")
    parser.add_argument("--current-price", default=None, type=float, help="Current share price, for implied-price rows.")
    parser.add_argument("--max-loss-streak", default=None, type=int, help="Max consecutive loss-making quarters within the window.")
    parser.add_argument("--ref-date", default=DEFAULT_REF_DATE, help=f"Reference-point date. Default: {DEFAULT_REF_DATE}.")
    parser.add_argument("--ref-label", default=DEFAULT_REF_LABEL, help=f"Reference-point label. Default: {DEFAULT_REF_LABEL}.")
    parser.add_argument("--ref-pe", default=None, type=float, help="TTM PE at the reference date (ruler-switch check + risk leg).")
    parser.add_argument("--ref-ps", default=None, type=float, help="TTM PS at the reference date (risk leg when the ruler is PS).")
    parser.add_argument("--metric", default="auto", choices=["auto", "pe", "ps"], help="Force the ruler instead of auto-deciding.")
    parser.add_argument("--current-percentile", default=None, type=float, help="Override current percentile (e.g. vendor-reported).")
    parser.add_argument("--pe-alert", default=DEFAULT_PE_ALERT, type=float, help=f"PE alert line (prominent warning + stop). Default: {DEFAULT_PE_ALERT:g}.")
    parser.add_argument("--ps-alert", default=DEFAULT_PS_ALERT, type=float, help=f"PS alert line (prominent warning + stop). Default: {DEFAULT_PS_ALERT:g}.")
    parser.add_argument("--data-span-years", default=None, type=float, help="Actual years covered by the percentile data; <5 triggers a prominent low-confidence warning and halves the position cap.")
    parser.add_argument("--grade", default=None, choices=tuple(GRADE_FACTORS) + BLOCKED_GRADES, help="chain-alpha verification grade; 金池子 full, 通过 x0.5, 待验证/剔除 no position.")
    parser.add_argument("--elastic", action="store_true", help="Elastic name (link revenue share 20-40%%): position cap x0.5.")
    parser.add_argument("--drawdown-budget", default=DEFAULT_DRAWDOWN_BUDGET, type=float, help=f"Primary/highlighted drawdown budget (%% of total assets one name may inflict). The report tabulates the full ladder {DRAWDOWN_BUDGET_LADDER}; this value is bolded and used in the conclusion. Default: {DEFAULT_DRAWDOWN_BUDGET:g}.")
    parser.add_argument("--fallback-drawdown", default=None, type=float, help="Manual drawdown %% (e.g. 45 for -45%%) used when the percentile-based potential risk is unavailable.")
    parser.add_argument("--alert-release", action="store_true", help="Release the alert line from zero to a half试仓 (x0.5). Only assert with tier-1 evidence: company guidance + orders/capacity lock (or delivery-tracking L4 lit) AND forward PE back inside the line. No effect unless the alert line is triggered.")
    parser.add_argument("--digestion", default=None, choices=list(DIGESTION_VERDICTS), help="Growth-digestion verdict from section 6. 透支 applies an extra x0.5 to new positions; other verdicts do not change the cap.")
    parser.add_argument("--date", type=parse_date, default=date.today(), help="Analysis date YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--output-dir", default="./output/company-valuation-risk", help="Output directory for the report.")
    parser.add_argument("--template", default="", help="Optional custom template path.")
    args = parser.parse_args()

    def resolve_series(file_arg: str, values_arg: str) -> list[float] | None:
        if file_arg:
            return load_series(Path(file_arg).expanduser().resolve())
        if values_arg:
            return parse_values(values_arg)
        return None

    script_dir = Path(__file__).resolve().parent
    default_template = script_dir.parent / "references" / "report-template.md"
    template_path = Path(args.template).expanduser().resolve() if args.template else default_template

    output_path = create_report(
        ticker=args.ticker,
        company=args.company,
        company_type=args.company_type,
        type_basis=args.type_basis,
        market=args.market,
        source=args.source,
        window=args.window,
        report_date=args.date,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        template_path=template_path,
        pe_series=resolve_series(args.pe_file, args.pe_values),
        ps_series=resolve_series(args.ps_file, args.ps_values),
        pe_anchors=parse_anchors(args.pe_anchors) if args.pe_anchors else None,
        ps_anchors=parse_anchors(args.ps_anchors) if args.ps_anchors else None,
        pe_median=args.pe_median,
        current_pe=args.current_pe,
        current_ps=args.current_ps,
        current_price=args.current_price,
        max_loss_streak=args.max_loss_streak,
        ref_date=args.ref_date,
        ref_label=args.ref_label,
        ref_pe=args.ref_pe,
        ref_ps=args.ref_ps,
        metric=args.metric,
        current_percentile=args.current_percentile,
        pe_alert=args.pe_alert,
        ps_alert=args.ps_alert,
        data_span_years=args.data_span_years,
        grade=args.grade,
        elastic=args.elastic,
        drawdown_budget=args.drawdown_budget,
        fallback_drawdown=args.fallback_drawdown,
        alert_release=args.alert_release,
        digestion=args.digestion,
    )
    print(output_path)


if __name__ == "__main__":
    main()
