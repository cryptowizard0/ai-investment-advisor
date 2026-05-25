from __future__ import annotations

import asyncio
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

from .extractors import extract_handoff
from .models import (
    AnalysisStatus,
    OrchestrationConfig,
    SkillSpec,
    StageResult,
    TaskRequest,
)
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
        self.project_root = project_root.resolve()

    async def execute_stage(self, spec: SkillSpec, request: TaskRequest) -> StageResult:
        max_retries = max(0, min(self.config.max_retries, spec.max_retries))
        effective_timeout = self._effective_timeout(spec)
        last_result: StageResult | None = None

        for attempt in range(max_retries + 1):
            started = time.monotonic()
            try:
                result = await asyncio.to_thread(
                    self._execute_once,
                    spec,
                    request,
                    effective_timeout,
                )
                result.retry_count = attempt
                result.duration = time.monotonic() - started

                if result.status == AnalysisStatus.FAILED:
                    last_result = result
                    continue

                content = result.output
                if result.report_path:
                    report_text = safe_read_text(Path(result.report_path))
                    content = report_text
                    result.output = report_text

                valid, reason = validate_output(content)
                if valid:
                    result.status = AnalysisStatus.SUCCESS
                    result.handoff = extract_handoff(content)
                    return result

                result.status = AnalysisStatus.FAILED
                result.errors.append(reason)
                last_result = result
            except subprocess.TimeoutExpired as exc:
                last_result = self._failed_result(
                    spec,
                    time.monotonic() - started,
                    attempt,
                    f"执行超时 (>{exc.timeout}s)",
                )
            except Exception as exc:
                last_result = self._failed_result(
                    spec,
                    time.monotonic() - started,
                    attempt,
                    f"执行异常: {exc}",
                )

        if last_result:
            last_result.status = AnalysisStatus.FAILED
            return last_result

        return self._failed_result(spec, 0.0, max_retries, "未知错误")

    def _execute_once(
        self,
        spec: SkillSpec,
        request: TaskRequest,
        timeout_seconds: int | None = None,
    ) -> StageResult:
        if self.config.execution_mode == "mock":
            output = self._mock_output(spec, request)
            return StageResult(
                skill_name=spec.skill_name,
                agent_name=spec.agent_name,
                status=AnalysisStatus.SUCCESS,
                output=output,
                handoff=extract_handoff(output),
            )

        command = self._format_command(spec, request)
        if not command.strip():
            raise RuntimeError("未配置执行命令（command_template）")

        started_at = datetime.now()
        completed = subprocess.run(
            shlex.split(command),
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        combined_output = "\n".join(
            part for part in [completed.stdout, completed.stderr] if part
        ).strip()

        if completed.returncode != 0:
            excerpt = combined_output[:1000]
            raise RuntimeError(
                f"命令执行失败 (exit={completed.returncode})"
                + (f": {excerpt}" if excerpt else "")
            )

        report_path = find_report_from_output(self.project_root, combined_output)
        if report_path is None:
            output_dir = (self.project_root / spec.output_dir).resolve()
            report_path = find_latest_report(output_dir, request.ticker, started_at)

        if report_path is None:
            return StageResult(
                skill_name=spec.skill_name,
                agent_name=spec.agent_name,
                status=AnalysisStatus.FAILED,
                output=combined_output,
                errors=["命令执行完成，但未定位到输出报告文件"],
                command=command,
            )

        output = combined_output
        if report_path:
            report_text = safe_read_text(report_path)
            if report_text:
                output = report_text

        return StageResult(
            skill_name=spec.skill_name,
            agent_name=spec.agent_name,
            status=AnalysisStatus.SUCCESS,
            output=output,
            report_path=str(report_path) if report_path else None,
            handoff=extract_handoff(output),
            command=command,
        )

    def _mock_output(self, spec: SkillSpec, request: TaskRequest) -> str:
        ticker = request.ticker or request.target
        company = request.company_name or ticker
        return f"""# {ticker} {company} {spec.skill_name} 分析报告

## 投资建议
建议：观望
置信度：60%

## 核心结论
{ticker} 当前处于模拟执行模式，本报告用于验证多 Agent 管线执行、结果校验、handoff 提取与聚合流程。结论是业务质量仍需结合真实数据确认，短期不输出激进买入或卖出信号。

## 核心证据
- {company} 的 mock 分析保留 ticker、公司名称、技能名称和报告结构，便于下游测试识别。
- 输出长度超过最低校验阈值，并包含分析、报告、结论等关键内容标识。
- 投资建议明确为观望，置信度为 60%，用于稳定验证 handoff 字段解析。

## 风险提示
- 该内容不是实时投资建议，不能替代真实基本面、资金流和估值分析。
- 真实命令执行仍需要外部工具输出报告路径或足够完整的标准输出。

## 监控指标
- 后续阶段应关注真实报告路径识别、异常重试次数、输出完整度和下游摘要一致性。
"""

    def _format_command(self, spec: SkillSpec, request: TaskRequest) -> str:
        return spec.command_template.format(
            ticker=request.ticker,
            company=request.company_name or request.target,
            target=request.target,
        )

    def _effective_timeout(self, spec: SkillSpec) -> int | None:
        timeouts = [
            timeout
            for timeout in (self.config.timeout_seconds, spec.timeout_seconds)
            if timeout and timeout > 0
        ]
        if not timeouts:
            return None
        return min(timeouts)

    def _failed_result(
        self,
        spec: SkillSpec,
        duration: float,
        retry_count: int,
        error: str,
    ) -> StageResult:
        return StageResult(
            skill_name=spec.skill_name,
            agent_name=spec.agent_name,
            status=AnalysisStatus.FAILED,
            errors=[error],
            duration=duration,
            retry_count=retry_count,
        )
