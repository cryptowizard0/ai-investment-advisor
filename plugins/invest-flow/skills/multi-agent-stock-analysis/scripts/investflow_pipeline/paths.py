from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


def find_project_root(start: Optional[Path] = None) -> Path:
    current = (start or Path(__file__)).resolve()
    candidates: Iterable[Path] = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "AGENTS.md").exists():
            return candidate
    return Path.cwd().resolve()


def safe_read_text(file_path: Path) -> str:
    if not file_path.exists() or not file_path.is_file():
        return ""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def ensure_output_dir(project_root: Path, relative_dir: str) -> Path:
    output_dir = (project_root / relative_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def find_report_from_output(project_root: Path, command_output: str) -> Optional[Path]:
    if not command_output:
        return None
    patterns = [
        r"([./\w\-\u4e00-\u9fff()]+/output/[^\s\"'`]+\.md)",
        r"(\.?/output/[^\s\"'`]+\.md)",
        r"(/[^ \n\t\"'`]+\.md)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, command_output):
            path = Path(match)
            if not path.is_absolute():
                path = (project_root / path).resolve()
            if path.exists() and path.is_file():
                return path
    return None


def find_latest_report(output_dir: Path, ticker: str, started_at: datetime) -> Optional[Path]:
    if not output_dir.exists():
        return None
    ticker_upper = ticker.upper()
    threshold_ts = started_at.timestamp() - 5
    candidates = [
        path
        for path in output_dir.glob("*.md")
        if path.is_file()
        and ticker_upper in path.name.upper()
        and path.stat().st_mtime >= threshold_ts
    ]
    if not candidates:
        candidates = [
            path
            for path in output_dir.glob("*.md")
            if path.is_file() and path.stat().st_mtime >= threshold_ts
        ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)
