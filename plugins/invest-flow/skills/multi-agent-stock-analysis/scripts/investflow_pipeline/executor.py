from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .models import (
    AnalysisStatus,
    Handoff,
    OrchestrationConfig,
    SkillSpec,
    StageResult,
    TaskRequest,
)


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
        self.project_root = project_root.resolve()

    async def execute_stage(self, spec: SkillSpec, request: TaskRequest) -> StageResult:
        prompt = self.format_prompt(spec, request)
        return StageResult(
            skill_name=spec.skill_name,
            agent_name=spec.agent_name,
            status=AnalysisStatus.PENDING,
            output=prompt,
            handoff=Handoff(
                data_gaps=[
                    "等待 Codex 当前会话执行该 prompt 后回填 handoff 或生成综合报告"
                ]
            ),
            prompt=prompt,
        )

    def format_prompt(self, spec: SkillSpec, request: TaskRequest) -> str:
        company = request.company_name or request.target
        return spec.prompt_template.format(
            ticker=request.ticker,
            company=company,
            target=request.target,
        )
