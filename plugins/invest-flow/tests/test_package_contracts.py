"""Package-level contract tests for invest-flow plugin packaging."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = PROJECT_ROOT / "plugins" / "invest-flow"
SKILLS_ROOT = PLUGIN_ROOT / "skills"

EXPECTED_SKILLS = {
    "chain-alpha",
    "chain-alpha-position-plan",
    "chain-alpha-industry-analysis",
    "chain-alpha-company-discovery",
    "chain-alpha-company-verification",
    "market-data-router",
    "monitor-ai-infrastructure",
    "monitor-chain-alpha-delivery",
    "monitor-gold",
    "monitor-index-cycle",
    "monitor-index-valuation",
    "monitor-nhnl-bottom",
    "monitor-us-market",
    "output-report-index",
    "research-earnings",
    "research-fundamentals",
    "research-institutional",
    "research-profile",
    "research-reflexivity",
    "research-reportify",
    "research-stock",
}

HISTORICAL_REPORT_ALIASES = {
    "ai-infrastructure-scarcity-radar",
    "ai-infrastructure-sector-discovery",
    "chain-alpha-delivery-tracking",
    "chain-alpha-entry-plan",
    "chain-alpha-mismatch",
    "chain-alpha-mismatch-discovery",
    "chain-alpha-monopoly",
    "chain-alpha-monopoly-screen",
    "chain-alpha-pipeline",
    "chain-alpha-verification",
    "company-buyability-score",
    "company-profile",
    "company-valuation-risk",
    "daily-us-market-scan",
    "earnings-report-analysis",
    "fundamental-analysis",
    "gold-analysis",
    "index-market-cycles",
    "index-pe-sensitivity",
    "institutional-accumulation-analysis",
    "non-consensus-company-discovery",
    "reflexivity-deep-analysis",
    "reflexivity-quick-scan",
    "reportify-stock-analysis",
    "research",
}

LEGACY_SKILL_IDS = HISTORICAL_REPORT_ALIASES - {"research"}
LEGACY_INVOCATION_TOKENS = {"invest-flow:research"}

ALLOWED_LEGACY_REFS = {
    "plugins/invest-flow/skills/output-report-index/scripts/generate_index.py": HISTORICAL_REPORT_ALIASES,
    "plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py": {
        "ai-infrastructure-sector-discovery",
        "chain-alpha-entry-plan",
        "chain-alpha-mismatch",
        "chain-alpha-mismatch-discovery",
        "chain-alpha-monopoly",
        "chain-alpha-verification",
        "company-profile",
        "daily-us-market-scan",
        "fundamental-analysis",
    },
    "plugins/invest-flow/tests/test_package_contracts.py": (
        HISTORICAL_REPORT_ALIASES | LEGACY_INVOCATION_TOKENS
    ),
    "web/backend/tests/test_app.py": {"chain-alpha-pipeline"},
}

CHAIN_ALPHA_SEQUENCE = (
    "chain-alpha-industry-analysis",
    "chain-alpha-company-discovery",
    "chain-alpha-company-verification",
    "chain-alpha-position-plan",
)

CROSS_SKILL_INVOCATIONS = {
    "skills/monitor-ai-infrastructure/SKILL.md": (
        "chain-alpha-industry-analysis",
        "chain-alpha",
    ),
    "skills/monitor-chain-alpha-delivery/SKILL.md": (
        "chain-alpha-company-verification",
        "chain-alpha-position-plan",
    ),
    "skills/research-stock/scripts/investflow_pipeline/registry.py": (
        "research-profile",
        "research-fundamentals",
        "research-institutional",
        "research-reflexivity",
        "research-reportify",
    ),
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


def _skill_reference_pattern(skill_id: str) -> str:
    escaped = re.escape(skill_id)
    return rf"(?:`(?:invest-flow:)?{escaped}`|[\"']{escaped}[\"'])"


def _iter_text_paths() -> list[Path]:
    """Repository-tracked text files only.

    Enumerating via ``git ls-files`` keeps gitignored/local files out of the
    legacy-ID scan (a developer's ``.claude/settings.local.json`` permission
    allowlist, cached ``output/`` reports, leftover untracked skill
    directories), which are not part of the shipped repository.
    """
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
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AssertionError(
            f"Unable to enumerate git-tracked files for legacy-ID scan: {exc}"
        )

    paths: list[Path] = []
    for rel_path in completed.stdout.decode("utf-8").split("\0"):
        if not rel_path:
            continue
        path = PROJECT_ROOT / rel_path
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_suffixes and not path.name.endswith(".md"):
            continue
        paths.append(path)

    return paths


class PackageContractTests(unittest.TestCase):
    def test_exact_canonical_skill_inventory(self) -> None:
        actual_skills = {
            path.name
            for path in SKILLS_ROOT.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertSetEqual(actual_skills, EXPECTED_SKILLS)

    def test_skill_directory_frontmatter_names_match(self) -> None:
        for skill_name in sorted(EXPECTED_SKILLS):
            skill_dir = SKILLS_ROOT / skill_name
            with self.subTest(skill_dir=skill_dir.name):
                skill_name = _extract_skill_name(skill_dir / "SKILL.md")
                self.assertEqual(skill_name, skill_dir.name)

    def test_skill_names_follow_category_contract(self) -> None:
        for skill_name in sorted(EXPECTED_SKILLS):
            with self.subTest(skill_name=skill_name):
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
        self.assertEqual(
            {
                codex_manifest["version"],
                claude_manifest["version"],
                codex_plugin["version"],
                claude_plugin["version"],
            },
            {codex_manifest["version"]},
        )
        self.assertEqual(codex_plugin["source"]["path"], "./plugins/invest-flow")
        self.assertEqual(claude_plugin["source"], "./plugins/invest-flow")
        self.assertEqual(claude_market["metadata"]["description"], "Repo-local marketplace for InvestFlow with the canonical Chain Alpha workflow.")

    def test_cross_skill_invocations_resolve_to_canonical_ids(self) -> None:
        chain_alpha_content = (SKILLS_ROOT / "chain-alpha" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cursor = 0
        for skill_id in CHAIN_ALPHA_SEQUENCE:
            self.assertIn(skill_id, EXPECTED_SKILLS)
            match = re.search(
                _skill_reference_pattern(skill_id),
                chain_alpha_content[cursor:],
            )
            self.assertIsNotNone(
                match,
                f"chain-alpha is missing ordered invocation of {skill_id}",
            )
            cursor += match.end()

        for relative_path, skill_ids in CROSS_SKILL_INVOCATIONS.items():
            content = (PLUGIN_ROOT / relative_path).read_text(encoding="utf-8")
            for skill_id in skill_ids:
                with self.subTest(relative_path=relative_path, skill_id=skill_id):
                    self.assertIn(skill_id, EXPECTED_SKILLS)
                    self.assertRegex(content, _skill_reference_pattern(skill_id))

    def test_no_legacy_skill_ids_outside_compatibility_holes(self) -> None:
        legacy_hits: set[tuple[str, str]] = set()
        for path in _iter_text_paths():
            rel_path = path.relative_to(PROJECT_ROOT).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                self.fail(f"Unable to scan {rel_path} for legacy skill IDs: {exc}")

            legacy_tokens = {
                legacy_id for legacy_id in LEGACY_SKILL_IDS if legacy_id in content
            }
            legacy_tokens.update(
                token
                for token in LEGACY_INVOCATION_TOKENS
                if re.search(re.escape(token) + r"(?![\w-])", content)
            )
            allowed = ALLOWED_LEGACY_REFS.get(rel_path, set())
            for legacy_token in legacy_tokens - allowed:
                legacy_hits.add((rel_path, legacy_token))

        self.assertFalse(
            legacy_hits,
            "Legacy skill IDs found outside explicit compatibility references: "
            + ", ".join(sorted(f"{path}:{legacy}" for path, legacy in legacy_hits)),
        )
