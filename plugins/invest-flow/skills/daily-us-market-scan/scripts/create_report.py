#!/usr/bin/env python3
"""Create a Daily US Market Scan report skeleton."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "daily-us-market-scan"
TEMPLATE_PATH = SKILL_DIR / "references" / "report-template.md"


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Chinese Daily US Market Scan report skeleton."
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
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
