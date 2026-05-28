#!/usr/bin/env python3
"""Generate a non-consensus company discovery report skeleton."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path


DEFAULT_MARKET = "US-listed equities/ADRs"
DEFAULT_AUTHOR = "InvestmentFlow"


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def validate_top_n(value: str) -> int:
    try:
        top_n = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Top N must be an integer.") from exc

    if top_n < 1 or top_n > 10:
        raise argparse.ArgumentTypeError("Top N must be between 1 and 10.")
    return top_n


def sanitize_theme_for_filename(theme: str) -> str:
    safe_chars = []
    for char in theme.strip():
        if char.isalnum() or char in "._-":
            safe_chars.append(char)
        else:
            safe_chars.append("-")

    safe = re.sub(r"-+", "-", "".join(safe_chars)).strip(".-_")
    return safe or "theme"


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
    theme: str,
    market: str,
    top_n: int,
    report_date: date,
) -> str:
    replacements = {
        "{{主题}}": theme,
        "{{作者}}": DEFAULT_AUTHOR,
        "{{YYYY年MM月DD日}}": report_date.strftime("%Y年%m月%d日"),
        "{{YYYY-MM-DD}}": report_date.isoformat(),
        "{{市场}}": market,
        "{{TopN}}": str(top_n),
    }

    rendered = template_text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def create_report(
    theme: str,
    market: str,
    top_n: int,
    report_date: date,
    output_dir: Path,
    template_path: Path,
) -> Path:
    if not theme.strip():
        raise ValueError("Theme cannot be empty.")
    if not market.strip():
        raise ValueError("Market cannot be empty.")
    if top_n < 1 or top_n > 10:
        raise ValueError("Top N must be between 1 and 10.")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    report_body = render_template(
        template_text=template_text,
        theme=theme.strip(),
        market=market.strip(),
        top_n=top_n,
        report_date=report_date,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_theme = sanitize_theme_for_filename(theme)
    filename = (
        f"non-consensus-company-discovery-{safe_theme}-{report_date.isoformat()}.md"
    )
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(report_body, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a non-consensus company discovery markdown skeleton."
    )
    parser.add_argument(
        "--theme",
        required=True,
        help='Theme or trend to analyze, e.g. "AI 数据中心电力".',
    )
    parser.add_argument(
        "--market",
        default=DEFAULT_MARKET,
        help=f"Candidate universe. Defaults to {DEFAULT_MARKET}.",
    )
    parser.add_argument(
        "--top-n",
        type=validate_top_n,
        default=3,
        help="Number of top companies to track in the final report. Defaults to 3.",
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        help="Analysis date in YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--output-dir",
        default="./output/non-consensus-company-discovery",
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
        theme=args.theme,
        market=args.market,
        top_n=args.top_n,
        report_date=args.date,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        template_path=template_path,
    )

    print(output_path)


if __name__ == "__main__":
    main()
