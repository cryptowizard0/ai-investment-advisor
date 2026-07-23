#!/usr/bin/env python3
"""Generate an earnings report analysis skeleton from the skill template."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


DEFAULT_AUTHOR = "InvestmentFlow"


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


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


def sanitize_for_filename(value: str, fallback: str) -> str:
    safe_chars = []
    for char in value.strip():
        if char.isalnum() or char in "._-":
            safe_chars.append(char)
        else:
            safe_chars.append("-")

    safe = re.sub(r"-+", "-", "".join(safe_chars)).strip(".-_")
    return safe or fallback


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
    period: str,
    exchange: str,
    currency: str,
    report_date: date,
) -> str:
    replacements = {
        "{{作者}}": DEFAULT_AUTHOR,
        "{{公司名}}": company,
        "{{Ticker}}": ticker,
        "{{财报周期}}": period,
        "{{交易所}}": exchange,
        "{{币种}}": currency,
        "{{YYYY年MM月DD日}}": report_date.strftime("%Y年%m月%d日"),
        "{{YYYY-MM-DD}}": report_date.isoformat(),
    }

    rendered = template_text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def create_report(
    ticker: str,
    company: str,
    period: str,
    exchange: str,
    currency: str,
    report_date: date,
    output_dir: Path,
    template_path: Path,
) -> Path:
    if not company.strip():
        company = ticker
    if not period.strip():
        period = "latest"
    if not exchange.strip():
        exchange = "不确定"
    if not currency.strip():
        currency = "不确定"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    report_body = render_template(
        template_text=template_text,
        ticker=ticker,
        company=company.strip(),
        period=period.strip(),
        exchange=exchange.strip(),
        currency=currency.strip(),
        report_date=report_date,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = sanitize_for_filename(ticker, "UNKNOWN")
    safe_period = sanitize_for_filename(period, "latest")
    filename = (
        f"research-earnings-{safe_ticker}-{safe_period}-"
        f"{report_date.isoformat()}.md"
    )
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an earnings report analysis markdown skeleton."
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
        "--period",
        default="latest",
        help='Fiscal period, e.g. "FY2026 Q1". Defaults to latest.',
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
        default="./output/research-earnings",
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
    output_path = create_report(
        ticker=args.ticker,
        company=args.company,
        period=args.period,
        exchange=args.exchange,
        currency=args.currency,
        report_date=args.date,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        template_path=template_path,
    )

    print(output_path)


if __name__ == "__main__":
    main()
