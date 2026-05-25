import unittest
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


class ModelTests(unittest.TestCase):
    def test_stage_result_to_dict_contains_handoff(self):
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.SUCCESS,
            report_path="/tmp/report.md",
            handoff=Handoff(
                conclusion="业务质量稳定",
                recommendation="观望",
                confidence=62,
                key_evidence=["收入增长"],
                risk_flags=["估值偏高"],
                contradiction_points=[],
                monitoring_signals=["下一季收入增速"],
                data_gaps=[],
            ),
            duration=1.5,
            retry_count=0,
        )

        data = result.to_dict()

        self.assertEqual(data["skill_name"], "fundamental-analysis")
        self.assertEqual(data["agent_name"], "fundamental")
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["handoff"]["recommendation"], "观望")
        self.assertEqual(data["handoff"]["confidence"], 62)
        self.assertTrue(result.is_success)

    def test_pipeline_result_to_dict_includes_ordered_stage_results_and_agents_alias(self):
        from investflow_pipeline.models import AnalysisStatus, PipelineResult, StageResult

        first = StageResult(
            skill_name="fundamental-analysis",
            agent_name="shared-agent",
            status=AnalysisStatus.SUCCESS,
        )
        second = StageResult(
            skill_name="gie-investment-framework",
            agent_name="shared-agent",
            status=AnalysisStatus.FAILED,
            errors=["timeout"],
        )
        result = PipelineResult(
            task_id="task-1",
            status="partial",
            intent="stock_analysis",
            target="Tesla",
            ticker="TSLA",
            company_name="Tesla",
            started_at="2026-05-25T09:00:00Z",
            ended_at="2026-05-25T09:01:00Z",
            stage_results=[first, second],
            summary_report_path="/tmp/summary.md",
            orchestration_json_path="/tmp/orchestration.json",
        )

        data = result.to_dict()

        self.assertIn("stage_results", data)
        self.assertEqual(
            [stage["skill_name"] for stage in data["stage_results"]],
            ["fundamental-analysis", "gie-investment-framework"],
        )
        self.assertEqual(
            data["agents"]["shared-agent"]["skill_name"],
            "gie-investment-framework",
        )

    def test_pipeline_result_to_dict_counts_failed_results(self):
        from investflow_pipeline.models import AnalysisStatus, PipelineResult, StageResult

        result = PipelineResult(
            task_id="task-1",
            status="partial",
            intent="stock_analysis",
            target="Tesla",
            ticker="TSLA",
            company_name="Tesla",
            started_at="2026-05-25T09:00:00Z",
            ended_at="2026-05-25T09:01:00Z",
            stage_results=[
                StageResult(
                    skill_name="fundamental-analysis",
                    agent_name="fundamental",
                    status=AnalysisStatus.SUCCESS,
                ),
                StageResult(
                    skill_name="gie-investment-framework",
                    agent_name="gie",
                    status=AnalysisStatus.FAILED,
                ),
                StageResult(
                    skill_name="institutional-accumulation-analysis",
                    agent_name="institutional",
                    status=AnalysisStatus.PARTIAL,
                ),
            ],
            summary_report_path=None,
            orchestration_json_path=None,
        )

        data = result.to_dict()

        self.assertEqual(data["completed_count"], 1)
        self.assertEqual(data["failed_count"], 2)
        self.assertEqual(data["total_count"], 3)

    def test_default_lists_are_isolated(self):
        from investflow_pipeline.models import Handoff, TaskRequest

        first_handoff = Handoff()
        second_handoff = Handoff()
        first_handoff.key_evidence.append("收入增长")

        first_request = TaskRequest(
            task_id="task-1",
            intent="stock_analysis",
            target="Tesla",
        )
        second_request = TaskRequest(
            task_id="task-2",
            intent="stock_analysis",
            target="Nvidia",
        )
        first_request.requested_outputs.append("debug")

        self.assertEqual(second_handoff.key_evidence, [])
        self.assertEqual(second_request.requested_outputs, ["summary", "handoff_json"])


class PathTests(unittest.TestCase):
    def test_find_project_root_finds_agents_md(self):
        from investflow_pipeline.paths import find_project_root

        root = find_project_root()

        self.assertTrue((root / "AGENTS.md").exists())
        self.assertTrue((root / "plugins" / "invest-flow").exists())

    def test_unique_path_adds_numbered_suffix(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import unique_path

        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "report.md"
            first.write_text("existing", encoding="utf-8")

            second = unique_path(first)

        self.assertEqual(second.name, "report(1).md")


if __name__ == "__main__":
    unittest.main()
