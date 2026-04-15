import unittest

from app.models.schemas import AnalysisJobRequest


class AnalysisJobRequestTest(unittest.TestCase):
    def test_defaults_generate_run_id(self) -> None:
        payload = AnalysisJobRequest(
            user_id="u1",
            thread_id="t1",
            analysis_mode="deep_report",
            target_type="ticker",
            target_value="TSLA",
            question="分析 TSLA",
            risk_profile="balanced",
            preferred_language="zh-CN",
            selected_skill_profile="chief-investment-advisor",
        )
        self.assertTrue(payload.run_id)


if __name__ == "__main__":
    unittest.main()
