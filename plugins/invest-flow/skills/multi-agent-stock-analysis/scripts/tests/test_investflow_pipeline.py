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

    def test_find_project_root_from_nested_path_finds_repo_sentinel(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_project_root

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            plugin_manifest = (
                project_root / "plugins" / "invest-flow" / ".codex-plugin" / "plugin.json"
            )
            nested = project_root / "plugins" / "invest-flow" / "skills"
            nested.mkdir(parents=True)
            plugin_manifest.parent.mkdir(parents=True)
            (project_root / "AGENTS.md").write_text("repo instructions", encoding="utf-8")
            plugin_manifest.write_text('{"name": "invest-flow"}', encoding="utf-8")

            root = find_project_root(start=nested)

        self.assertEqual(root, project_root.resolve())

    def test_find_project_root_rejects_agents_with_git_only(self):
        import os
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_project_root

        with TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "generic-repo"
            nested = fake_root / "src"
            nested.mkdir(parents=True)
            (fake_root / "AGENTS.md").write_text("repo instructions", encoding="utf-8")
            (fake_root / ".git").mkdir()

            old_cwd = Path.cwd()
            try:
                os.chdir(fake_root)
                with self.assertRaisesRegex(RuntimeError, "Unable to locate InvestFlow project root"):
                    find_project_root(start=nested)
            finally:
                os.chdir(old_cwd)

    def test_find_project_root_raises_when_only_agents_parent_and_cwd_invalid(self):
        import os
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_project_root

        with TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "fake-global-root"
            nested = fake_root / "cache" / "plugin"
            nested.mkdir(parents=True)
            (fake_root / "AGENTS.md").write_text("global instructions", encoding="utf-8")

            old_cwd = Path.cwd()
            try:
                os.chdir(fake_root)
                with self.assertRaisesRegex(RuntimeError, "Unable to locate InvestFlow project root"):
                    find_project_root(start=nested)
            finally:
                os.chdir(old_cwd)


    def test_find_report_from_output_returns_existing_output_report(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_report_from_output

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            report = project_root / "output" / "summary" / "综合分析-TSLA.md"
            report.parent.mkdir(parents=True)
            report.write_text("report", encoding="utf-8")

            found = find_report_from_output(project_root, f"saved to {report}")

        self.assertEqual(found, report.resolve())

    def test_find_report_from_output_returns_bare_relative_output_report(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_report_from_output

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            report = project_root / "output" / "fundamental-analysis" / "TSLA.md"
            report.parent.mkdir(parents=True)
            report.write_text("report", encoding="utf-8")

            found = find_report_from_output(
                project_root,
                "saved to output/fundamental-analysis/TSLA.md",
            )

        self.assertEqual(found, report.resolve())

    def test_find_report_from_output_returns_dot_relative_output_report(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_report_from_output

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            report = project_root / "output" / "fundamental-analysis" / "TSLA.md"
            report.parent.mkdir(parents=True)
            report.write_text("report", encoding="utf-8")

            found = find_report_from_output(
                project_root,
                "saved to ./output/fundamental-analysis/TSLA.md",
            )

        self.assertEqual(found, report.resolve())

    def test_find_report_from_output_rejects_markdown_outside_output(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_report_from_output

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            readme = project_root / "README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text("not a report", encoding="utf-8")

            found = find_report_from_output(project_root, f"template: {readme}")

        self.assertIsNone(found)

    def test_find_latest_report_prefers_ticker_match_over_newer_non_ticker_report(self):
        from datetime import datetime, timedelta
        import os
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import find_latest_report

        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            ticker_report = output_dir / "TSLA-analysis.md"
            other_report = output_dir / "NVDA-analysis.md"
            started_at = datetime.now() - timedelta(seconds=1)
            ticker_report.write_text("ticker", encoding="utf-8")
            other_report.write_text("other", encoding="utf-8")
            ticker_ts = started_at.timestamp() + 1
            other_ts = started_at.timestamp() + 2
            os.utime(ticker_report, (ticker_ts, ticker_ts))
            os.utime(other_report, (other_ts, other_ts))

            found = find_latest_report(output_dir, "TSLA", started_at)

        self.assertEqual(found, ticker_report)

    def test_ensure_output_dir_rejects_paths_outside_project_root(self):
        from tempfile import TemporaryDirectory
        from investflow_pipeline.paths import ensure_output_dir

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            outside = Path(tmp) / "outside"

            with self.assertRaises(ValueError):
                ensure_output_dir(project_root, "../outside")
            with self.assertRaises(ValueError):
                ensure_output_dir(project_root, str(outside))


if __name__ == "__main__":
    unittest.main()
