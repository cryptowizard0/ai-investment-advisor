#!/usr/bin/env python3
"""Generate an index valuation price-sensitivity report.

Given a base valuation multiple (default TTM P/E computed with the 整体法
aggregate caliber) plus either percentile anchor points or a historical value
series, compute how a set of index-price moves shift the multiple and its
N-year percentile, then render a Chinese Markdown report.

Core method (matches the skill's methodology):
  new multiple = base multiple * (1 + price_move)   # earnings held constant
  percentile   = rank of new multiple within the N-year distribution

The percentile is looked up either by piecewise-linear interpolation over
supplied quantile anchors (min/20/50/80/current/max ...) or empirically from a
historical value series.
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


DEFAULT_MOVES = "0.10,0.05,-0.05,-0.10"
DEFAULT_METRIC = "TTM P/E"
DEFAULT_WINDOW = "5年"
DEFAULT_SOURCE = "Choice 指数整体口径"
PLACEHOLDER = "待填写"


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def parse_moves(value: str) -> list[float]:
    """Parse a comma list of fractional price moves; always include 0.0."""
    moves = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        moves.append(float(token))
    moves.append(0.0)
    # Descending so positive moves sit on top, 现在 in the middle, negatives below.
    return sorted(set(moves), reverse=True)


def parse_anchors(value: str) -> list[tuple[float, float]]:
    """Parse "pe:pct,pe:pct,..." anchors, sorted ascending by multiple."""
    anchors: list[tuple[float, float]] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise argparse.ArgumentTypeError(
                f"Invalid anchor '{token}'. Use multiple:percentile, e.g. 159.29:80."
            )
        pe_str, pct_str = token.split(":", 1)
        anchors.append((float(pe_str), float(pct_str)))
    if len(anchors) < 2:
        raise argparse.ArgumentTypeError("Need at least two anchors for interpolation.")
    return sorted(anchors, key=lambda item: item[0])


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


def interp_percentile(value: float, anchors: list[tuple[float, float]]) -> float:
    """Piecewise-linear percentile from ascending (multiple, percentile) anchors."""
    xs = [item[0] for item in anchors]
    ys = [item[1] for item in anchors]
    if value <= xs[0]:
        return ys[0]
    if value >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if value <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y1
            return y0 + (value - x0) / (x1 - x0) * (y1 - y0)
    return ys[-1]


def empirical_percentile(value: float, series: list[float]) -> float:
    """Weak percentile rank: share of observations <= value."""
    count = sum(1 for item in series if item <= value)
    return count / len(series) * 100.0


def percentile_for(
    value: float,
    anchors: list[tuple[float, float]] | None,
    series: list[float] | None,
) -> float | None:
    if series is not None:
        return empirical_percentile(value, series)
    if anchors is not None:
        return interp_percentile(value, anchors)
    return None


def move_label(move: float, report_date: date) -> str:
    if abs(move) < 1e-9:
        return f"现在 {report_date.isoformat()}"
    sign = "+" if move > 0 else "−"
    return f"指数 {sign}{abs(move) * 100:.0f}%"


def build_table(
    base: float,
    moves: list[float],
    report_date: date,
    metric: str,
    window: str,
    anchors: list[tuple[float, float]] | None,
    series: list[float] | None,
    current_pct: float | None,
) -> tuple[str, float | None]:
    if current_pct is None:
        current_pct = percentile_for(base, anchors, series)

    lines = [
        f"| 情景 | {metric} | {window}分位数 | 较现在 |",
        "|:----:|:----:|:----:|:----:|",
    ]
    for move in moves:
        value = base * (1 + move)
        is_now = abs(move) < 1e-9
        pct = current_pct if is_now else percentile_for(value, anchors, series)

        label = move_label(move, report_date)
        pe_cell = f"{value:.1f}"
        if pct is None:
            pct_cell = PLACEHOLDER
            delta_cell = PLACEHOLDER
        elif is_now:
            pct_cell = f"{pct:.1f}%"
            delta_cell = "—"
        else:
            pct_cell = f"{pct:.1f}%"
            delta_cell = (
                PLACEHOLDER
                if current_pct is None
                else f"{pct - current_pct:+.1f}pt"
            )

        if is_now:
            label, pe_cell = f"**{label}**", f"**{pe_cell}**"
            if pct is not None:
                pct_cell = f"**{pct_cell}**"
        lines.append(f"| {label} | {pe_cell} | {pct_cell} | {delta_cell} |")

    return "\n".join(lines), current_pct


def percentile_method_label(
    anchors: list[tuple[float, float]] | None, series: list[float] | None
) -> str:
    if series is not None:
        return f"{len(series)} 点历史序列经验分位"
    if anchors is not None:
        return "分位锚点分段线性插值(顶/底部区间较粗略)"
    return PLACEHOLDER


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^\w一-鿿.-]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-._")
    return value or "index"


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


def render_template(
    template_text: str,
    *,
    index_name: str,
    code: str,
    source: str,
    metric: str,
    window: str,
    report_date: date,
    base: float,
    current_pct: float | None,
    table: str,
    method_label: str,
) -> str:
    current_pct_text = PLACEHOLDER if current_pct is None else f"{current_pct:.1f}%"
    replacements = {
        "{{指数名}}": index_name,
        "{{代码}}": code or "—",
        "{{数据源}}": source,
        "{{指标}}": metric,
        "{{窗口}}": window,
        "{{分析日期}}": report_date.isoformat(),
        "{{分析日期中文}}": report_date.strftime("%Y年%m月%d日"),
        "{{基准值}}": f"{base:.1f}",
        "{{当前分位}}": current_pct_text,
        "{{分位方法}}": method_label,
        "{{敏感性表格}}": table,
    }
    rendered = template_text
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered


def create_report(
    *,
    index_name: str,
    code: str,
    source: str,
    metric: str,
    window: str,
    base: float,
    moves: list[float],
    report_date: date,
    output_dir: Path,
    template_path: Path,
    anchors: list[tuple[float, float]] | None = None,
    series: list[float] | None = None,
    current_pct: float | None = None,
) -> Path:
    index_name = index_name.strip()
    if not index_name:
        raise ValueError("Index name cannot be empty.")
    if base <= 0:
        raise ValueError("Base multiple must be positive.")
    if not moves:
        raise ValueError("Need at least one price move.")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    table, resolved_pct = build_table(
        base=base,
        moves=moves,
        report_date=report_date,
        metric=metric,
        window=window,
        anchors=anchors,
        series=series,
        current_pct=current_pct,
    )
    report_body = render_template(
        template_path.read_text(encoding="utf-8"),
        index_name=index_name,
        code=code.strip(),
        source=source.strip(),
        metric=metric.strip(),
        window=window.strip(),
        report_date=report_date,
        base=base,
        current_pct=resolved_pct,
        table=table,
        method_label=percentile_method_label(anchors, series),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(code or index_name)
    filename = f"index-pe-sensitivity-{slug}-{report_date.isoformat()}.md"
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an index valuation price-sensitivity Markdown report."
    )
    parser.add_argument("--index", required=True, help="Index display name, e.g. 科创50 or 纳斯达克100.")
    parser.add_argument("--code", default="", help="Index code, e.g. 000688 or NDX.")
    parser.add_argument("--base", required=True, type=float, help="Current valuation multiple (整体法).")
    parser.add_argument("--metric", default=DEFAULT_METRIC, help=f"Multiple label. Default: {DEFAULT_METRIC}.")
    parser.add_argument("--window", default=DEFAULT_WINDOW, help=f"Percentile window label. Default: {DEFAULT_WINDOW}.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help=f"Data source/caliber label. Default: {DEFAULT_SOURCE}.")
    parser.add_argument("--moves", default=DEFAULT_MOVES, type=parse_moves, help=f"Comma list of fractional price moves. Default: {DEFAULT_MOVES}.")
    parser.add_argument("--anchors", default="", help='Percentile anchors "multiple:pct,...", e.g. "36.31:0,83.91:50,263.72:100".')
    parser.add_argument("--series-file", default="", help="Path to a historical value series (one number per line) for empirical percentiles.")
    parser.add_argument("--current-percentile", default=None, type=float, help="Override current percentile (e.g. vendor-reported).")
    parser.add_argument("--date", type=parse_date, default=date.today(), help="Analysis date YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--output-dir", default="./output/index-pe-sensitivity", help="Output directory for the report.")
    parser.add_argument("--template", default="", help="Optional custom template path.")
    args = parser.parse_args()

    anchors = parse_anchors(args.anchors) if args.anchors else None
    series = load_series(Path(args.series_file).expanduser().resolve()) if args.series_file else None

    script_dir = Path(__file__).resolve().parent
    default_template = script_dir.parent / "references" / "report-template.md"
    template_path = Path(args.template).expanduser().resolve() if args.template else default_template

    output_path = create_report(
        index_name=args.index,
        code=args.code,
        source=args.source,
        metric=args.metric,
        window=args.window,
        base=args.base,
        moves=args.moves,
        report_date=args.date,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        template_path=template_path,
        anchors=anchors,
        series=series,
        current_pct=args.current_percentile,
    )
    print(output_path)


if __name__ == "__main__":
    main()
