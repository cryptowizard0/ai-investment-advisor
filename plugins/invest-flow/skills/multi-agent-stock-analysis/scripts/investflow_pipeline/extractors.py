from __future__ import annotations

import re
from typing import List

from .models import CompanyProfile, Handoff


def _strip_markdown_emphasis(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^(?:[*_`]{1,3}\s*)+", "", stripped)
    stripped = re.sub(r"(?:\s*[*_`]{1,3})+$", "", stripped)
    return stripped.strip()


def _remove_markdown_markers(text: str) -> str:
    return re.sub(r"[*_`]+", "", text).strip()


def _heading(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s*(.*?)\s*$", line.strip())
    if not match:
        return None
    text = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
    return len(match.group(1)), _strip_markdown_emphasis(text)


def _section(markdown: str, names: List[str]) -> str:
    lines = markdown.splitlines()
    start = None
    matched_level = None
    for name in names:
        for index, line in enumerate(lines):
            heading = _heading(line)
            if heading and name in heading[1]:
                start = index + 1
                matched_level = heading[0]
                break
        if start is not None:
            break
    if start is None or matched_level is None:
        return ""
    collected: List[str] = []
    for line in lines[start:]:
        heading = _heading(line)
        if heading and heading[0] <= matched_level:
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
        if _heading(stripped):
            continue
        if stripped and not stripped.startswith("- ") and not stripped.startswith("* "):
            return _strip_markdown_emphasis(stripped)
    return ""


def _label_value(markdown: str, label: str) -> str:
    pattern = re.compile(rf"^[\-*]\s*{re.escape(label)}[:：]\s*(.*?)\s*$")
    for line in markdown.splitlines():
        match = pattern.match(line.strip())
        if match:
            return _strip_markdown_emphasis(match.group(1))
    return ""


def _split_delimited_values(value: str) -> List[str]:
    return [
        _strip_markdown_emphasis(item)
        for item in re.split(r"[，,；;]", value)
        if _strip_markdown_emphasis(item)
    ]


def _section_bullets(markdown: str, names: List[str]) -> List[str]:
    return [_strip_markdown_emphasis(value) for value in _bullets(_section(markdown, names))]


def _split_data_sources_and_uncertainties(text: str) -> tuple[List[str], List[str]]:
    data_sources: List[str] = []
    key_uncertainties: List[str] = []
    in_uncertainties = False
    for line in text.splitlines():
        stripped = line.strip()
        if "主要不确定性" in _remove_markdown_markers(stripped):
            in_uncertainties = True
            continue
        if stripped.startswith("- "):
            value = _strip_markdown_emphasis(stripped[2:].strip())
        elif stripped.startswith("* "):
            value = _strip_markdown_emphasis(stripped[2:].strip())
        else:
            continue
        if in_uncertainties:
            key_uncertainties.append(value)
        else:
            data_sources.append(value)
    return data_sources, key_uncertainties


def _first_section_line(markdown: str, names: List[str]) -> str:
    return _first_nonempty_line(_section(markdown, names))


def _extract_ai_relevance(markdown: str) -> str:
    labeled = _label_value(markdown, "相关性")
    if labeled:
        return labeled.split("；", 1)[0].split(";", 1)[0].strip()
    summary = _label_value(markdown, "AI 相关性结论")
    if "；" in summary:
        return summary.split("；", 1)[0].strip()
    if ";" in summary:
        return summary.split(";", 1)[0].strip()
    return summary


def _extract_recommendation(markdown: str) -> str:
    patterns = [
        r"操作建议[:：]\s*([^\n\r]+)",
        r"建议[:：]\s*([^\n\r]+)",
        r"操作评级[:：]\s*([^\n\r]+)",
        r"最终结论[:：]\s*([^\n\r]+)",
    ]
    for line in markdown.splitlines():
        plain_line = _remove_markdown_markers(line)
        for pattern in patterns:
            match = re.search(pattern, plain_line)
            if match:
                return _strip_markdown_emphasis(match.group(1))
    return ""


def _extract_confidence(markdown: str) -> int | None:
    final_values: List[int] = []
    normal_values: List[int] = []
    raw_values: List[int] = []
    for line in markdown.splitlines():
        plain_line = _remove_markdown_markers(line)
        match = re.search(r"(最终置信度|原始置信度|置信度)[:：]?\s*(\d{1,3})\s*%", plain_line)
        if not match:
            continue
        value = max(0, min(100, int(match.group(2))))
        label = match.group(1)
        if label == "最终置信度":
            final_values.append(value)
        elif label == "置信度":
            normal_values.append(value)
        else:
            raw_values.append(value)

    if final_values:
        return final_values[-1]
    if normal_values:
        return normal_values[-1]
    if raw_values:
        return raw_values[-1]
    return None


def _extract_recommendation_like_line(text: str, label: str) -> str:
    for line in text.splitlines():
        plain_line = _remove_markdown_markers(line)
        match = re.search(rf"{re.escape(label)}[:：]\s*([^\n\r]+)", plain_line)
        if match:
            return _strip_markdown_emphasis(match.group(1))
    return ""


def _extract_company_profile(markdown: str) -> CompanyProfile | None:
    if "公司画像" not in markdown:
        return None

    core_products = _section_bullets(markdown, ["核心业务与收入结构"])
    technical_section = _section(markdown, ["核心技术优势", "技术壁垒"])
    technical_advantages = [
        bullet
        for bullet in _section_bullets(markdown, ["核心技术优势", "技术壁垒"])
        if not bullet.startswith("护城河判断：")
    ]
    ai_positions = []
    for bullet in _section_bullets(markdown, ["AI 产业链相关性"]):
        if bullet.startswith("位置："):
            ai_positions.append(_strip_markdown_emphasis(bullet.split("：", 1)[1]))
    competitors = _section_bullets(markdown, ["竞争对手与行业地位"])
    pre_questions = _section_bullets(markdown, ["投资分析前置问题"])
    data_sources, uncertainty_bullets = _split_data_sources_and_uncertainties(
        _section(markdown, ["数据来源与不确定性"])
    )
    key_uncertainties = [
        value
        for value in [_label_value(markdown, "最重要的不确定性")]
        if value
    ]
    key_uncertainties.extend(uncertainty_bullets)

    profile = CompanyProfile(
        one_liner=_label_value(markdown, "公司一句话定义"),
        business_summary=_label_value(markdown, "核心业务"),
        core_products=core_products,
        revenue_model=_label_value(markdown, "收入来源"),
        customers_and_end_markets=_split_delimited_values(
            _label_value(markdown, "主要客户 / 下游需求")
        ),
        technical_advantages=technical_advantages,
        moat_assessment=_extract_recommendation_like_line(technical_section, "护城河判断"),
        industry_chain_position=_first_section_line(markdown, ["产业链位置"]),
        ai_relevance=_extract_ai_relevance(markdown),
        ai_value_chain_position=ai_positions,
        competitors=competitors,
        industry_position=_extract_recommendation_like_line(
            _section(markdown, ["竞争对手与行业地位"]),
            "行业地位",
        ),
        key_uncertainties=key_uncertainties,
        pre_analysis_questions=pre_questions,
        data_sources=data_sources,
    )
    return profile


def _company_profile_data_gaps(profile: CompanyProfile | None) -> List[str]:
    if profile is None:
        return []
    required_strings = {
        "one_liner": profile.one_liner,
        "business_summary": profile.business_summary,
        "revenue_model": profile.revenue_model,
        "industry_chain_position": profile.industry_chain_position,
        "ai_relevance": profile.ai_relevance,
        "industry_position": profile.industry_position,
    }
    required_lists = {
        "core_products": profile.core_products,
        "technical_advantages": profile.technical_advantages,
        "ai_value_chain_position": profile.ai_value_chain_position,
        "competitors": profile.competitors,
        "key_uncertainties": profile.key_uncertainties,
        "pre_analysis_questions": profile.pre_analysis_questions,
        "data_sources": profile.data_sources,
    }
    gaps = [
        f"company_profile.{name} missing"
        for name, value in required_strings.items()
        if not value
    ]
    gaps.extend(
        f"company_profile.{name} missing"
        for name, values in required_lists.items()
        if not values
    )
    return gaps


def extract_handoff(markdown: str) -> Handoff:
    conclusion_section = _section(markdown, ["核心结论", "投资建议", "执行摘要"])
    evidence_section = _section(markdown, ["核心证据", "关键证据", "核心逻辑"])
    risk_section = _section(markdown, ["风险提示", "主要风险", "高风险因素"])
    monitoring_section = _section(markdown, ["监控指标", "跟踪指标", "Dashboard"])
    gaps_section = _section(markdown, ["数据缺口", "信息缺口", "待验证"])

    conclusion = _first_nonempty_line(conclusion_section)
    if not conclusion:
        conclusion = _first_nonempty_line(markdown)

    company_profile = _extract_company_profile(markdown)
    data_gaps = _bullets(gaps_section)
    data_gaps.extend(_company_profile_data_gaps(company_profile))

    return Handoff(
        conclusion=conclusion,
        recommendation=_extract_recommendation(markdown),
        confidence=_extract_confidence(markdown),
        key_evidence=_bullets(evidence_section),
        risk_flags=_bullets(risk_section),
        contradiction_points=_bullets(_section(markdown, ["冲突", "分歧"])),
        monitoring_signals=_bullets(monitoring_section),
        data_gaps=data_gaps,
        company_profile=company_profile,
    )
