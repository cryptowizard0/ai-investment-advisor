from __future__ import annotations

from typing import Dict, List

from .models import SkillSpec


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
            self.get("reflexivity-deep-analysis"),
            self.get("reportify-stock-analysis"),
            self.get("non-consensus-company-discovery"),
        ]


def _spec(
    *,
    skill_name: str,
    agent_name: str,
    stage: str,
    prompt_template: str,
    output_dir: str,
    required: bool,
) -> SkillSpec:
    return SkillSpec(
        skill_name=skill_name,
        agent_name=agent_name,
        stage=stage,
        prompt_template=prompt_template,
        output_dir=output_dir,
        required=required,
        extractor_type="markdown",
    )


def build_registry() -> SkillRegistry:
    specs = [
        _spec(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            stage="single_asset_validation",
            prompt_template="使用 invest-flow:fundamental-analysis 分析 {ticker}",
            output_dir="output/fundamental-analysis",
            required=True,
        ),
        _spec(
            skill_name="institutional-accumulation-analysis",
            agent_name="institutional",
            stage="single_asset_validation",
            prompt_template="使用 invest-flow:institutional-accumulation-analysis 分析 {ticker}",
            output_dir="output/institutional-accumulation-analysis",
            required=False,
        ),
        _spec(
            skill_name="gie-investment-framework",
            agent_name="gie",
            stage="single_asset_validation",
            prompt_template="使用 invest-flow:gie-investment-framework 分析 {ticker} / {company}",
            output_dir="output/gie-investment-framework",
            required=True,
        ),
        _spec(
            skill_name="market-data-router",
            agent_name="market_data",
            stage="market_context",
            prompt_template="使用 invest-flow:market-data-router 获取 {ticker} 的市场数据",
            output_dir="output/cache/market-data",
            required=False,
        ),
        _spec(
            skill_name="daily-us-market-scan",
            agent_name="daily_scan",
            stage="market_context",
            prompt_template="使用 invest-flow:daily-us-market-scan 生成美股收盘日报",
            output_dir="output/daily-us-market-scan",
            required=False,
        ),
        _spec(
            skill_name="gold-trend-analysis",
            agent_name="gold_trend",
            stage="opportunity_discovery",
            prompt_template="使用 invest-flow:gold-trend-analysis 分析 {company}",
            output_dir="output/gold-analysis",
            required=False,
        ),
        _spec(
            skill_name="reflexivity-quick-scan",
            agent_name="reflexivity_quick",
            stage="single_asset_validation",
            prompt_template="使用 invest-flow:reflexivity-quick-scan 分析 {ticker}",
            output_dir="output/reflexivity-quick-scan",
            required=False,
        ),
        _spec(
            skill_name="reflexivity-deep-analysis",
            agent_name="reflexivity_deep",
            stage="single_asset_validation",
            prompt_template="使用 invest-flow:reflexivity-deep-analysis 分析 {ticker}",
            output_dir="output/reflexivity-deep-analysis",
            required=False,
        ),
        _spec(
            skill_name="professional-investment-analyst",
            agent_name="professional_analyst",
            stage="decision_report",
            prompt_template="使用 invest-flow:professional-investment-analyst 分析 {ticker}",
            output_dir="output/professional-investment-analyst",
            required=False,
        ),
        _spec(
            skill_name="reportify-stock-analysis",
            agent_name="reportify",
            stage="decision_report",
            prompt_template="使用 invest-flow:reportify-stock-analysis 分析 {ticker}",
            output_dir="output/reportify-stock-analysis",
            required=False,
        ),
        _spec(
            skill_name="non-consensus-company-discovery",
            agent_name="non_consensus",
            stage="thesis_challenge",
            prompt_template="使用 invest-flow:non-consensus-company-discovery 评估 {ticker} / {company} 的非共识重估机会",
            output_dir="output/non-consensus-company-discovery",
            required=False,
        ),
    ]
    return SkillRegistry(specs)
