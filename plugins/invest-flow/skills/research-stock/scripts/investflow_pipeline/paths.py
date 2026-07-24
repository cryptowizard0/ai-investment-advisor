from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional


def _is_project_root(candidate: Path) -> bool:
    if not (candidate / "AGENTS.md").exists():
        return False
    plugin_dir = candidate / "plugins" / "invest-flow"
    manifests = (
        plugin_dir / ".codex-plugin" / "plugin.json",
        plugin_dir / ".claude-plugin" / "plugin.json",
    )
    return any(manifest.is_file() for manifest in manifests)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def find_project_root(start: Optional[Path] = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    candidates: Iterable[Path] = [current, *current.parents]
    for candidate in candidates:
        if _is_project_root(candidate):
            return candidate

    cwd = Path.cwd().resolve()
    if _is_project_root(cwd):
        return cwd
    raise RuntimeError("Unable to locate InvestFlow project root")


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
    root = project_root.resolve()
    output_dir = (root / relative_dir).resolve()
    if not _is_relative_to(output_dir, root):
        raise ValueError(f"Output directory escapes project root: {relative_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
