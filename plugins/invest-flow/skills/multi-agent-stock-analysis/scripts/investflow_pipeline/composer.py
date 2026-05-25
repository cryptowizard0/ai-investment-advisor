from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import List

from .models import AnalysisStatus, PipelineResult, StageResult
from .paths import ensure_output_dir, unique_path


def _line_items(values: List[str], fallback: str) -> str:
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return f"- {fallback}"
    return "\n".join(f"- {value}" for value in cleaned)


def _stage_table(results: List[StageResult]) -> str:
    lines = [
        "| 分析维度 | Agent | 状态 | 结论摘要 | 置信度 | 报告路径 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for stage in results:
        conclusion = stage.handoff.conclusion.strip() or "无结论"
        if len(conclusion) > 40:
            conclusion = f"{conclusion[:37]}..."
        confidence = (
            str(stage.handoff.confidence) if stage.handoff.confidence is not None else "N/A"
        )
        report_path = stage.report_path or "-"
        lines.append(
            f"| {stage.skill_name} | {stage.agent_name} | {stage.status.value} | "
            f"{conclusion} | {confidence} | {report_path} |"
        )
    return "\n".join(lines)


def compose_summary(result: PipelineResult) -> str:
    success_results = [stage for stage in result.stage_results if stage.is_success]
    failed_results = [stage for stage in result.stage_results if not stage.is_success]

    evidence_items: List[str] = []
    conflicts: List[str] = []
    risks: List[str] = []
    decisions: List[str] = []
    data_gaps: List[str] = []
    subreports: List[str] = []
    for stage in success_results:
        evidence_items.extend(stage.handoff.key_evidence)
        conflicts.extend(stage.handoff.contradiction_points)
        risks.extend(stage.handoff.risk_flags)
        decisions.append(
            f"{stage.skill_name}: {stage.handoff.recommendation or '未提供建议'}"
        )
        data_gaps.extend(stage.handoff.data_gaps)
        if stage.report_path:
            subreports.append(f"{stage.skill_name}: {stage.report_path}")

    failed_notes = [
        f"{stage.skill_name}({stage.agent_name}) 失败: {'; '.join(stage.errors) or '未知错误'}"
        for stage in failed_results
    ]
    data_gaps.extend(failed_notes)

    execution_summary = (
        f"任务ID：{result.task_id}\n"
        f"标的：{result.ticker or result.target} {result.company_name}\n"
        f"执行状态：{result.status}\n"
        f"开始时间：{result.started_at}\n"
        f"结束时间：{result.ended_at}\n"
        f"成功阶段：{len(success_results)}/{len(result.stage_results)}"
    )

    return (
        f"# 综合分析报告 - {result.ticker}\n\n"
        f"作者：InvestmentFlow\n\n"
        f"## 执行摘要\n{execution_summary}\n\n"
        f"## 分析维度总览\n{_stage_table(result.stage_results)}\n\n"
        f"## 证据汇总\n{_line_items(evidence_items, '暂无关键证据')}\n\n"
        f"## 分歧与冲突\n{_line_items(conflicts, '当前无显著分歧')}\n\n"
        f"## 风险清单\n{_line_items(risks, '暂无新增风险信号')}\n\n"
        f"## 决策看板\n{_line_items(decisions, '暂无可执行建议')}\n\n"
        f"## 数据缺口与失败阶段说明\n{_line_items(data_gaps, '无明显数据缺口')}\n\n"
        f"## 子报告索引\n{_line_items(subreports, '暂无子报告路径')}\n\n"
        f"## 投资免责声明\n"
        f"- 本报告仅用于研究与教育目的，不构成任何投资建议。\n"
        f"- 市场有风险，投资需结合个人风险承受能力独立决策。\n"
    )


def _summary_date(ended_at: str) -> str:
    normalized = ended_at.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def write_outputs(project_root: Path, result: PipelineResult) -> PipelineResult:
    summary_dir = ensure_output_dir(project_root, "output/summary")
    ticker = (result.ticker or result.target or "UNKNOWN").upper()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = unique_path(summary_dir / f"orchestration-{ticker}-{timestamp}.json").resolve()

    updated = replace(result, orchestration_json_path=str(json_path))
    json_payload = updated.to_dict()
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not any(stage.status == AnalysisStatus.SUCCESS for stage in result.stage_results):
        return replace(updated, summary_report_path=None)

    summary_name = f"综合分析-{ticker}-{_summary_date(result.ended_at)}.md"
    summary_path = unique_path(summary_dir / summary_name).resolve()
    final_result = replace(updated, summary_report_path=str(summary_path))
    summary_path.write_text(compose_summary(final_result), encoding="utf-8")
    return final_result
