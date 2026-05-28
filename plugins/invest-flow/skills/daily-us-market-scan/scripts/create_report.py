#!/usr/bin/env python3
"""Create a Daily US Market Scan report skeleton."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "daily-us-market-scan"
TEMPLATE_PATH = SKILL_DIR / "references" / "report-template.md"
US_EASTERN = ZoneInfo("America/New_York")
REGULAR_MARKET_CLOSE = time(16, 0)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def nth_weekday(year: int, month: int, weekday: int, nth: int) -> date:
    current = date(year, month, 1)
    days_until_weekday = (weekday - current.weekday()) % 7
    return current + timedelta(days=days_until_weekday + (nth - 1) * 7)


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        current = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    return current - timedelta(days=(current.weekday() - weekday) % 7)


def observed_fixed_holiday(year: int, month: int, day: int) -> date:
    holiday = date(year, month, day)
    if holiday.weekday() == 5:
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)
    return holiday


def easter_date(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def us_market_holidays(year: int) -> set[date]:
    holidays = {
        observed_fixed_holiday(year, 1, 1),
        observed_fixed_holiday(year + 1, 1, 1),
        nth_weekday(year, 1, 0, 3),
        nth_weekday(year, 2, 0, 3),
        easter_date(year) - timedelta(days=2),
        last_weekday(year, 5, 0),
        observed_fixed_holiday(year, 6, 19),
        observed_fixed_holiday(year, 7, 4),
        nth_weekday(year, 9, 0, 1),
        nth_weekday(year, 11, 3, 4),
        observed_fixed_holiday(year, 12, 25),
    }
    return {holiday for holiday in holidays if holiday.year == year}


def is_us_trading_day(session_date: date) -> bool:
    if session_date.weekday() >= 5:
        return False
    return session_date not in us_market_holidays(session_date.year)


def previous_us_trading_day(session_date: date) -> date:
    current = session_date - timedelta(days=1)
    while not is_us_trading_day(current):
        current -= timedelta(days=1)
    return current


def latest_completed_us_session(now: datetime | None = None) -> date:
    current = now or datetime.now(US_EASTERN)
    if current.tzinfo is None:
        current = current.astimezone()
    eastern_now = current.astimezone(US_EASTERN)
    candidate = eastern_now.date()

    if is_us_trading_day(candidate) and eastern_now.time() >= REGULAR_MARKET_CLOSE:
        return candidate
    return previous_us_trading_day(candidate)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Chinese Daily US Market Scan report skeleton."
    )
    parser.add_argument(
        "--date",
        default=latest_completed_us_session().isoformat(),
        help="US market session date for the report, format YYYY-MM-DD.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated reports.",
    )
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the generated path after writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Invalid --date {args.date!r}; expected YYYY-MM-DD.") from exc

    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found: {TEMPLATE_PATH}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"us-market-close-daily-{report_date.isoformat()}.md"
    output_path = unique_path(output_dir / filename)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    content = content.replace("{REPORT_DATE}", report_date.isoformat())
    content = content.replace("{GENERATED_AT}", generated_at)

    output_path.write_text(content, encoding="utf-8")

    if args.print_path:
        print(output_path)
    else:
        print(f"Created report skeleton: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
