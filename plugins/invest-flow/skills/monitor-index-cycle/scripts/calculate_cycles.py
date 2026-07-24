#!/usr/bin/env python3
"""Detect index bull and bear cycles from daily closing prices."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence


DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y")


@dataclass(frozen=True)
class PricePoint:
    date: date
    close: float


@dataclass(frozen=True)
class Cycle:
    kind: str
    start_date: date
    end_date: date
    start_close: float
    end_close: float
    duration_days: int
    return_pct: float
    status: str
    confirmed_date: date | None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "start_close": round(self.start_close, 8),
            "end_close": round(self.end_close, 8),
            "duration_days": self.duration_days,
            "return_pct": round(self.return_pct, 8),
            "status": self.status,
            "confirmed_date": (
                self.confirmed_date.isoformat() if self.confirmed_date else None
            ),
        }


def parse_date(value: str) -> date:
    cleaned = value.strip()
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported date: {value!r}")


def _resolve_column(fieldnames: Sequence[str], requested: str) -> str:
    normalized = {name.strip().casefold(): name for name in fieldnames}
    resolved = normalized.get(requested.strip().casefold())
    if resolved is None:
        raise ValueError(
            f"missing column {requested!r}; available columns: {', '.join(fieldnames)}"
        )
    return resolved


def load_prices(
    path: Path,
    date_column: str = "date",
    close_column: str = "close",
    as_of: date | None = None,
) -> list[PricePoint]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("price CSV has no header")
        date_key = _resolve_column(reader.fieldnames, date_column)
        close_key = _resolve_column(reader.fieldnames, close_column)
        points: list[PricePoint] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                point_date = parse_date(row[date_key])
                close = float(row[close_key].strip().replace(",", "").replace("$", ""))
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid price row {line_number}: {exc}") from exc
            if close <= 0:
                raise ValueError(f"invalid non-positive close on {point_date}: {close}")
            if as_of is None or point_date <= as_of:
                points.append(PricePoint(point_date, close))

    points.sort(key=lambda point: point.date)
    if len(points) < 2:
        raise ValueError("at least two price rows are required")
    for previous, current in zip(points, points[1:]):
        if previous.date == current.date:
            raise ValueError(f"duplicate price date: {current.date}")
    return points


def _make_cycle(
    kind: str,
    start: PricePoint,
    end: PricePoint,
    status: str,
    confirmed_date: date | None,
) -> Cycle:
    return Cycle(
        kind=kind,
        start_date=start.date,
        end_date=end.date,
        start_close=start.close,
        end_close=end.close,
        duration_days=(end.date - start.date).days,
        return_pct=(end.close / start.close - 1.0) * 100.0,
        status=status,
        confirmed_date=confirmed_date,
    )


def detect_cycles(
    points: Iterable[PricePoint],
    threshold: float = 0.20,
    seed_kind: str = "auto",
) -> list[Cycle]:
    ordered = sorted(points, key=lambda point: point.date)
    if len(ordered) < 2:
        raise ValueError("at least two price points are required")
    if not 0 < threshold < 1:
        raise ValueError("threshold must be between 0 and 1")
    if seed_kind not in {"auto", "bull", "bear"}:
        raise ValueError("seed_kind must be auto, bull, or bear")

    state: str | None = None if seed_kind == "auto" else seed_kind
    start = ordered[0]
    extreme = ordered[0]
    running_high = ordered[0]
    running_low = ordered[0]
    state_confirmed_date: date | None = None
    cycles: list[Cycle] = []

    for point in ordered[1:]:
        if state is None:
            if point.close > running_high.close:
                running_high = point
            if point.close < running_low.close:
                running_low = point

            if point.close <= running_high.close * (1.0 - threshold):
                state = "bear"
                start = running_high
                extreme = point
                state_confirmed_date = point.date
            elif point.close >= running_low.close * (1.0 + threshold):
                state = "bull"
                start = running_low
                extreme = point
                state_confirmed_date = point.date
            continue

        if state == "bull":
            if point.close > extreme.close:
                extreme = point
            if point.close <= extreme.close * (1.0 - threshold):
                cycles.append(
                    _make_cycle("bull", start, extreme, "completed", point.date)
                )
                state = "bear"
                start = extreme
                extreme = point
                state_confirmed_date = point.date
        else:
            if point.close < extreme.close:
                extreme = point
            if point.close >= extreme.close * (1.0 + threshold):
                cycles.append(
                    _make_cycle("bear", start, extreme, "completed", point.date)
                )
                state = "bull"
                start = extreme
                extreme = point
                state_confirmed_date = point.date

    if state is not None:
        cycles.append(
            _make_cycle(state, start, extreme, "ongoing", state_confirmed_date)
        )
    return cycles


def render_markdown(cycles: Sequence[Cycle]) -> str:
    lines = [
        "| 周期 | 起始日 | 峰/谷日 | 持续天数 | 幅度 | 状态 | 确认日 |",
        "|:--:|:--:|:--:|--:|--:|:--:|:--:|",
    ]
    labels = {"bull": "牛市", "bear": "熊市"}
    statuses = {"completed": "已完成", "ongoing": "进行中"}
    for cycle in cycles:
        confirmed = cycle.confirmed_date.isoformat() if cycle.confirmed_date else "—"
        lines.append(
            f"| {labels[cycle.kind]} | {cycle.start_date.isoformat()} | "
            f"{cycle.end_date.isoformat()} | {cycle.duration_days} | "
            f"{cycle.return_pct:+.2f}% | {statuses[cycle.status]} | {confirmed} |"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect bull/bear cycles from a daily index close CSV."
    )
    parser.add_argument("--prices-file", type=Path, required=True)
    parser.add_argument("--date-column", default="date")
    parser.add_argument("--close-column", default="close")
    parser.add_argument("--threshold", type=float, default=0.20)
    parser.add_argument(
        "--seed-kind", choices=("auto", "bull", "bear"), default="auto"
    )
    parser.add_argument("--as-of", type=parse_date)
    parser.add_argument("--kind", choices=("all", "bull", "bear"), default="all")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    prices = load_prices(
        args.prices_file,
        date_column=args.date_column,
        close_column=args.close_column,
        as_of=args.as_of,
    )
    cycles = detect_cycles(prices, threshold=args.threshold, seed_kind=args.seed_kind)
    if args.kind != "all":
        cycles = [cycle for cycle in cycles if cycle.kind == args.kind]
    if args.format == "markdown":
        print(render_markdown(cycles))
    else:
        print(json.dumps([cycle.to_dict() for cycle in cycles], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
