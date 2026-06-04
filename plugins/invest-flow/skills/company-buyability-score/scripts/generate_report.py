#!/usr/bin/env python3
"""Generate a company buyability score report skeleton."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


DEFAULT_AUTHOR = "InvestmentFlow"
DEFAULT_MARKET = "US-listed equities/ADRs"
DEFAULT_HORIZON = "6-24 个月"


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def normalize_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker:
        raise ValueError("Ticker cannot be empty.")
    if len(ticker) > 24:
        raise ValueError("Ticker is too long. Max length is 24.")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-=/]*", ticker):
        raise ValueError("Invalid ticker format. Allowed: letters, numbers, ., -, =, /.")
    return ticker


def validate_ticker(value: str) -> str:
    try:
        return normalize_ticker(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def sanitize_ticker_for_filename(ticker: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", ticker)
    safe = safe.strip(".-_")
    return safe or "UNKNOWN"


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


def render_template(
    template_text: str,
    ticker: str,
    company: str,
    exchange: str,
    currency: str,
    report_date: date,
) -> str:
    replacements = {
        "{{公司名}}": company,
        "{{Ticker}}": ticker,
        "{{作者}}": DEFAULT_AUTHOR,
        "{{YYYY年MM月DD日}}": report_date.strftime("%Y年%m月%d日"),
        "{{YYYY-MM-DD}}": report_date.isoformat(),
        "{{交易所}}": exchange,
        "{{币种}}": currency,
        "{{默认市场}}": DEFAULT_MARKET,
        "{{投资周期}}": DEFAULT_HORIZON,
    }

    rendered = template_text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def create_report(
    ticker: str,
    company: str,
    exchange: str,
    currency: str,
    report_date: date,
    output_dir: Path,
    template_path: Path,
) -> Path:
    ticker = normalize_ticker(ticker)
    company = company.strip()
    exchange = exchange.strip()
    currency = currency.strip()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")
    if not company:
        raise ValueError("Company cannot be empty.")
    if not exchange:
        raise ValueError("Exchange cannot be empty.")
    if not currency:
        raise ValueError("Currency cannot be empty.")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    report_body = render_template(
        template_text=template_text,
        ticker=ticker,
        company=company,
        exchange=exchange,
        currency=currency,
        report_date=report_date,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = sanitize_ticker_for_filename(ticker)
    filename = f"company-buyability-score-{safe_ticker}-{report_date.isoformat()}.md"
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a company buyability score markdown skeleton."
    )
    parser.add_argument(
        "--ticker",
        required=True,
        type=validate_ticker,
        help="Stock ticker, e.g. NVDA or BRK/B.",
    )
    parser.add_argument(
        "--company",
        default="",
        help="Company display name. Defaults to ticker when omitted.",
    )
    parser.add_argument(
        "--exchange",
        default="NASDAQ",
        help="Exchange display name. Defaults to NASDAQ.",
    )
    parser.add_argument(
        "--currency",
        default="USD",
        help="Reporting/valuation currency. Defaults to USD.",
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        help="Analysis date in YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--output-dir",
        default="./output/company-buyability-score",
        help="Output directory for the generated markdown file.",
    )
    parser.add_argument(
        "--template",
        default="",
        help="Optional custom template path. Defaults to skill references/report-template.md.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_template = script_dir.parent / "references" / "report-template.md"
    template_path = (
        Path(args.template).expanduser().resolve() if args.template else default_template
    )
    company = args.company.strip() if args.company else args.ticker
    output_path = create_report(
        ticker=args.ticker,
        company=company,
        exchange=args.exchange,
        currency=args.currency,
        report_date=args.date,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        template_path=template_path,
    )

    print(output_path)


if __name__ == "__main__":
    main()
