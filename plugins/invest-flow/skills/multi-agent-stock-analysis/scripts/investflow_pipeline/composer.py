from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import List

from .models import AnalysisStatus, CompanyProfile, PipelineResult, StageResult
from .paths import ensure_output_dir, unique_path


def _normalize_text(value: str) -> str:
    compact = " ".join((value or "").replace("\n", " ").split())
    return "".join(ch for ch in compact if ch >= " " or ch == "\t").strip()


def _table_cell(value: str, fallback: str) -> str:
    text = _normalize_text(value) or fallback
    return text.replace("|", r"\|")


def _safe_symbol_token(*candidates: str) -> str:
    raw = ""
    for candidate in candidates:
        candidate = (candidate or "").strip()
        if candidate:
            raw = candidate
            break
    upper = raw.upper()
    sanitized = re.sub(r"[^A-Z0-9._-]+", "_", upper)
    sanitized = re.sub(r"_+", "_", sanitized).strip("._-")
    return sanitized or "UNKNOWN"


def _safe_unique_path(summary_dir: Path, filename: str) -> Path:
    candidate = unique_path(summary_dir / filename).resolve()
    try:
        candidate.relative_to(summary_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"Output path escapes summary dir: {candidate}") from exc
    return candidate


def _line_items(values: List[str], fallback: str) -> str:
    cleaned = [_normalize_text(value) for value in values]
    cleaned = [value for value in cleaned if value]
    if not cleaned:
        return f"- {_normalize_text(fallback)}"
    return "\n".join(f"- {value.replace('|', r'\|')}" for value in cleaned)


