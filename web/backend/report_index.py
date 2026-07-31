"""Adapter around the existing report metadata extraction rules."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_GENERATOR_PATH = (
    REPO_ROOT
    / "plugins"
    / "invest-flow"
    / "skills"
    / "output-report-index"
    / "scripts"
    / "generate_index.py"
)


def load_index_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "invest_flow_output_index",
        INDEX_GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load report index rules: {INDEX_GENERATOR_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INDEX_GENERATOR = load_index_generator()


def collect_report_metadata(output_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "category": report.category,
            "skill": report.skill,
            "date": report.date_text,
            "title": report.title,
            "relative_path": report.relative_path,
        }
        for report in INDEX_GENERATOR.collect_reports(output_dir)
    ]
