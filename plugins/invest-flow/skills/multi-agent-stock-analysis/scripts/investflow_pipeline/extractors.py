from __future__ import annotations

import re
from typing import List

from .models import Handoff


def _section(markdown: str, names: List[str]) -> str:
    lines = markdown.splitlines()
    start = None
    for name in names:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") and name in stripped:
                start = index + 1
                break
        if start is not None:
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
