"""Package-level contract tests for invest-flow plugin packaging."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = PROJECT_ROOT / "plugins" / "invest-flow"
SKILLS_ROOT = PLUGIN_ROOT / "skills"

ALLOWED_LEGACY_REFS = {
    "plugins/invest-flow/skills/output-report-index/scripts/generate_index.py": {
        "chain-alpha-mismatch-discovery",
        "chain-alpha-monopoly-screen",
        "chain-alpha-pipeline",
        "company-valuation-risk",
    },
    "plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py": {
        "chain-alpha-mismatch-discovery",
        "chain-alpha-monopoly-screen",
        "chain-alpha-pipeline",
        "company-valuation-risk",
    },
}

LEGACY_SKILL_IDS = {
    "chain-alpha-pipeline",
    "chain-alpha-mismatch-discovery",
    "chain-alpha-monopoly-screen",
    "company-valuation-risk",
}


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _extract_skill_name(skill_md_path: Path) -> str:
    content = skill_md_path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{skill_md_path} missing YAML frontmatter"
    end = content.find("\n---", 3)
    assert end != -1, f"{skill_md_path} frontmatter closing marker missing"
    frontmatter = content[3:end].splitlines()
    for raw_line in frontmatter:
        line = raw_line.strip()
        if not line.startswith("name:"):
            continue
        return line.split(":", 1)[1].strip().strip('"').strip("'")
    raise AssertionError(f"{skill_md_path} has no frontmatter name field")


def _iter_text_paths() -> list[Path]:
    allowed_suffixes = {
        ".md",
        ".py",
        ".json",
        ".toml",
        ".yml",
        ".yaml",
        ".txt",
        ".ini",
    }
    skip_dirs = {".git", ".venv", "output", "__pycache__"}
    paths: list[Path] = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in skip_dirs):
            continue
        if path.suffix.lower() not in allowed_suffixes and not path.name.endswith(".md"):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        paths.append(path)

    return paths


class PackageContractTests(unittest.TestCase):
    def test_skill_directory_frontmatter_names_match(self) -> None:
        for skill_dir in sorted(
            [path for path in SKILLS_ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()],
            key=lambda p: p.name,
        ):
            with self.subTest(skill_dir=skill_dir.name):
                skill_name = _extract_skill_name(skill_dir / "SKILL.md")
                self.assertEqual(skill_name, skill_dir.name)

    def test_skill_names_follow_category_contract(self) -> None:
        for skill_dir in sorted(
            [path for path in SKILLS_ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()],
            key=lambda p: p.name,
        ):
            with self.subTest(skill_dir=skill_dir.name):
                skill_name = skill_dir.name
                self.assertTrue(
                    skill_name in {"chain-alpha", "market-data-router", "output-report-index"}
                    or skill_name.startswith("chain-alpha-")
                    or skill_name.startswith("monitor-")
                    or skill_name.startswith("research-"),
                    f"Unexpected legacy/unmapped skill name: {skill_name}",
                )

    def test_manifests_keep_version_and_paths_in_sync(self) -> None:
        codex_manifest = _load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
        claude_manifest = _load_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
        codex_market = _load_json(PROJECT_ROOT / ".agents" / "plugins" / "marketplace.json")
        claude_market = _load_json(PROJECT_ROOT / ".claude-plugin" / "marketplace.json")

        self.assertEqual(codex_manifest["name"], "invest-flow")
        self.assertEqual(codex_manifest["name"], claude_manifest["name"])
        self.assertEqual(codex_manifest["version"], claude_manifest["version"])
        self.assertEqual(codex_manifest["skills"], "./skills/")

        codex_plugin = codex_market["plugins"][0]
        claude_plugin = claude_market["plugins"][0]
        self.assertEqual(codex_plugin["name"], codex_manifest["name"])
        self.assertEqual(claude_plugin["name"], claude_manifest["name"])
        self.assertEqual(codex_plugin["source"]["path"], "./plugins/invest-flow")
        self.assertEqual(claude_plugin["source"], "./plugins/invest-flow")
        self.assertEqual(claude_market["metadata"]["description"], "Repo-local marketplace for InvestFlow with the canonical Chain Alpha workflow.")

    def test_no_legacy_skill_ids_outside_compatibility_holes(self) -> None:
        legacy_hits: set[tuple[str, str]] = set()
        for path in _iter_text_paths():
            rel_path = path.relative_to(PROJECT_ROOT).as_posix()
            content = path.read_text(encoding="utf-8")
            for legacy_id in LEGACY_SKILL_IDS:
                if legacy_id not in content:
                    continue
                allowed = ALLOWED_LEGACY_REFS.get(rel_path, set())
                if legacy_id not in allowed:
                    legacy_hits.add((rel_path, legacy_id))

        self.assertFalse(
            legacy_hits,
            "Legacy skill IDs found outside explicit compatibility references: "
            + ", ".join(sorted(f"{path}:{legacy}" for path, legacy in legacy_hits)),
        )
