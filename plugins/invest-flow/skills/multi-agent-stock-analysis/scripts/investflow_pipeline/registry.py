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
