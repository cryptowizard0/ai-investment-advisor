from app.runtime.task_router import resolve_skill_profile


def test_resolve_theme_research_default() -> None:
    result = resolve_skill_profile("theme_research", "AI 电力基础设施", "")
    assert result == ["chief-investment-advisor", "gie-investment-framework"]
