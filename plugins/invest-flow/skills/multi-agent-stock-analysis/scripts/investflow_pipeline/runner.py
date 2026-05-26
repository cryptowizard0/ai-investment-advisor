from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from .composer import write_outputs
from .executor import PipelineExecutor
from .models import AnalysisStatus, OrchestrationConfig, PipelineResult, StageResult
from .paths import find_project_root
from .planner import create_stock_request, plan_basic_stock_analysis
from .registry import build_registry


def _stage_exception_result(spec, exc: Exception) -> StageResult:
    return StageResult(
        skill_name=spec.skill_name,
        agent_name=spec.agent_name,
        status=AnalysisStatus.FAILED,
        errors=[f"Stage execution raised exception: {exc}"],
    )


def _overall_status(results: list[StageResult]) -> str:
    success_count = sum(1 for result in results if result.status == AnalysisStatus.SUCCESS)
    if success_count == len(results) and results:
        return AnalysisStatus.SUCCESS.value
    if success_count > 0:
        return "partial_success"
    return AnalysisStatus.FAILED.value


async def analyze_stock(
    ticker: str,
    company: str = "",
    config: Optional[OrchestrationConfig] = None,
    project_root: Optional[Path] = None,
) -> PipelineResult:
    effective_config = config or OrchestrationConfig()
    root = (project_root or find_project_root()).resolve()

    request = create_stock_request(ticker, company)
    registry = build_registry()
    specs = plan_basic_stock_analysis(request, registry)
    executor = PipelineExecutor(effective_config, root)
    started_at = datetime.now().isoformat()

    if effective_config.parallel_execution:
        raw_results = await asyncio.gather(
            *(executor.execute_stage(spec, request) for spec in specs),
            return_exceptions=True,
        )
        stage_results = []
        for spec, raw_result in zip(specs, raw_results):
            if isinstance(raw_result, Exception):
                stage_results.append(_stage_exception_result(spec, raw_result))
                continue
            stage_results.append(raw_result)
    else:
        stage_results = []
        for spec in specs:
            try:
                stage_result = await executor.execute_stage(spec, request)
            except Exception as exc:
                stage_result = _stage_exception_result(spec, exc)
            stage_results.append(stage_result)
            if not effective_config.continue_on_failure and not stage_result.is_success:
                break

    failed_required = []
    for spec, stage_result in zip(specs, stage_results):
        if spec.required and not stage_result.is_success:
            failed_required.append(spec.skill_name)

    result = PipelineResult(
        task_id=request.task_id,
        status=_overall_status(stage_results),
        intent=request.intent,
        target=request.target,
        ticker=request.ticker,
        company_name=request.company_name,
        started_at=started_at,
        ended_at=datetime.now().isoformat(),
        stage_results=stage_results,
        summary_report_path=None,
        orchestration_json_path=None,
        failed_required=failed_required,
    )
    return write_outputs(root, result)


def analyze_stock_sync(
    ticker: str,
    company: str = "",
    config: Optional[OrchestrationConfig] = None,
    project_root: Optional[Path] = None,
) -> PipelineResult:
    return asyncio.run(analyze_stock(ticker, company, config, project_root))
