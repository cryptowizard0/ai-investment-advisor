# Multi-Agent Stock Analysis Refactor Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `multi-agent-stock-analysis` into a modular pipeline package while preserving the existing CLI entrypoint and old three-agent behavior.

**Architecture:** Keep `orchestrator.py` as a thin compatibility wrapper and move the core logic into `scripts/investflow_pipeline/`. Phase 1 implements the compatible `stock_decision_basic` flow with `fundamental-analysis`, `institutional-accumulation-analysis`, and `gie-investment-framework`, plus mock-mode end-to-end JSON and Markdown summary output.

**Tech Stack:** Python 3.12 standard library (`argparse`, `asyncio`, `dataclasses`, `json`, `pathlib`, `subprocess`, `unittest`), existing `opencode run` command surface, Markdown output files.

---

## Scope

This plan implements Phase 1 from the design spec:

- Split `orchestrator.py` into a CLI wrapper plus focused pipeline modules.
- Preserve the existing default three-agent flow.
- Preserve `mock` and `command` execution modes.
- Preserve old environment variable overrides: `ORCH_FUNDAMENTAL_CMD`, `ORCH_INSTITUTIONAL_CMD`, `ORCH_GIE_CMD`.
- Add unified command env override support: `INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS`, `INVESTFLOW_CMD_INSTITUTIONAL_ACCUMULATION_ANALYSIS`, `INVESTFLOW_CMD_GIE_INVESTMENT_FRAMEWORK`.
- Generate both orchestration JSON and Chinese Markdown summary in mock mode.
- Update `SKILL.md` so the documented workflow matches the command-driven implementation.

This plan does not implement Phase 2 workflow presets or default `market-data-router`, `reflexivity-quick-scan`, and `professional-investment-analyst` execution. It creates registry entries in a form that Phase 2 can extend.

## Files

- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py`
  Compatibility CLI wrapper and legacy API wrapper.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/__init__.py`
  Package exports.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py`
  Shared dataclasses and status enum.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/paths.py`
  Repo root detection, safe reads, report path discovery, non-overwriting output paths.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py`
  Skill registry and command override resolution.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/planner.py`
  Compatible three-agent planning.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/executor.py`
  Command/mock execution, retry, timeout, result validation.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py`
  Conservative Markdown handoff extraction.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py`
  Summary Markdown and orchestration JSON writer.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/runner.py`
  Pipeline orchestration across planner, executor, extractor, and composer.
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
  Standard-library tests for Phase 1 behavior.
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`
  Align docs with command-driven pipeline.
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md`
  Align workflow details with modular pipeline.
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md`
  Align data structure docs with Phase 1 model names.

## Commands

Run all Phase 1 tests with unittest discovery because the repository paths include hyphens:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Run the CLI in mock mode:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company Tesla --execution-mode mock
```

Expected CLI output includes:

```text
多Agent股票分析编排器
状态: success
成功: 3/3
综合报告:
编排JSON:
```

---

### Task 1: Create Pipeline Models

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/__init__.py`
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py`
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Write failing tests for model serialization**

Add this initial test file:

```python
import unittest
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


class ModelTests(unittest.TestCase):
    def test_stage_result_to_dict_contains_handoff(self):
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.SUCCESS,
            report_path="/tmp/report.md",
            handoff=Handoff(
                conclusion="业务质量稳定",
                recommendation="观望",
                confidence=62,
                key_evidence=["收入增长"],
                risk_flags=["估值偏高"],
                contradiction_points=[],
                monitoring_signals=["下一季收入增速"],
                data_gaps=[],
            ),
            duration=1.5,
            retry_count=0,
        )

        data = result.to_dict()

        self.assertEqual(data["skill_name"], "fundamental-analysis")
        self.assertEqual(data["agent_name"], "fundamental")
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["handoff"]["recommendation"], "观望")
        self.assertEqual(data["handoff"]["confidence"], 62)
        self.assertTrue(result.is_success)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline'`.

- [ ] **Step 3: Create the package exports**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/__init__.py`:

```python
"""InvestFlow multi-agent pipeline package."""

from .models import (
    AnalysisStatus,
    Handoff,
    OrchestrationConfig,
    PipelineResult,
    SkillSpec,
    StageResult,
    TaskRequest,
)

