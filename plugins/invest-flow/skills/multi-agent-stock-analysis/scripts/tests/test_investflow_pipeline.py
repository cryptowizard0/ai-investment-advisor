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


class RegistryTests(unittest.TestCase):
    def test_basic_specs_include_three_legacy_agents(self):
        from investflow_pipeline.registry import build_registry

        registry = build_registry()
        specs = registry.basic_stock_specs()
        names = [spec.agent_name for spec in specs]

        self.assertEqual(names, ["fundamental", "institutional", "gie"])
        self.assertTrue(specs[0].required)
        self.assertFalse(specs[1].required)
        self.assertTrue(specs[2].required)

    def test_unified_env_var_overrides_default_command(self):
        import os
        from investflow_pipeline.registry import build_registry

        key = "INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS"
        original = os.environ.get(key)
        os.environ[key] = 'echo "/tmp/custom.md"'
        try:
            registry = build_registry()
            spec = registry.get("fundamental-analysis")
        finally:
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original

        self.assertEqual(spec.command_template, 'echo "/tmp/custom.md"')


class PlannerTests(unittest.TestCase):
    def test_create_stock_request_sets_task_fields(self):
        from investflow_pipeline.planner import create_stock_request

        request = create_stock_request("tsla", "Tesla")

        self.assertEqual(request.intent, "stock_decision_basic")
        self.assertEqual(request.target, "TSLA")
        self.assertEqual(request.ticker, "TSLA")
        self.assertEqual(request.company_name, "Tesla")
        self.assertTrue(request.task_id.startswith("ma_"))

    def test_create_stock_request_rejects_blank_ticker(self):
        from investflow_pipeline.planner import create_stock_request

        with self.assertRaisesRegex(ValueError, "ticker is required"):
            create_stock_request("   ")

    def test_create_stock_request_rejects_malformed_ticker(self):
        from investflow_pipeline.planner import create_stock_request

        for ticker in ("TSLA;rm", "TS LA"):
            with self.subTest(ticker=ticker):
                with self.assertRaisesRegex(ValueError, "invalid ticker"):
                    create_stock_request(ticker)

    def test_create_stock_request_task_id_is_unique_for_immediate_calls(self):
        from investflow_pipeline.planner import create_stock_request

        first = create_stock_request("TSLA")
        second = create_stock_request("TSLA")

        self.assertNotEqual(first.task_id, second.task_id)
        self.assertTrue(first.task_id.startswith("ma_"))
        self.assertTrue(second.task_id.startswith("ma_"))

    def test_basic_plan_uses_three_legacy_specs(self):
        from investflow_pipeline.planner import create_stock_request, plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        specs = plan_basic_stock_analysis(request, build_registry())

        self.assertEqual([spec.agent_name for spec in specs], ["fundamental", "institutional", "gie"])

    def test_basic_plan_rejects_non_basic_intent(self):
        from investflow_pipeline.models import TaskRequest
        from investflow_pipeline.planner import plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = TaskRequest(
            task_id="task-1",
            intent="custom_intent",
            target="TSLA",
            ticker="TSLA",
        )

        with self.assertRaisesRegex(ValueError, "unsupported intent for basic stock analysis: custom_intent"):
            plan_basic_stock_analysis(request, build_registry())

    def test_basic_plan_rejects_direct_request_blank_ticker(self):
        from investflow_pipeline.models import TaskRequest
        from investflow_pipeline.planner import plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = TaskRequest(
            task_id="task-1",
            intent="stock_decision_basic",
            target="TSLA",
            ticker="   ",
        )

        with self.assertRaisesRegex(ValueError, "ticker is required"):
            plan_basic_stock_analysis(request, build_registry())

    def test_basic_plan_rejects_direct_request_malformed_ticker(self):
        from investflow_pipeline.models import TaskRequest
        from investflow_pipeline.planner import plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = TaskRequest(
            task_id="task-1",
            intent="stock_decision_basic",
            target="TSLA",
            ticker="TSLA;rm",
        )

        with self.assertRaisesRegex(ValueError, "invalid ticker"):
            plan_basic_stock_analysis(request, build_registry())

    def test_basic_plan_rejects_direct_request_non_normalized_ticker(self):
        from investflow_pipeline.models import TaskRequest
        from investflow_pipeline.planner import plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = TaskRequest(
            task_id="task-1",
            intent="stock_decision_basic",
            target="TSLA",
            ticker=" TSLA ",
        )

        with self.assertRaisesRegex(ValueError, "ticker must be normalized before planning"):
            plan_basic_stock_analysis(request, build_registry())


