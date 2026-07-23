#!/usr/bin/env python3
"""Save a reflexivity analysis markdown report (quick or deep) with stable naming."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path


DEFAULT_OUTPUT_DIR = "./output/research-reflexivity"


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc


def sanitize_topic(topic: str) -> str:
    cleaned = re.sub(r"\s+", "-", topic.strip())
    cleaned = re.sub(r"[\\\\/:*?\"<>|]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip(".-")
    return cleaned or "untitled-topic"


def find_unique_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    while True:
        candidate = base_path.with_name(f"{stem}({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def build_default_content(topic: str, report_date: date, template_text: str) -> str:
    """Fill a blank template: known slots first, then every remaining {{...}} -> 待填写.

    This is mode-agnostic, so the quick and deep templates share one code path.
    """
    special = {
        "{{主题}}": topic,
        "{{分析日期}}": report_date.isoformat(),
        "{{信息缺口与待验证点}}": "- 待填写",
        "{{数据来源与观察依据}}": "- 待填写",
    }
    rendered = template_text
    for placeholder, value in special.items():
        rendered = rendered.replace(placeholder, value)
    return re.sub(r"\{\{[^}]+\}\}", "待填写", rendered)


def read_content(args: argparse.Namespace, template_path: Path) -> str:
    if args.content_file:
        return Path(args.content_file).expanduser().read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        piped = sys.stdin.read()
        if piped.strip():
            return piped

    return build_default_content(
        topic=args.topic,
        report_date=args.date,
        template_text=template_path.read_text(encoding="utf-8"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Save a reflexivity analysis report to the project output directory."
    )
    parser.add_argument("--topic", required=True, help="Analysis topic, such as NVDA or 黄金.")
    parser.add_argument(
        "--mode",
        choices=("quick", "deep"),
        default="deep",
        help="Report mode: quick (5-minute scan) or deep (full cycle). Defaults to deep.",
    )
    parser.add_argument(
        "--date",
        type=parse_date,
        default=date.today(),
        help="Analysis date in YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument(
        "--content-file",
        default="",
        help="Optional path to a markdown file whose content should be saved.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Defaults to {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--template",
        default="",
        help="Optional custom report template path.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    template_name = "report-template-quick.md" if args.mode == "quick" else "report-template.md"
    default_template = script_dir.parent / "assets" / template_name
    template_path = Path(args.template).expanduser().resolve() if args.template else default_template
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    content = read_content(args, template_path)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_topic = sanitize_topic(args.topic)
    filename = f"research-reflexivity-{args.mode}-{safe_topic}-{args.date.isoformat()}.md"
    output_path = find_unique_path(output_dir / filename)
    output_path.write_text(content, encoding="utf-8")

    print(output_path)


if __name__ == "__main__":
    main()
