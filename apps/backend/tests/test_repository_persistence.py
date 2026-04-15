import tempfile
import unittest
from pathlib import Path

from app.models.schemas import (
    AnalysisJobRecord,
    AnalysisJobRequest,
    JobEvent,
    ReportRecord,
    ThreadSummary,
)
from app.services.repository import SqliteRepository


class SqliteRepositoryPersistenceTest(unittest.TestCase):
    def test_persists_threads_jobs_events_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "backend.sqlite3"

            first_repo = SqliteRepository(database_path)
            thread = first_repo.create_thread(ThreadSummary(user_id="demo-user", title="TSLA 分析"))
            job_request = AnalysisJobRequest(
                user_id="demo-user",
                thread_id=thread.id,
                analysis_mode="deep_report",
                target_type="ticker",
                target_value="TSLA",
                question="分析 TSLA",
                risk_profile="balanced",
                preferred_language="zh-CN",
                selected_skill_profile="chief-investment-advisor",
            )
            job = first_repo.create_job(
                AnalysisJobRecord(thread_id=thread.id, user_id="demo-user", request=job_request)
            )
            first_repo.append_events(
                job.id,
                [
                    JobEvent(event="job.created", message="created"),
                    JobEvent(event="run.completed", message="completed"),
                ],
            )
            report = first_repo.create_report(
                ReportRecord(
                    thread_id=thread.id,
                    job_id=job.id,
                    user_id="demo-user",
                    title="TSLA 深度分析报告",
                    target_value="TSLA",
                    analysis_mode="deep_report",
                    summary="summary",
                    rating="WATCH",
                    markdown="# report",
                )
            )

            second_repo = SqliteRepository(database_path)

            loaded_thread = second_repo.get_thread(thread.id)
            loaded_job = second_repo.get_job(job.id)
            loaded_events = second_repo.get_events(job.id)
            loaded_report = second_repo.get_report(report.id)

            self.assertIsNotNone(loaded_thread)
            self.assertEqual(loaded_thread.id, thread.id)
            self.assertIsNotNone(loaded_job)
            self.assertEqual(loaded_job.request.target_value, "TSLA")
            self.assertEqual([event.event for event in loaded_events], ["job.created", "run.completed"])
            self.assertIsNotNone(loaded_report)
            self.assertEqual(loaded_report.title, "TSLA 深度分析报告")


if __name__ == "__main__":
    unittest.main()
