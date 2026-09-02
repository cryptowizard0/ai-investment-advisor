"""Adapter around the existing report metadata extraction rules."""

from __future__ import annotations

import importlib.util
import json
import re
from json import JSONDecodeError
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, TypedDict


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
NUMBERED_REVISION_RE = re.compile(r"^(?P<base>.+)\((?P<revision>\d+)\)$")
ALIASES_PATH = Path(__file__).with_name("aliases.json")
H1_TICKER_RE = re.compile(
    r"[\(（]([A-Za-z0-9]+(?:[.-][A-Za-z]{1,2})?)[\)）]"
)
FILENAME_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:\.[A-Za-z]{1,2})?")
FALSE_TICKER_TOKENS = {"AI", "CPO", "GRID", "HBM", "TGV"}
UNKNOWN_TICKER_RE = re.compile(r"(?:[A-Z]{1,5}|\d{4,6}[A-Z]{1,2})")


class ReportMetadata(TypedDict):
    category: str
    skill: str
    date: str
    title: str
    relative_path: str
    tickers: list[str]
    themes: list[str]


def normalize_alias(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.upper())


def load_aliases() -> tuple[dict[str, str], dict[str, list[str]]]:
    try:
        aliases = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError) as error:
        raise RuntimeError(
            f"Unable to load report aliases from {ALIASES_PATH}: {error}"
        ) from error
    ticker_lookup = {
        normalize_alias(alias): canonical
        for canonical, values in aliases["tickers"].items()
        for alias in [canonical, *values]
    }
    theme_aliases = {
        canonical: [normalize_alias(alias) for alias in [canonical, *values]]
        for canonical, values in aliases["themes"].items()
    }
    return ticker_lookup, theme_aliases


def unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def extract_tickers(
    title: str,
    relative_path: str,
    ticker_lookup: dict[str, str],
) -> list[str]:
    explicit_candidates = [
        normalized
        for candidate in H1_TICKER_RE.findall(title)
        if (normalized := normalize_alias(candidate)) in ticker_lookup
        or (
            normalized not in FALSE_TICKER_TOKENS
            and UNKNOWN_TICKER_RE.fullmatch(normalized)
        )
    ]
    explicit_tickers = unique_values(
        [
            ticker_lookup[candidate]
            for candidate in explicit_candidates
            if candidate in ticker_lookup
        ]
    )
    if explicit_candidates:
        return explicit_tickers

    filename_tokens = FILENAME_TOKEN_RE.findall(
        PurePosixPath(relative_path).stem
    )
    filename_candidates = filename_tokens + [
        f"{left}-{right}"
        for left, right in zip(filename_tokens, filename_tokens[1:])
    ]
    return unique_values(
        [
            ticker_lookup[normalized]
            for candidate in filename_candidates
            if (normalized := normalize_alias(candidate)) in ticker_lookup
        ]
    )


def extract_themes(
    title: str,
    relative_path: str,
    theme_aliases: dict[str, list[str]],
) -> list[str]:
    source = normalize_alias(f"{title} {PurePosixPath(relative_path).stem}")
    return [
        canonical
        for canonical, aliases in theme_aliases.items()
        if any(alias in source for alias in aliases)
    ]


def duplicate_identity(relative_path: str) -> tuple[str, int]:
    path = PurePosixPath(relative_path)
    match = NUMBERED_REVISION_RE.fullmatch(path.stem)
    if match is None:
        return relative_path, 0

    group_path = path.with_name(f"{match.group('base')}{path.suffix}")
    return group_path.as_posix(), int(match.group("revision"))


def metadata_for_report(
    report: Any,
    ticker_lookup: dict[str, str],
    theme_aliases: dict[str, list[str]],
) -> ReportMetadata:
    return {
        "category": report.category,
        "skill": report.skill,
        "date": report.date_text,
        "title": report.title,
        "relative_path": report.relative_path,
        "tickers": extract_tickers(
            report.title,
            report.relative_path,
            ticker_lookup,
        ),
        "themes": extract_themes(
            report.title,
            report.relative_path,
            theme_aliases,
        ),
    }


def collect_report_metadata(output_dir: Path) -> list[ReportMetadata]:
    ticker_lookup, theme_aliases = load_aliases()
    return [
        metadata_for_report(report, ticker_lookup, theme_aliases)
        for report in INDEX_GENERATOR.collect_reports(output_dir)
    ]


def collect_report_paths(output_dir: Path) -> list[str]:
    paths: list[str] = []
    resolved_output_dir = output_dir.resolve()
    for directory in sorted(INDEX_GENERATOR.TOPIC_CATEGORIES):
        topic_dir = output_dir / directory
        if not topic_dir.is_dir():
            continue
        for path in sorted(topic_dir.rglob("*.md")):
            if not path.is_file():
                continue
            try:
                path.resolve().relative_to(resolved_output_dir)
            except (OSError, ValueError):
                continue
            paths.append(path.relative_to(output_dir).as_posix())
    return paths


def report_relative_path(output_dir: Path, path: Path) -> str | None:
    try:
        relative_path = path.resolve().relative_to(output_dir.resolve())
    except ValueError:
        return None
    if (
        len(relative_path.parts) < 2
        or relative_path.parts[0] not in INDEX_GENERATOR.TOPIC_CATEGORIES
        or relative_path.suffix != ".md"
    ):
        return None
    return relative_path.as_posix()


def collect_report_metadata_for_path(
    output_dir: Path,
    path: Path,
    *,
    title: str | None = None,
) -> ReportMetadata | None:
    relative_path = report_relative_path(output_dir, path)
    if relative_path is None or not path.is_file():
        return None

    ticker_lookup, theme_aliases = load_aliases()
    category = INDEX_GENERATOR.normalize_report_category(
        Path(relative_path).parts[0]
    )
    report = INDEX_GENERATOR.ReportEntry(
        category=category,
        skill=INDEX_GENERATOR.infer_report_skill(path.stem),
        date_text=INDEX_GENERATOR.parse_report_date(path),
        title=(
            title
            if title is not None
            else INDEX_GENERATOR.extract_title(path)
        ),
        relative_link=INDEX_GENERATOR.markdown_link_path(Path(relative_path)),
        relative_path=relative_path,
    )
    return metadata_for_report(report, ticker_lookup, theme_aliases)
