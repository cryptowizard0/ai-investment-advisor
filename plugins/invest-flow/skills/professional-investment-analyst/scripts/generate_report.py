#!/usr/bin/env python3
"""Generate a professional investment analyst report skeleton from the skill template."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def find_unique_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    index = 1

    while True:
        candidate = parent / f"{stem}({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def sanitize_ticker_for_filename(ticker: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", ticker)
    safe = safe.strip(".-_")
    return safe or "UNKNOWN"


def validate_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker:
        raise argparse.ArgumentTypeError("Ticker cannot be empty.")
    if len(ticker) > 24:
        raise argparse.ArgumentTypeError("Ticker is too long. Max length is 24.")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-=/]*", ticker):
        raise argparse.ArgumentTypeError(
            "Invalid ticker format. Allowed: letters, numbers, ., -, =, /."
        )
    return ticker


def render_template(
    template_text: str,
    ticker: str,
    company: str,
    exchange: str,
    currency: str,
    report_date: date,
) -> str:
    fiscal_year = report_date.year - 1
    replacements = {
        "{{公司名}}": company,
        "{{Ticker}}": ticker,
        "{{交易所}}": exchange,
        "{{币种}}": currency,
        "{{YYYY年MM月DD日}}": report_date.strftime("%Y年%m月%d日"),
        "{{财报年份}}": str(fiscal_year),
        "{{财报年份-1}}": str(fiscal_year - 1),
        "{{财报年份-2}}": str(fiscal_year - 2),
        "{{财报年份-3}}": str(fiscal_year - 3),
        "{{财报年份-4}}": str(fiscal_year - 4),
    }

    rendered = template_text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a professional investment research markdown skeleton."
    )
    parser.add_argument(
        "--ticker",
        required=True,
        type=validate_ticker,
        help="Stock ticker, e.g. TSLA or BRK/B.",
    )
    parser.add_argument(
        "--company",
        default="",
        help="Company display name. Defaults to ticker when omitted.",
    )
    parser.add_argument(
        "--exchange",
        default="不确定",
        help="Exchange display name. Defaults to 不确定.",
    )
    parser.add_argument(
        "--currency",
        default="不确定",
        help="Reporting/valuation currency. Defaults to 不确定.",
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        help="Analysis date in YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--output-dir",
        default="./output/professional-investment-analyst",
        help="Output directory for the generated markdown file.",
    )
    parser.add_argument(
        "--template",
        default="",
        help="Optional custom template path. Defaults to skill references/report-template.md.",
    )
    args = parser.parse_args()

    ticker = args.ticker
    company = args.company.strip() if args.company else ticker
    safe_ticker = sanitize_ticker_for_filename(ticker)

    script_dir = Path(__file__).resolve().parent
    default_template = script_dir.parent / "references" / "report-template.md"
    template_path = (
        Path(args.template).expanduser().resolve() if args.template else default_template
    )

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    report_body = render_template(
        template_text=template_text,
        ticker=ticker,
        company=company,
        exchange=args.exchange,
        currency=args.currency,
        report_date=args.date,
    )

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"professional-investment-analyst-{safe_ticker}-{args.date.isoformat()}.md"
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")

    print(output_path)


if __name__ == "__main__":
    main()
