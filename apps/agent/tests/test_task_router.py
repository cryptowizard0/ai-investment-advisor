import unittest

from app.runtime.task_router import resolve_skill_profile


class TaskRouterTest(unittest.TestCase):
    def test_resolve_theme_research_default(self) -> None:
        result = resolve_skill_profile("theme_research", "AI 电力基础设施", "")
        self.assertEqual(result, ["chief-investment-advisor", "gie-investment-framework"])

    def test_preferred_profile_wins(self) -> None:
        result = resolve_skill_profile("deep_report", "TSLA", "fundamental-analysis")
        self.assertEqual(result, ["fundamental-analysis"])


if __name__ == "__main__":
    unittest.main()
