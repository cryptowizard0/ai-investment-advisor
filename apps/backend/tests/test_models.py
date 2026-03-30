from app.models.schemas import AnalysisJobRequest


def test_analysis_job_request_defaults() -> None:
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
    assert payload.run_id
