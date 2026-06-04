#!/usr/bin/env python3
"""Generate an index page for Markdown reports under output/."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"
INDEX_FILENAME = "index.md"
ISO_DATE_RE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
COMPACT_DATE_RE = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")


class ReportEntry(NamedTuple):
    category: str
    date_text: str
    title: str
    relative_link: str
    relative_path: str


def parse_report_date(path: Path) -> str:
    stem = path.stem

    iso_matches = list(ISO_DATE_RE.finditer(stem))
    if iso_matches:
        return iso_matches[-1].group(1)

    compact_matches = list(COMPACT_DATE_RE.finditer(stem))
    if compact_matches:
        match = compact_matches[-1]
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return ""


def extract_title(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if stripped.startswith("# ") and len(stripped) > 2:
                    return stripped[2:].strip()
    except UnicodeDecodeError:
        return path.stem

    return path.stem


def markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def markdown_link_path(path: Path) -> str:
    return "./" + path.as_posix().replace(" ", "%20")


def collect_reports(output_dir: Path) -> list[ReportEntry]:
    reports: list[ReportEntry] = []
    index_path = (output_dir / INDEX_FILENAME).resolve()

    for path in sorted(output_dir.rglob("*.md")):
        if path.resolve() == index_path:
            continue
        if not path.is_file():
            continue

        relative_path = path.relative_to(output_dir)
        parts = relative_path.parts
        category = parts[0] if len(parts) > 1 else "root"
        reports.append(
            ReportEntry(
                category=category,
                date_text=parse_report_date(path),
                title=extract_title(path),
                relative_link=markdown_link_path(relative_path),
                relative_path=relative_path.as_posix(),
            )
        )

    return reports


def render_index(reports: list[ReportEntry]) -> str:
    lines = [
        "# Output 报告索引",
        "",
        "按 `output/` 一级目录分类，分类内按报告日期升序排列。",
        "",
    ]

    if not reports:
        lines.extend(["暂无 Markdown 报告。", ""])
        return "\n".join(lines)

    categories = sorted({report.category for report in reports})
    for category in categories:
        category_reports = sorted(
            (report for report in reports if report.category == category),
            key=lambda report: (report.date_text, report.relative_path),
        )
        lines.extend(
            [
                f"## {category}",
                "",
                "| 日期 | 标题 | 原文链接 |",
                "|---|---|---|",
            ]
        )
        for report in category_reports:
            lines.append(
                "| {date} | {title} | [原文]({link}) |".format(
                    date=markdown_table_cell(report.date_text),
                    title=markdown_table_cell(report.title),
                    link=report.relative_link,
                )
            )
        lines.append("")

    return "\n".join(lines)


def generate_index(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        raise SystemExit(f"Output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise SystemExit(f"Output path is not a directory: {output_dir}")

    index_path = output_dir / INDEX_FILENAME
    content = render_index(collect_reports(output_dir))
    index_path.write_text(content, encoding="utf-8")
    return index_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or update output/index.md from Markdown reports."
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory to scan for Markdown reports.",
    )
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the generated index path after writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_path = generate_index(output_dir=Path(args.output_dir))
    if args.print_path:
        print(index_path)
    else:
        print(f"Updated report index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