__all__ = [
    "AnalysisStatus",
    "Handoff",
    "OrchestrationConfig",
    "PipelineResult",
    "SkillSpec",
    "StageResult",
    "TaskRequest",
]
```

- [ ] **Step 4: Implement models**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    PARTIAL = "partial"


@dataclass
class Handoff:
    conclusion: str = ""
    recommendation: str = ""
    confidence: Optional[int] = None
    key_evidence: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    contradiction_points: List[str] = field(default_factory=list)
    monitoring_signals: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "key_evidence": list(self.key_evidence),
            "risk_flags": list(self.risk_flags),
            "contradiction_points": list(self.contradiction_points),
            "monitoring_signals": list(self.monitoring_signals),
            "data_gaps": list(self.data_gaps),
        }


@dataclass
class TaskRequest:
    task_id: str
    intent: str
    target: str
    ticker: str = ""
    company_name: str = ""
    market: str = "unknown"
    horizon: str = "mixed"
    requested_outputs: List[str] = field(default_factory=lambda: ["summary", "handoff_json"])


@dataclass
class SkillSpec:
    skill_name: str
    agent_name: str
    stage: str
    command_template: str
    output_dir: str
    required: bool = False
    timeout_seconds: int = 240
    max_retries: int = 1
    extractor_type: str = "markdown"
    legacy_env_var: str = ""
    unified_env_var: str = ""


@dataclass
class StageResult:
    skill_name: str
    agent_name: str
    status: AnalysisStatus
    output: str = ""
    report_path: Optional[str] = None
    handoff: Handoff = field(default_factory=Handoff)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    retry_count: int = 0
    command: str = ""

    @property
    def is_success(self) -> bool:
        return self.status == AnalysisStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "report_path": self.report_path,
            "handoff": self.handoff.to_dict(),
            "errors": list(self.errors),
            "duration": self.duration,
            "retry_count": self.retry_count,
            "command": self.command,
        }


@dataclass
class OrchestrationConfig:
    execution_mode: str = "command"
    max_retries: int = 1
    timeout_seconds: int = 240
    parallel_execution: bool = True
    continue_on_failure: bool = True


@dataclass
class PipelineResult:
    task_id: str
    status: str
    intent: str
    target: str
    ticker: str
    company_name: str
    started_at: str
    ended_at: str
    stage_results: List[StageResult]
    summary_report_path: Optional[str]
    orchestration_json_path: Optional[str]
    failed_required: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        success_count = sum(1 for result in self.stage_results if result.is_success)
        return {
            "task_id": self.task_id,
            "status": self.status,
            "intent": self.intent,
            "target": self.target,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "completed_count": success_count,
            "failed_count": len(self.stage_results) - success_count,
            "total_count": len(self.stage_results),
            "summary_report_path": self.summary_report_path,
            "orchestration_json_path": self.orchestration_json_path,
            "failed_required": list(self.failed_required),
            "warnings": list(self.warnings),
            "agents": {result.agent_name: result.to_dict() for result in self.stage_results},
        }
```

- [ ] **Step 5: Run the model test and verify it passes**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for `test_stage_result_to_dict_contains_handoff`.

- [ ] **Step 6: Commit Task 1**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/__init__.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add investflow pipeline models"
```

---

### Task 2: Add Path Utilities

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/paths.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing tests for root discovery and non-overwrite paths**

Append this class to `test_investflow_pipeline.py` before the `if __name__ == "__main__"` block:

```python