def _stage_table(results: List[StageResult]) -> str:
    lines = [
        "| 分析维度 | Agent | 状态 | 结论摘要 | 置信度 | 报告路径 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for stage in results:
        conclusion = _normalize_text(stage.handoff.conclusion) or "无结论"
        if len(conclusion) > 40:
            conclusion = f"{conclusion[:37]}..."
        confidence = (
            str(stage.handoff.confidence) if stage.handoff.confidence is not None else "N/A"
        )
        report_path = stage.report_path or "-"
        lines.append(
            f"| {_table_cell(stage.skill_name, '-')} | {_table_cell(stage.agent_name, '-')} "
            f"| {_table_cell(stage.status.value, '-')} | {_table_cell(conclusion, '无结论')} "
            f"| {_table_cell(confidence, 'N/A')} | {_table_cell(report_path, '-')} |"
        )
    return "\n".join(lines)


def _join_values(values: List[str], fallback: str = "不确定") -> str:
    cleaned = [_normalize_text(value) for value in values if _normalize_text(value)]
    return "、".join(cleaned) if cleaned else fallback


def _find_company_profile_stage(results: List[StageResult]) -> StageResult | None:
    for stage in results:
        if stage.skill_name == "company-profile":
            return stage
    return None


def _profile_from_stage(stage: StageResult | None) -> CompanyProfile | None:
    if stage is None:
        return None
    return stage.handoff.company_profile


def _company_profile_summary(results: List[StageResult]) -> str:
    stage = _find_company_profile_stage(results)
    if stage is not None and stage.status == AnalysisStatus.FAILED:
        note = "缺少公司画像会降低整体判断可信度。"
        return (
            "| 项目 | 内容 |\n"
            "| --- | --- |\n"
            f"| 公司画像状态 | {_table_cell(note, '不确定')} |"
        )

    profile = _profile_from_stage(stage)
    if profile is None:
        note = "公司画像未生成，后续结论只能依赖投资维度报告。"
        return (
            "| 项目 | 内容 |\n"
            "| --- | --- |\n"
            f"| 公司画像状态 | {_table_cell(note, '不确定')} |"
        )

    ai_context = profile.ai_relevance or "不确定"
    ai_positions = _join_values(profile.ai_value_chain_position, "")
    if ai_positions:
        ai_context = f"{ai_context} / {ai_positions}"

    rows = [
        ("公司一句话定义", profile.one_liner),
        ("核心业务", profile.business_summary),
        ("收入来源", profile.revenue_model),
        ("核心技术 / 壁垒", _join_values(profile.technical_advantages)),
        ("产业链位置", profile.industry_chain_position),
        ("AI 相关性", ai_context),
        ("主要竞争对手", _join_values(profile.competitors)),
        ("行业地位", profile.industry_position),
        ("关键不确定性", _join_values(profile.key_uncertainties)),
    ]
    lines = ["| 项目 | 内容 |", "| --- | --- |"]
    lines.extend(
        f"| {_table_cell(label, '-')} | {_table_cell(value, '不确定')} |"
        for label, value in rows
    )
    return "\n".join(lines)


def _subreport_index(results: List[StageResult]) -> str:
    if not results:
        return "- 暂无子报告"
    lines = []
    for stage in results:
        if stage.report_path:
            lines.append(f"- **{stage.skill_name}**：{stage.report_path}")
        else:
            lines.append(
                f"- **{stage.skill_name}**：未生成子报告链接（{stage.status.value}）"
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
    monitoring_signals: List[str] = []
    for stage in success_results:
        evidence_items.extend(stage.handoff.key_evidence)
        conflicts.extend(stage.handoff.contradiction_points)
        risks.extend(stage.handoff.risk_flags)
        decisions.append(
            f"{stage.skill_name}: {stage.handoff.recommendation or '未提供建议'}"
        )
        data_gaps.extend(stage.handoff.data_gaps)
        monitoring_signals.extend(stage.handoff.monitoring_signals)

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
        f"## 公司画像摘要\n{_company_profile_summary(result.stage_results)}\n\n"
        f"## 执行摘要\n{execution_summary}\n\n"
        f"## 分析维度总览\n{_stage_table(result.stage_results)}\n\n"
        f"## 证据汇总\n{_line_items(evidence_items, '暂无关键证据')}\n\n"
        f"## 分歧与冲突\n{_line_items(conflicts, '当前无显著分歧')}\n\n"
        f"## 风险清单\n{_line_items(risks, '暂无新增风险信号')}\n\n"
        f"## 决策看板\n{_line_items(decisions, '暂无可执行建议')}\n\n"
        f"## 数据缺口与失败阶段说明\n{_line_items(data_gaps, '无明显数据缺口')}\n\n"
        f"## 后续跟踪信号\n{_line_items(monitoring_signals, '暂无后续跟踪信号')}\n\n"
        f"## 子报告索引\n{_subreport_index(result.stage_results)}\n\n"
        f"## 投资免责声明\n"
        f"- 本报告仅用于研究与教育目的，不构成任何投资建议。\n"
        f"- 市场有风险，投资需结合个人风险承受能力独立决策。\n"
    )


def compose_prompt_plan(result: PipelineResult) -> str:
    prompt_lines = []
    for index, stage in enumerate(result.stage_results, start=1):
        prompt_lines.append(
            f"### {index}. {stage.skill_name}\n\n"
            f"Agent：{stage.agent_name}\n\n"
            f"```text\n{stage.prompt or stage.output}\n```"
        )

    return (
        f"# Codex Prompt 编排计划 - {result.ticker}\n\n"
        f"作者：InvestmentFlow\n\n"
        f"## 任务信息\n"
        f"- 任务ID：{result.task_id}\n"
        f"- 标的：{result.ticker or result.target} {result.company_name}\n"
        f"- 状态：{result.status}\n"
        f"- 开始时间：{result.started_at}\n"
        f"- 生成时间：{result.ended_at}\n\n"
        f"## 执行方式\n"
        f"在当前 Codex 会话中依次执行以下 prompt，完成所有子 skill 后，"
        f"按综合模板汇总结论、证据、分歧、风险和数据缺口。\n\n"
        f"## 子 Skill Prompts\n\n"
        f"{chr(10).join(prompt_lines)}\n"
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
    ticker = _safe_symbol_token(result.ticker, result.target)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = _safe_unique_path(
        summary_dir, f"orchestration-{ticker}-{timestamp}.json"
    )

    summary_path = None
    if any(stage.status == AnalysisStatus.SUCCESS for stage in result.stage_results):
        summary_name = f"综合分析-{ticker}-{_summary_date(result.ended_at)}.md"
        summary_path = _safe_unique_path(summary_dir, summary_name)

    prompt_plan_path = None
    if result.status == "prompt_plan":
        prompt_plan_path = _safe_unique_path(
            summary_dir, f"prompt-plan-{ticker}-{timestamp}.md"
        )

    final_result = replace(
        result,
        summary_report_path=str(summary_path) if summary_path else None,
        orchestration_json_path=str(json_path),
        prompt_plan_path=str(prompt_plan_path) if prompt_plan_path else None,
    )

    if summary_path:
        summary_path.write_text(compose_summary(final_result), encoding="utf-8")
    if prompt_plan_path:
        prompt_plan_path.write_text(compose_prompt_plan(final_result), encoding="utf-8")
    json_path.write_text(
        json.dumps(final_result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return final_result
