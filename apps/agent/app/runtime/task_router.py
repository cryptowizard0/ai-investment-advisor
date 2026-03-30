from __future__ import annotations


def resolve_skill_profile(analysis_mode: str, target_value: str, preferred_profile: str) -> list[str]:
    if preferred_profile:
        return [preferred_profile]
    if "gold" in target_value.lower():
        return ["gold-trend-analysis"]
    if analysis_mode == "quick_scan":
        return ["reflexivity-quick-scan"]
    if analysis_mode == "theme_research":
        return ["chief-investment-advisor", "gie-investment-framework"]
    return ["chief-investment-advisor"]