class PathTests(unittest.TestCase):
    def test_find_project_root_finds_agents_md(self):
        from investflow_pipeline.paths import find_project_root

        root = find_project_root()

        self.assertTrue((root / "AGENTS.md").exists())
        self.assertTrue((root / "plugins" / "invest-flow").exists())

    def test_unique_path_adds_numbered_suffix(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import unique_path

        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "report.md"
            first.write_text("existing", encoding="utf-8")

            second = unique_path(first)

        self.assertEqual(second.name, "report(1).md")
```

- [ ] **Step 2: Run tests and verify the new tests fail**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.paths'`.

- [ ] **Step 3: Implement path utilities**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/paths.py`:

```python
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
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for model and path tests.

- [ ] **Step 5: Commit Task 2**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/paths.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add pipeline path utilities"
```

---

### Task 3: Add Skill Registry

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing registry tests**

Append this class before the `if __name__ == "__main__"` block:

```python

class RegistryTests(unittest.TestCase):
    def test_basic_specs_include_three_legacy_agents(self):
        from investflow_pipeline.registry import build_registry

        registry = build_registry()
        specs = registry.basic_stock_specs()
        names = [spec.agent_name for spec in specs]

        self.assertEqual(names, ["fundamental", "institutional", "gie"])
        self.assertTrue(specs[0].required)
        self.assertFalse(specs[1].required)
        self.assertTrue(specs[2].required)

    def test_unified_env_var_overrides_default_command(self):
        import os
        from investflow_pipeline.registry import build_registry

        key = "INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS"
        original = os.environ.get(key)
        os.environ[key] = 'echo "/tmp/custom.md"'
        try:
            registry = build_registry()
            spec = registry.get("fundamental-analysis")
        finally:
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original

        self.assertEqual(spec.command_template, 'echo "/tmp/custom.md"')
```

- [ ] **Step 2: Run tests and verify registry tests fail**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.registry'`.

- [ ] **Step 3: Implement the registry**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py`:

```python
from __future__ import annotations

import os
from typing import Dict, List

from .models import SkillSpec


def _unified_env_name(skill_name: str) -> str:
    return "INVESTFLOW_CMD_" + skill_name.upper().replace("-", "_")


class SkillRegistry:
    def __init__(self, specs: List[SkillSpec]):
        self._specs: Dict[str, SkillSpec] = {spec.skill_name: spec for spec in specs}

    def get(self, skill_name: str) -> SkillSpec:
        return self._specs[skill_name]

    def all_specs(self) -> List[SkillSpec]:
        return list(self._specs.values())

    def basic_stock_specs(self) -> List[SkillSpec]:
        return [
            self.get("fundamental-analysis"),
            self.get("institutional-accumulation-analysis"),
            self.get("gie-investment-framework"),
        ]


def _resolve_command(default: str, legacy_env_var: str, unified_env_var: str) -> str:
    if unified_env_var and os.environ.get(unified_env_var):
        return os.environ[unified_env_var]
    if legacy_env_var and os.environ.get(legacy_env_var):
        return os.environ[legacy_env_var]
    return default


def _spec(
    *,
    skill_name: str,
    agent_name: str,
    stage: str,
    command_template: str,
    output_dir: str,
    required: bool,
    timeout_seconds: int = 240,
    max_retries: int = 1,
    legacy_env_var: str = "",
) -> SkillSpec:
    unified_env_var = _unified_env_name(skill_name)
    return SkillSpec(
        skill_name=skill_name,
        agent_name=agent_name,
        stage=stage,
        command_template=_resolve_command(command_template, legacy_env_var, unified_env_var),
        output_dir=output_dir,
        required=required,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        extractor_type="markdown",
        legacy_env_var=legacy_env_var,
        unified_env_var=unified_env_var,
    )


def build_registry() -> SkillRegistry:
    specs = [
        _spec(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            stage="single_asset_validation",
            command_template='opencode run "/fundamental-analysis {ticker}" --format default',
            output_dir="output/fundamental-analysis",
            required=True,
            legacy_env_var="ORCH_FUNDAMENTAL_CMD",
        ),
        _spec(
            skill_name="institutional-accumulation-analysis",
            agent_name="institutional",
            stage="single_asset_validation",
            command_template='opencode run "/institutional-accumulation-analysis {ticker}" --format default',
            output_dir="output/institutional-accumulation-analysis",
            required=False,
            legacy_env_var="ORCH_INSTITUTIONAL_CMD",
        ),
        _spec(
            skill_name="gie-investment-framework",
            agent_name="gie",
            stage="single_asset_validation",
            command_template='opencode run "/gie-investment-framework {ticker}" --format default',
            output_dir="output/gie-investment-framework",
            required=True,
            legacy_env_var="ORCH_GIE_CMD",
        ),
        _spec(
            skill_name="market-data-router",
            agent_name="market_data",
            stage="market_context",
            command_template='python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --market US --symbol {ticker} --interval auto --types bars --out -',
            output_dir="output/cache/market-data",
            required=False,
            timeout_seconds=60,
            max_retries=0,
        ),
        _spec(
            skill_name="daily-us-market-scan",
            agent_name="daily_scan",
            stage="market_context",
            command_template='opencode run "/daily-us-market-scan" --format default',
            output_dir="output/daily-us-market-scan",
            required=False,
        ),
        _spec(
            skill_name="ai-infrastructure-sector-discovery",
            agent_name="ai_infra_sector_discovery",
            stage="opportunity_discovery",
            command_template='opencode run "/ai-infrastructure-sector-discovery {company}" --format default',
            output_dir="output/ai-infrastructure-sector-discovery",
            required=False,
        ),
        _spec(
            skill_name="ai-infrastructure-scarcity-radar",
            agent_name="ai_infra_scarcity_radar",
            stage="opportunity_discovery",
            command_template='opencode run "/ai-infrastructure-scarcity-radar {company}" --format default',
            output_dir="output/ai-infrastructure-scarcity-radar",
            required=False,
        ),
        _spec(
            skill_name="gold-trend-analysis",
            agent_name="gold_trend",
            stage="opportunity_discovery",
            command_template='opencode run "/gold-trend-analysis {company}" --format default',
            output_dir="output/gold-analysis",
            required=False,
        ),
        _spec(
            skill_name="reflexivity-quick-scan",
            agent_name="reflexivity_quick",
            stage="single_asset_validation",
            command_template='opencode run "/reflexivity-quick-scan {ticker}" --format default',
            output_dir="output/reflexivity-quick-scan",
            required=False,
        ),
        _spec(
            skill_name="reflexivity-deep-analysis",
            agent_name="reflexivity_deep",
            stage="single_asset_validation",
            command_template='opencode run "/reflexivity-deep-analysis {ticker}" --format default',
            output_dir="output/reflexivity-deep-analysis",
            required=False,
        ),
        _spec(
            skill_name="professional-investment-analyst",
            agent_name="professional_analyst",
            stage="decision_report",
            command_template='opencode run "/professional-investment-analyst {ticker}" --format default',
            output_dir="output/professional-investment-analyst",
            required=False,
        ),
        _spec(
            skill_name="reportify-stock-analysis",
            agent_name="reportify",
            stage="decision_report",
            command_template='opencode run "/reportify-stock-analysis {ticker}" --format default',
            output_dir="output/reportify-stock-analysis",
            required=False,
        ),
    ]
    return SkillRegistry(specs)
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for model, path, and registry tests.

- [ ] **Step 5: Commit Task 3**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add investflow skill registry"
```

---

### Task 4: Add Compatible Planner

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/planner.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing planner tests**

Append this class before the `if __name__ == "__main__"` block:

```python

class PlannerTests(unittest.TestCase):
    def test_create_stock_request_sets_task_fields(self):
        from investflow_pipeline.planner import create_stock_request

        request = create_stock_request("tsla", "Tesla")

        self.assertEqual(request.intent, "stock_decision_basic")
        self.assertEqual(request.target, "TSLA")
        self.assertEqual(request.ticker, "TSLA")
        self.assertEqual(request.company_name, "Tesla")
        self.assertTrue(request.task_id.startswith("ma_"))

    def test_basic_plan_uses_three_legacy_specs(self):
        from investflow_pipeline.planner import create_stock_request, plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        specs = plan_basic_stock_analysis(request, build_registry())

        self.assertEqual([spec.agent_name for spec in specs], ["fundamental", "institutional", "gie"])
```

- [ ] **Step 2: Run tests and verify planner tests fail**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.planner'`.

- [ ] **Step 3: Implement planner**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/planner.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import List

from .models import SkillSpec, TaskRequest
from .registry import SkillRegistry


def create_stock_request(ticker: str, company_name: str = "") -> TaskRequest:
    normalized_ticker = ticker.strip().upper() or "TSLA"
    task_id = f"ma_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return TaskRequest(
        task_id=task_id,
        intent="stock_decision_basic",
        target=normalized_ticker,
        ticker=normalized_ticker,
        company_name=company_name.strip(),
        market="unknown",
        horizon="mixed",
        requested_outputs=["summary", "handoff_json"],
    )