class ExtractorTests(unittest.TestCase):
    def test_extract_handoff_reads_conclusion_and_risks(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# TSLA 分析报告

## 投资建议
建议：观望
置信度：68%

## 核心结论
公司长期逻辑仍在，但短期估值偏高。

## 核心证据
- 收入仍保持增长
- 毛利率存在压力

## 风险提示
- 估值回撤风险
- 竞争加剧
"""
        handoff = extract_handoff(markdown)

        self.assertEqual(handoff.recommendation, "观望")
        self.assertEqual(handoff.confidence, 68)
        self.assertIn("公司长期逻辑仍在，但短期估值偏高。", handoff.conclusion)
        self.assertIn("收入仍保持增长", handoff.key_evidence)
        self.assertIn("估值回撤风险", handoff.risk_flags)

    def test_extract_handoff_keeps_child_heading_content_in_parent_section(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# TSLA 分析报告

## 执行摘要
### 一句话 thesis
长期需求仍在，但盈利拐点需要验证。

## 风险提示
- 交付放缓
"""
        handoff = extract_handoff(markdown)

        self.assertIn("长期需求仍在，但盈利拐点需要验证。", handoff.conclusion)

    def test_extract_handoff_strips_bold_recommendation_label(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# TSLA 分析报告

## 投资建议
**操作建议：** 观望
"""
        handoff = extract_handoff(markdown)

        self.assertEqual(handoff.recommendation, "观望")

    def test_extract_handoff_prefers_later_displayed_confidence_over_raw(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# TSLA 分析报告

原始置信度: 54%

## 投资建议
**置信度：** 40%
"""
        handoff = extract_handoff(markdown)

        self.assertEqual(handoff.confidence, 40)


class ExecutorTests(unittest.TestCase):
    def _report_text(self, ticker="TSLA", company="Tesla"):
        return f"""# {ticker} {company} 分析报告

## 投资建议
建议：观望
置信度：60%

## 核心结论
{ticker} 的测试报告用于验证 command mode 可以读取已经落在 output 目录下的 Markdown 报告。结论是当前样本足够完整，可以进入 handoff 提取流程。

## 核心证据
- 报告路径位于 project_root/output 之下，满足 hardened path 规则。
- 内容包含分析、报告、结论等关键标识，长度也超过 executor 的最低校验阈值。
- 建议和置信度字段可被 extract_handoff 稳定读取。

## 风险提示
- 这是单元测试夹具，不代表真实投资观点。
- 命令执行必须定位到报告文件，不能只依赖 stdout 中的长文本。
"""

    def _spec(self, command_template, *, max_retries=1, timeout_seconds=10):
        from investflow_pipeline.models import SkillSpec

        return SkillSpec(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            stage="single_asset_validation",
            command_template=command_template,
            output_dir="output/fundamental-analysis",
            required=True,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    def _python_command(self, script, *args):
        import shlex

        return " ".join(
            shlex.quote(str(part)) for part in (sys.executable, script, *args)
        )

    def test_mock_executor_returns_successful_stage_result(self):
        import asyncio
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        spec = build_registry().get("fundamental-analysis")
        executor = PipelineExecutor(
            config=OrchestrationConfig(execution_mode="mock"),
            project_root=Path.cwd(),
        )

        result = asyncio.run(executor.execute_stage(spec, request))

        self.assertTrue(result.is_success)
        self.assertEqual(result.agent_name, "fundamental")
        self.assertIn("TSLA", result.output)
        self.assertEqual(result.handoff.recommendation, "观望")

    def test_validate_rejects_short_output(self):
        from investflow_pipeline.executor import validate_output

        valid, reason = validate_output("短")

        self.assertFalse(valid)
        self.assertEqual(reason, "输出内容不完整")

    def test_command_mode_succeeds_when_stdout_contains_existing_output_report(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            report = project_root / "output" / "fundamental-analysis" / "TSLA-report.md"
            report.parent.mkdir(parents=True)
            report.write_text(self._report_text(), encoding="utf-8")
            script = project_root / "emit_report.py"
            script.write_text(f"print({str(report)!r})\n", encoding="utf-8")

            executor = PipelineExecutor(
                config=OrchestrationConfig(execution_mode="command", max_retries=0),
                project_root=project_root,
            )
            result = asyncio.run(
                executor.execute_stage(
                    self._spec(self._python_command(script), max_retries=0),
                    create_stock_request("TSLA", "Tesla"),
                )
            )

        self.assertTrue(result.is_success)
        self.assertEqual(result.report_path, str(report.resolve()))
        self.assertIn("核心结论", result.output)
        self.assertEqual(result.handoff.recommendation, "观望")

    def test_command_mode_fails_when_no_report_path_is_found(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            script = project_root / "emit_stdout_only.py"
            script.write_text(f"print({self._report_text()!r})\n", encoding="utf-8")

            executor = PipelineExecutor(
                config=OrchestrationConfig(execution_mode="command", max_retries=0),
                project_root=project_root,
            )
            result = asyncio.run(
                executor.execute_stage(
                    self._spec(self._python_command(script), max_retries=0),
                    create_stock_request("TSLA", "Tesla"),
                )
            )

        self.assertFalse(result.is_success)
        self.assertIn("命令执行完成，但未定位到输出报告文件", result.errors)

    def test_spec_max_retries_zero_prevents_retry_after_invalid_output(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request

        script_content = """
from pathlib import Path

attempts = Path("attempts.txt")
count = int(attempts.read_text(encoding="utf-8")) if attempts.exists() else 0
attempts.write_text(str(count + 1), encoding="utf-8")
report = Path("output/fundamental-analysis/TSLA-short.md")
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text("短", encoding="utf-8")
print(report)
"""

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            script = project_root / "short_report.py"
            script.write_text(script_content, encoding="utf-8")

            executor = PipelineExecutor(
                config=OrchestrationConfig(execution_mode="command", max_retries=1),
                project_root=project_root,
            )
            result = asyncio.run(
                executor.execute_stage(
                    self._spec(self._python_command(script), max_retries=0),
                    create_stock_request("TSLA", "Tesla"),
                )
            )
            attempts = (project_root / "attempts.txt").read_text(encoding="utf-8")

        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[-1], "输出内容不完整")
        self.assertEqual(attempts, "1")

    def test_command_nonzero_exit_returns_failed_result(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            script = project_root / "fail.py"
            script.write_text(
                'import sys\nprint("boom")\nsys.exit(7)\n',
                encoding="utf-8",
            )

            executor = PipelineExecutor(
                config=OrchestrationConfig(execution_mode="command", max_retries=0),
                project_root=project_root,
            )
            result = asyncio.run(
                executor.execute_stage(
                    self._spec(self._python_command(script), max_retries=0),
                    create_stock_request("TSLA", "Tesla"),
                )
            )

        self.assertFalse(result.is_success)
        self.assertIn("命令执行失败", result.errors[0])

    def test_blank_company_formats_as_target(self):
        import asyncio
        from tempfile import TemporaryDirectory
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request

        script_content = f"""
from pathlib import Path
import sys

company = sys.argv[1]
report = Path("output/fundamental-analysis") / f"{{company}}-report.md"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text({self._report_text("TSLA", "TSLA")!r}, encoding="utf-8")
print(report)
"""

        with TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            script = project_root / "company_arg.py"
            script.write_text(script_content, encoding="utf-8")

            executor = PipelineExecutor(
                config=OrchestrationConfig(execution_mode="command", max_retries=0),
                project_root=project_root,
            )
            result = asyncio.run(
                executor.execute_stage(
                    self._spec(
                        self._python_command(script, "{company}"),
                        max_retries=0,
                    ),
                    create_stock_request("TSLA"),
                )
            )

        self.assertTrue(result.is_success)
        self.assertTrue(result.report_path.endswith("TSLA-report.md"))


if __name__ == "__main__":
    unittest.main()
