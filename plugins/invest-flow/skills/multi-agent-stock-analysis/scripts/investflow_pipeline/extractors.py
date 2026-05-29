from __future__ import annotations

import re
from typing import List

from .models import Handoff


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