def plan_basic_stock_analysis(request: TaskRequest, registry: SkillRegistry) -> List[SkillSpec]:
    if not request.ticker:
        raise ValueError("ticker is required for stock_decision_basic")
    return registry.basic_stock_specs()
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit Task 4**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/planner.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add compatible stock planner"
```

---

### Task 5: Add Extractors

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing extractor tests**

Append this class before the `if __name__ == "__main__"` block:

```python

class ExtractorTests(unittest.TestCase):
    def test_extract_handoff_reads_conclusion_and_risks(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# TSLA 分析报告

## 投资建议
建议：观望
置信度：68%

## 核心结论
公司长期逻辑仍在，但短期估值偏高。

## 核心证据
- 收入仍保持增长
- 毛利率存在压力

## 风险提示
- 估值回撤风险
- 竞争加剧
"""
        handoff = extract_handoff(markdown)

        self.assertEqual(handoff.recommendation, "观望")
        self.assertEqual(handoff.confidence, 68)
        self.assertIn("公司长期逻辑仍在，但短期估值偏高。", handoff.conclusion)
        self.assertIn("收入仍保持增长", handoff.key_evidence)
        self.assertIn("估值回撤风险", handoff.risk_flags)
```

- [ ] **Step 2: Run tests and verify extractor test fails**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.extractors'`.

- [ ] **Step 3: Implement conservative extractor**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py`:

```python
from __future__ import annotations

import re
from typing import List

from .models import Handoff


def _section(markdown: str, names: List[str]) -> str:
    lines = markdown.splitlines()
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") and any(name in stripped for name in names):
            start = index + 1
            break
    if start is None:
        return ""
    collected: List[str] = []
    for line in lines[start:]:
        if line.strip().startswith("#"):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def _bullets(text: str) -> List[str]:
    values: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
        elif stripped.startswith("* "):
            values.append(stripped[2:].strip())
    return values


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("- ") and not stripped.startswith("* "):
            return stripped
    return ""


def _extract_recommendation(markdown: str) -> str:
    patterns = [
        r"建议[:：]\s*([^\n\r]+)",
        r"操作评级[:：]\s*([^\n\r]+)",
        r"最终结论[:：]\s*([^\n\r]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, markdown)
        if match:
            return match.group(1).strip()
    return ""


def _extract_confidence(markdown: str) -> int | None:
    match = re.search(r"置信度[:：]?\s*(\d{1,3})\s*%", markdown)
    if not match:
        return None
    value = int(match.group(1))
    return max(0, min(100, value))


def extract_handoff(markdown: str) -> Handoff:
    conclusion_section = _section(markdown, ["核心结论", "投资建议", "执行摘要"])
    evidence_section = _section(markdown, ["核心证据", "关键证据", "核心逻辑"])
    risk_section = _section(markdown, ["风险提示", "主要风险", "高风险因素"])
    monitoring_section = _section(markdown, ["监控指标", "跟踪指标", "Dashboard"])
    gaps_section = _section(markdown, ["数据缺口", "信息缺口", "待验证"])

    conclusion = _first_nonempty_line(conclusion_section)
    if not conclusion:
        conclusion = _first_nonempty_line(markdown)

    return Handoff(
        conclusion=conclusion,
        recommendation=_extract_recommendation(markdown),
        confidence=_extract_confidence(markdown),
        key_evidence=_bullets(evidence_section),
        risk_flags=_bullets(risk_section),
        contradiction_points=_bullets(_section(markdown, ["冲突", "分歧"])),
        monitoring_signals=_bullets(monitoring_section),
        data_gaps=_bullets(gaps_section),
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit Task 5**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add markdown handoff extractor"
```

---

### Task 6: Add Executor

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/executor.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing executor tests**

Append this class before the `if __name__ == "__main__"` block:

```python

class ExecutorTests(unittest.TestCase):
    def test_mock_executor_returns_successful_stage_result(self):
        import asyncio
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        spec = build_registry().get("fundamental-analysis")
        executor = PipelineExecutor(
            config=OrchestrationConfig(execution_mode="mock"),
            project_root=Path.cwd(),
        )

        result = asyncio.run(executor.execute_stage(spec, request))

        self.assertTrue(result.is_success)
        self.assertEqual(result.agent_name, "fundamental")
        self.assertIn("TSLA", result.output)
        self.assertEqual(result.handoff.recommendation, "观望")

    def test_validate_rejects_short_output(self):
        from investflow_pipeline.executor import validate_output

        valid, reason = validate_output("短")

        self.assertFalse(valid)
        self.assertEqual(reason, "输出内容不完整")
```

- [ ] **Step 2: Run tests and verify executor tests fail**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.executor'`.

- [ ] **Step 3: Implement executor**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/executor.py`:

```python
from __future__ import annotations

import asyncio
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple

from .extractors import extract_handoff
from .models import AnalysisStatus, OrchestrationConfig, SkillSpec, StageResult, TaskRequest
from .paths import find_latest_report, find_report_from_output, safe_read_text


def validate_output(content: str) -> Tuple[bool, str]:
    if len(content.strip()) < 200:
        return False, "输出内容不完整"
    required_keywords = ["分析", "报告", "结论"]
    if not any(keyword in content for keyword in required_keywords):
        return False, "输出缺少关键内容标识"
    return True, ""


class PipelineExecutor:
    def __init__(self, config: OrchestrationConfig, project_root: Path):
        self.config = config
        self.project_root = project_root

    async def execute_stage(self, spec: SkillSpec, request: TaskRequest) -> StageResult:
        last_result: StageResult | None = None
        max_retries = self.config.max_retries if self.config.max_retries is not None else spec.max_retries
        timeout = self.config.timeout_seconds if self.config.timeout_seconds else spec.timeout_seconds

        for attempt in range(max_retries + 1):
            started_at = datetime.now()
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self._execute_once, spec, request, started_at, attempt),
                    timeout=timeout,
                )
                result.retry_count = attempt
                valid, reason = validate_output(result.output)
                if result.report_path:
                    report_text = safe_read_text(Path(result.report_path))
                    if not report_text:
                        valid = False
                        reason = f"报告文件不可读或为空: {result.report_path}"
                    else:
                        result.output = report_text
                        result.handoff = extract_handoff(report_text)
                if valid:
                    return result
                result.status = AnalysisStatus.FAILED
                result.errors.append(reason)
                last_result = result
            except asyncio.TimeoutError:
                last_result = StageResult(
                    skill_name=spec.skill_name,
                    agent_name=spec.agent_name,
                    status=AnalysisStatus.FAILED,
                    errors=[f"执行超时 (>{timeout}s)"],
                    retry_count=attempt,
                )
            except Exception as exc:
                last_result = StageResult(
                    skill_name=spec.skill_name,
                    agent_name=spec.agent_name,
                    status=AnalysisStatus.FAILED,
                    errors=[f"执行异常: {exc}"],
                    retry_count=attempt,
                )

        if last_result is None:
            return StageResult(
                skill_name=spec.skill_name,
                agent_name=spec.agent_name,
                status=AnalysisStatus.FAILED,
                errors=["未知错误"],
            )
        last_result.status = AnalysisStatus.FAILED
        return last_result

    def _execute_once(
        self,
        spec: SkillSpec,
        request: TaskRequest,
        started_at: datetime,
        attempt: int,
    ) -> StageResult:
        begin = datetime.now()
        if self.config.execution_mode == "mock":
            output = self._mock_output(spec, request)
            return StageResult(
                skill_name=spec.skill_name,
                agent_name=spec.agent_name,
                status=AnalysisStatus.SUCCESS,
                output=output,
                report_path=None,
                handoff=extract_handoff(output),
                duration=(datetime.now() - begin).total_seconds(),
                retry_count=attempt,
                command="mock",
            )

        command = spec.command_template.format(
            ticker=request.ticker,
            company=request.company_name or request.target,
            target=request.target,
        )
        completed = subprocess.run(
            shlex.split(command),
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
        combined_output = "\n".join(
            part for part in [completed.stdout, completed.stderr] if part
        ).strip()
        if completed.returncode != 0:
            excerpt = combined_output[:1000]
            raise RuntimeError(f"命令执行失败 (exit={completed.returncode}): {excerpt}")

        report_path = find_report_from_output(self.project_root, combined_output)
        if report_path is None:
            output_dir = self.project_root / spec.output_dir
            report_path = find_latest_report(output_dir, request.ticker, started_at)

        report_text = safe_read_text(report_path) if report_path else ""
        output = report_text or combined_output
        return StageResult(
            skill_name=spec.skill_name,
            agent_name=spec.agent_name,
            status=AnalysisStatus.SUCCESS,
            output=output,
            report_path=str(report_path) if report_path else None,
            handoff=extract_handoff(output),
            duration=(datetime.now() - begin).total_seconds(),
            retry_count=attempt,
            command=command,
        )

    def _mock_output(self, spec: SkillSpec, request: TaskRequest) -> str:
        return (
            f"# {request.ticker} {spec.skill_name} 分析报告\n\n"
            "## 投资建议\n"
            "建议：观望\n"
            "置信度：60%\n\n"
            "## 核心结论\n"
            f"{request.ticker} 的 {spec.agent_name} mock 分析结论：当前用于验证编排、抽取和汇总流程，不代表真实投资建议。\n\n"
            "## 核心证据\n"
            "- mock 输出包含稳定报告结构\n"
            "- mock 输出可用于端到端测试\n\n"
            "## 风险提示\n"
            "- 当前为调试模式\n"
            "- 未接入真实市场数据\n\n"
            "## 监控指标 Dashboard\n"
            "- 后续真实 command 模式报告路径\n"
            "- 子 Agent 成功率\n"
        )
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit Task 6**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/executor.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add pipeline executor"
```

---

### Task 7: Add Composer

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing composer tests**

Append this class before the `if __name__ == "__main__"` block:

```python

class ComposerTests(unittest.TestCase):
    def test_write_outputs_creates_json_and_markdown(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.composer import write_outputs
        from investflow_pipeline.models import AnalysisStatus, Handoff, PipelineResult, StageResult

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = PipelineResult(
                task_id="ma_test",
                status="success",
                intent="stock_decision_basic",
                target="TSLA",
                ticker="TSLA",
                company_name="Tesla",
                started_at="2026-05-25T00:00:00",
                ended_at="2026-05-25T00:01:00",
                stage_results=[
                    StageResult(
                        skill_name="fundamental-analysis",
                        agent_name="fundamental",
                        status=AnalysisStatus.SUCCESS,
                        handoff=Handoff(
                            conclusion="基本面中性",
                            recommendation="观望",
                            confidence=60,
                            key_evidence=["收入增长"],
                            risk_flags=["估值偏高"],
                        ),
                    )
                ],
                summary_report_path=None,
                orchestration_json_path=None,
            )

            updated = write_outputs(root, result)

            self.assertIsNotNone(updated.summary_report_path)
            self.assertIsNotNone(updated.orchestration_json_path)
            self.assertTrue(Path(updated.summary_report_path).exists())
            self.assertTrue(Path(updated.orchestration_json_path).exists())
            self.assertIn("作者：InvestmentFlow", Path(updated.summary_report_path).read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run tests and verify composer test fails**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.composer'`.

- [ ] **Step 3: Implement composer**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py`:

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .models import PipelineResult, StageResult
from .paths import ensure_output_dir, unique_path


def _line_items(values: List[str], fallback: str) -> str:
    if not values:
        return f"- {fallback}"
    return "\n".join(f"- {value}" for value in values)


def _stage_table(results: List[StageResult]) -> str:
    rows = ["| 维度 | 状态 | 建议 | 置信度 | 报告 |", "|---|---|---|---|---|"]
    for result in results:
        handoff = result.handoff
        confidence = "" if handoff.confidence is None else f"{handoff.confidence}%"
        report_path = result.report_path or "未生成"
        rows.append(
            f"| {result.skill_name} | {result.status.value} | {handoff.recommendation or '未提取'} | {confidence or '未提取'} | {report_path} |"
        )
    return "\n".join(rows)


def compose_summary(result: PipelineResult) -> str:
    successful = [stage for stage in result.stage_results if stage.is_success]
    failed = [stage for stage in result.stage_results if not stage.is_success]
    recommendations = [stage.handoff.recommendation for stage in successful if stage.handoff.recommendation]
    conclusion = "；".join(stage.handoff.conclusion for stage in successful if stage.handoff.conclusion)
    if not conclusion:
        conclusion = "当前没有足够成功维度形成完整投资结论。"

    key_evidence: List[str] = []
    risk_flags: List[str] = []
    monitoring_signals: List[str] = []
    data_gaps: List[str] = []
    for stage in successful:
        key_evidence.extend(stage.handoff.key_evidence)
        risk_flags.extend(stage.handoff.risk_flags)
        monitoring_signals.extend(stage.handoff.monitoring_signals)
        data_gaps.extend(stage.handoff.data_gaps)
    for stage in failed:
        data_gaps.append(f"{stage.skill_name} 未成功：{'；'.join(stage.errors) or '未知错误'}")

    final_recommendation = recommendations[0] if recommendations else "观望"

    return f"""# {result.ticker} 多维度投资分析摘要

作者：InvestmentFlow

## 执行摘要

- 任务类型：{result.intent}
- 分析目标：{result.target}
- 公司名称：{result.company_name or "未提供"}
- 综合状态：{result.status}
- 综合建议：{final_recommendation}

## 综合结论

{conclusion}

## 各维度结果

{_stage_table(result.stage_results)}

## 多维共振信号

{_line_items(key_evidence, "暂无可提取的共振证据")}

## 冲突与分歧

{_line_items([stage.handoff.conclusion for stage in successful if stage.handoff.conclusion and stage.handoff.recommendation not in {"观望", "持有"}], "暂无明确冲突，需结合完整子报告复核")}

## 风险提示

{_line_items(risk_flags, "暂无可提取风险，需阅读子报告")}

## 跟踪指标 Dashboard

{_line_items(monitoring_signals, "后续跟踪各子报告列出的关键财务、资金流与叙事验证指标")}

## 数据缺口

{_line_items(data_gaps, "暂无显著数据缺口")}

## 子报告索引

{_line_items([f"{stage.skill_name}: {stage.report_path or '未生成'}" for stage in result.stage_results], "暂无子报告")}

## 免责声明

本报告仅供研究参考，不构成投资建议。投资决策需结合个人风险承受能力和最新市场信息。
"""


def write_outputs(project_root: Path, result: PipelineResult) -> PipelineResult:
    summary_dir = ensure_output_dir(project_root, "output/summary")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    date_text = datetime.now().strftime("%Y-%m-%d")
    json_path = unique_path(summary_dir / f"orchestration-{result.ticker}-{timestamp}.json")
    markdown_path = unique_path(summary_dir / f"综合分析-{result.ticker}-{date_text}.md")

    result.orchestration_json_path = str(json_path)
    result.summary_report_path = str(markdown_path)

    markdown_path.write_text(compose_summary(result), encoding="utf-8")
    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit Task 7**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add summary composer"
```

---

### Task 8: Add Pipeline Runner

**Files:**
- Create: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/runner.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing runner test**

Append this class before the `if __name__ == "__main__"` block:

```python

class RunnerTests(unittest.TestCase):
    def test_mock_pipeline_writes_success_outputs(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.runner import analyze_stock

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "output").mkdir()
            result = asyncio.run(
                analyze_stock(
                    ticker="TSLA",
                    company="Tesla",
                    config=OrchestrationConfig(execution_mode="mock"),
                    project_root=root,
                )
            )

        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.stage_results), 3)
        self.assertEqual(sum(1 for stage in result.stage_results if stage.is_success), 3)
        self.assertIsNotNone(result.summary_report_path)
        self.assertIsNotNone(result.orchestration_json_path)
```

- [ ] **Step 2: Run tests and verify runner test fails**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'investflow_pipeline.runner'`.

- [ ] **Step 3: Implement runner**

Create `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/runner.py`:

```python
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from .composer import write_outputs
from .executor import PipelineExecutor
from .models import OrchestrationConfig, PipelineResult, StageResult
from .paths import find_project_root
from .planner import create_stock_request, plan_basic_stock_analysis
from .registry import build_registry


def _overall_status(results: list[StageResult]) -> str:
    success_count = sum(1 for result in results if result.is_success)
    if success_count == len(results):
        return "success"
    if success_count > 0:
        return "partial_success"
    return "failed"


async def analyze_stock(
    ticker: str,
    company: str = "",
    config: Optional[OrchestrationConfig] = None,
    project_root: Optional[Path] = None,
) -> PipelineResult:
    effective_config = config or OrchestrationConfig()
    root = project_root or find_project_root()
    request = create_stock_request(ticker, company)
    registry = build_registry()
    specs = plan_basic_stock_analysis(request, registry)
    executor = PipelineExecutor(effective_config, root)
    started_at = datetime.now()

    if effective_config.parallel_execution:
        stage_results = await asyncio.gather(
            *(executor.execute_stage(spec, request) for spec in specs)
        )
    else:
        stage_results = []
        for spec in specs:
            stage_results.append(await executor.execute_stage(spec, request))

    failed_required = [
        spec.skill_name
        for spec, result in zip(specs, stage_results)
        if spec.required and not result.is_success
    ]
    ended_at = datetime.now()
    pipeline_result = PipelineResult(
        task_id=request.task_id,
        status=_overall_status(list(stage_results)),
        intent=request.intent,
        target=request.target,
        ticker=request.ticker,
        company_name=request.company_name,
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        stage_results=list(stage_results),
        summary_report_path=None,
        orchestration_json_path=None,
        failed_required=failed_required,
        warnings=[],
    )
    return write_outputs(root, pipeline_result)


def analyze_stock_sync(
    ticker: str,
    company: str = "",
    config: Optional[OrchestrationConfig] = None,
    project_root: Optional[Path] = None,
) -> PipelineResult:
    return asyncio.run(analyze_stock(ticker, company, config, project_root))
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Commit Task 8**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/runner.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: add pipeline runner"
```

---

### Task 9: Replace Orchestrator With Compatibility Wrapper

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Add failing compatibility API test**

Append this class before the `if __name__ == "__main__"` block:

```python

class OrchestratorCompatibilityTests(unittest.TestCase):
    def test_analyze_stock_with_retry_returns_legacy_shape(self):
        import importlib.util

        script_path = SCRIPT_DIR / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("orchestrator", script_path)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        result = module.analyze_stock_with_retry(
            ticker="TSLA",
            company="Tesla",
            execution_mode="mock",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["completed_count"], 3)
        self.assertEqual(result["total_count"], 3)
        self.assertIn("summary_report_path", result)
        self.assertIn("orchestration_json_path", result)
```

- [ ] **Step 2: Run tests and verify compatibility test fails**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: FAIL because the existing `analyze_stock_with_retry()` output does not include `summary_report_path`.

- [ ] **Step 3: Replace orchestrator with wrapper**

Replace `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py` with:

```python
#!/usr/bin/env python3
"""
Multi-agent stock analysis CLI wrapper.

The implementation lives in investflow_pipeline. This file preserves the
existing script path and Python API used by README and existing workflows.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from investflow_pipeline.models import OrchestrationConfig
from investflow_pipeline.runner import analyze_stock_sync


def analyze_stock_with_retry(
    ticker: str,
    company: str = "",
    max_retries: int = 1,
    timeout: int = 240,
    **kwargs: Any,
) -> Dict[str, Any]:
    config = OrchestrationConfig(
        execution_mode=kwargs.get("execution_mode", os.environ.get("ORCH_EXECUTION_MODE", "command")),
        max_retries=max_retries,
        timeout_seconds=timeout,
        parallel_execution=kwargs.get("parallel_execution", True),
        continue_on_failure=kwargs.get("continue_on_failure", True),
    )
    result = analyze_stock_sync(ticker=ticker, company=company, config=config)
    data = result.to_dict()
    data["summary_report_path"] = result.summary_report_path
    data["orchestration_json_path"] = result.orchestration_json_path
    data["retried_count"] = sum(stage.retry_count > 0 for stage in result.stage_results)
    data["metadata"] = {
        "start_time": result.started_at,
        "end_time": result.ended_at,
        "config": {
            "execution_mode": config.execution_mode,
            "max_retries": config.max_retries,
            "timeout": config.timeout_seconds,
            "parallel": config.parallel_execution,
        },
    }
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="多Agent股票分析编排器")
    parser.add_argument("ticker", nargs="?", default="TSLA")
    parser.add_argument("--company", default="")
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--execution-mode",
        choices=["command", "mock"],
        default=os.environ.get("ORCH_EXECUTION_MODE", "command"),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("多Agent股票分析编排器")
    print("=" * 60)

    result = analyze_stock_with_retry(
        ticker=args.ticker,
        company=args.company,
        max_retries=args.max_retries,
        timeout=args.timeout,
        execution_mode=args.execution_mode,
    )

    print("\n分析结果:")
    print(f"  状态: {result['status']}")
    print(f"  成功: {result['completed_count']}/{result['total_count']}")
    print(f"  重试: {result['retried_count']} 次")
    print(f"  综合报告: {result.get('summary_report_path')}")
    print(f"  编排JSON: {result.get('orchestration_json_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: PASS for all tests.

- [ ] **Step 5: Run CLI mock mode**

Run:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company Tesla --execution-mode mock
```

Expected output includes:

```text
状态: success
成功: 3/3
综合报告:
编排JSON:
```

- [ ] **Step 6: Commit Task 9**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py \
        plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "refactor: wrap orchestrator around pipeline"
```

---

### Task 10: Align Skill Documentation

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md`

- [ ] **Step 1: Replace the architecture section in SKILL.md**

In `SKILL.md`, replace the existing overview diagram and `delegate_task`-based workflow with this content:

````markdown
## 概述

本系统通过命令驱动的轻量 Pipeline 实现多维度股票分析。当前默认兼容流程为：

```text
用户请求
  -> CLI / Python API
  -> Intent Request
  -> Basic Stock Planner
  -> 并行执行 3 个 Skill
       fundamental-analysis
       institutional-accumulation-analysis
       gie-investment-framework
  -> Handoff Extractor
  -> Decision Composer
  -> orchestration JSON + 中文综合摘要
```

Phase 1 保持旧三件套流程兼容；后续阶段会把 `market-data-router`、`reflexivity-*`、`professional-investment-analyst`、`daily-us-market-scan` 和 AI 基建相关 skill 接入更多 workflow preset。
````

- [ ] **Step 2: Replace the SubAgent launch section in SKILL.md**

Replace the `delegate_task(...)` examples with:

````markdown
### Step 2: 生成兼容执行计划

默认 `stock_decision_basic` 计划包含：

| Agent | Skill | 默认命令 |
|---|---|---|
| fundamental | `fundamental-analysis` | `opencode run "/fundamental-analysis {ticker}" --format default` |
| institutional | `institutional-accumulation-analysis` | `opencode run "/institutional-accumulation-analysis {ticker}" --format default` |
| gie | `gie-investment-framework` | `opencode run "/gie-investment-framework {ticker}" --format default` |

命令可通过环境变量覆盖：

```bash
export INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS='opencode run "/fundamental-analysis {ticker}" --format default'
export INVESTFLOW_CMD_INSTITUTIONAL_ACCUMULATION_ANALYSIS='opencode run "/institutional-accumulation-analysis {ticker}" --format default'
export INVESTFLOW_CMD_GIE_INVESTMENT_FRAMEWORK='opencode run "/gie-investment-framework {ticker}" --format default'
```
````

- [ ] **Step 3: Update output section in SKILL.md**

Ensure the output section states:

```markdown
### Step 6: 输出结果

系统输出两类文件：

- `output/summary/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`
- `output/summary/综合分析-{TICKER}-{YYYY-MM-DD}.md`

综合报告必须包含固定作者字段：`InvestmentFlow`。
```

- [ ] **Step 4: Update workflow-guide.md with Phase 1 command-driven flow**

At the top of `workflow-guide.md`, add this note:

```markdown
> 当前实现为 Phase 1 命令驱动 Pipeline。历史文档中出现的 `delegate_task` 伪代码仅表示目标架构概念，不是当前脚本调用方式。当前真实入口是 `scripts/orchestrator.py`，核心逻辑位于 `scripts/investflow_pipeline/`。
```

- [ ] **Step 5: Update data-structure.md with Phase 1 model names**

Add this section near the top of `data-structure.md`:

```markdown
## Phase 1 实现模型

当前代码中的数据模型位于：

`scripts/investflow_pipeline/models.py`

核心模型：

- `TaskRequest`
- `SkillSpec`
- `StageResult`
- `Handoff`
- `PipelineResult`
- `OrchestrationConfig`

历史 TypeScript interface 示例保留为设计参考；以 Python dataclass 为当前实现准绳。
```

- [ ] **Step 6: Run documentation checks**

Run:

```bash
rg -n "delegate_task\\(" plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md
```

Expected: no output.

Run:

```bash
rg -n "INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS|orchestration-\\{TICKER\\}" plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md
```

Expected: output includes the new environment variable and output path sections.

- [ ] **Step 7: Commit Task 10**

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md \
        plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md \
        plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md
git commit -m "docs: align multi-agent skill with pipeline"
```

---

### Task 11: Final Phase 1 Verification

**Files:**
- Modify only if a verification failure identifies a concrete defect in files changed by prior tasks.

- [ ] **Step 1: Run unit tests**

Run:

```bash
python -m unittest discover -s plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests -p 'test_*.py' -v
```

Expected: all tests pass.

- [ ] **Step 2: Run CLI help**

Run:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py --help
```

Expected output includes:

```text
usage: orchestrator.py
--execution-mode {command,mock}
```

- [ ] **Step 3: Run CLI mock mode**

Run:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company Tesla --execution-mode mock
```

Expected output includes:

```text
状态: success
成功: 3/3
综合报告:
编排JSON:
```

- [ ] **Step 4: Verify generated files**

Run:

```bash
ls output/summary | sort | tail
```

Expected: at least one `orchestration-TSLA-*.json` and one `综合分析-TSLA-*.md`.

Run:

```bash
rg -n "作者：InvestmentFlow|综合结论|各维度结果|数据缺口" output/summary/综合分析-TSLA-*.md
```

Expected: matches in the generated summary Markdown.

- [ ] **Step 5: Verify git diff quality**

Run:

```bash
git diff --check
```

Expected: no output.

Run:

```bash
git status --short
```

Expected: only intended Phase 1 files are modified, plus generated `output/summary` files if they are not gitignored.

- [ ] **Step 6: Remove generated output files from the commit if tracked**

Run:

```bash
git status --short output/summary
```

Expected: generated files are either ignored or visible as untracked files.

If generated output files are staged, unstage them:

```bash
git restore --staged output/summary
```

Expected: generated output files are not included in the next commit.

- [ ] **Step 7: Commit final verification fixes if any were needed**

If Step 1-6 required code or documentation fixes, commit them:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis
git commit -m "test: verify multi-agent pipeline phase 1"
```

If no fixes were needed, do not create an empty commit.

## Self-Review Checklist

- Spec coverage: Phase 1 architecture split, compatibility CLI, mock execution, summary Markdown, JSON output, env override support, partial success model, and docs alignment are covered.
- Out of scope: Phase 2 default `stock_decision` with market data, reflexivity, and professional analyst execution is intentionally left for a later plan.
- Placeholder scan: The plan contains no incomplete requirements or unspecified implementation steps.
- Type consistency: `TaskRequest`, `SkillSpec`, `StageResult`, `Handoff`, `PipelineResult`, `OrchestrationConfig`, `PipelineExecutor`, `build_registry`, `create_stock_request`, `plan_basic_stock_analysis`, `extract_handoff`, `write_outputs`, and `analyze_stock` are introduced before use in implementation tasks.
