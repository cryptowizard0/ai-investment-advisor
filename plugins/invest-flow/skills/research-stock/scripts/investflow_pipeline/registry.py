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
            self.get("research-profile"),
            self.get("research-fundamentals"),
            self.get("research-institutional"),
            self.get("research-reflexivity"),
            self.get("research-reportify"),
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


def _report_required_prompt(base_prompt: str, output_dir: str) -> str:
    return (
        f"{base_prompt}；必须生成并保存 Markdown 子报告到 {output_dir}/，"
        "并在回复末尾明确写出 report_path"
    )


def build_registry() -> SkillRegistry:
    specs = [
        _spec(
            skill_name="research-profile",
            agent_name="company_profile",
            stage="single_asset_context",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位",
                "output/research-profile",
            ),
            output_dir="output/research-profile",
            required=True,
        ),
        _spec(
            skill_name="research-fundamentals",
            agent_name="fundamental",
            stage="single_asset_validation",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-fundamentals 分析 {ticker}",
                "output/research-fundamentals",
            ),
            output_dir="output/research-fundamentals",
            required=True,
        ),
        _spec(
            skill_name="research-earnings",
            agent_name="earnings",
            stage="event_research",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-earnings 分析 {ticker} / {company} 的指定财报期或最新财报事件",
                "output/research-earnings",
            ),
            output_dir="output/research-earnings",
            required=False,
        ),
        _spec(
            skill_name="research-institutional",
            agent_name="institutional",
            stage="single_asset_validation",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-institutional 分析 {ticker}",
                "output/research-institutional",
            ),
            output_dir="output/research-institutional",
            required=False,
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
            skill_name="monitor-us-market",
            agent_name="daily_scan",
            stage="market_context",
            prompt_template="使用 invest-flow:monitor-us-market 生成美股收盘日报",
            output_dir="output/monitor-us-market",
            required=False,
        ),
        _spec(
            skill_name="monitor-gold",
            agent_name="gold_trend",
            stage="opportunity_discovery",
            prompt_template="使用 invest-flow:monitor-gold 分析 {company}",
            output_dir="output/monitor-gold",
            required=False,
        ),
        _spec(
            skill_name="research-reflexivity",
            agent_name="reflexivity",
            stage="single_asset_validation",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-reflexivity 对 {ticker} 做深度反身性分析",
                "output/research-reflexivity",
            ),
            output_dir="output/research-reflexivity",
            required=False,
        ),
        _spec(
            skill_name="research-reportify",
            agent_name="reportify",
            stage="decision_report",
            prompt_template=_report_required_prompt(
                "使用 invest-flow:research-reportify 分析 {ticker}",
                "output/research-reportify",
            ),
            output_dir="output/research-reportify",
            required=False,
        ),
    ]
    return SkillRegistry(specs)
