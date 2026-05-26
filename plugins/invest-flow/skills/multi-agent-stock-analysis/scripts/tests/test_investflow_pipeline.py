import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


class ModelTests(unittest.TestCase):
    def test_stage_result_to_dict_contains_prompt_and_handoff(self):
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.PENDING,
            prompt="使用 invest-flow:fundamental-analysis 分析 TSLA",
            handoff=Handoff(data_gaps=["等待执行"]),
        )

        data = result.to_dict()

        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["prompt"], "使用 invest-flow:fundamental-analysis 分析 TSLA")
        self.assertEqual(data["handoff"]["data_gaps"], ["等待执行"])
        self.assertFalse(result.is_success)

    def test_pipeline_result_to_dict_counts_success_failed_and_pending(self):
        from investflow_pipeline.models import AnalysisStatus, PipelineResult, StageResult

        result = PipelineResult(
            task_id="task-1",
            status="prompt_plan",
            intent="stock_decision_basic",
            target="TSLA",
            ticker="TSLA",
            company_name="Tesla",
            started_at="2026-05-25T09:00:00Z",
            ended_at="2026-05-25T09:01:00Z",
            stage_results=[
                StageResult("fundamental-analysis", "fundamental", AnalysisStatus.SUCCESS),
                StageResult("gie-investment-framework", "gie", AnalysisStatus.FAILED),
                StageResult(
                    "institutional-accumulation-analysis",
                    "institutional",
                    AnalysisStatus.PENDING,
                ),
            ],
            summary_report_path=None,
            orchestration_json_path="/tmp/orchestration.json",
            prompt_plan_path="/tmp/prompt-plan.md",
        )

        data = result.to_dict()

        self.assertEqual(data["completed_count"], 1)
        self.assertEqual(data["failed_count"], 1)
        self.assertEqual(data["pending_count"], 1)
        self.assertEqual(data["total_count"], 3)
        self.assertEqual(data["prompt_plan_path"], "/tmp/prompt-plan.md")

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
        from investflow_pipeline.paths import unique_path

        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "report.md"
            first.write_text("existing", encoding="utf-8")

            second = unique_path(first)

        self.assertEqual(second.name, "report(1).md")

    def test_ensure_output_dir_rejects_paths_outside_project_root(self):
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
    def test_basic_specs_are_codex_prompt_templates(self):
        from investflow_pipeline.registry import build_registry

        registry = build_registry()
        specs = registry.basic_stock_specs()

        self.assertEqual(
            [spec.skill_name for spec in specs],
            [
                "fundamental-analysis",
                "institutional-accumulation-analysis",
                "gie-investment-framework",
            ],
        )
        for spec in specs:
            self.assertIn("使用 invest-flow:", spec.prompt_template)
            self.assertIn("{ticker}", spec.prompt_template)
            self.assertFalse(hasattr(spec, "com" + "mand" + "_template"))

    def test_basic_specs_include_expected_agents_and_required_flags(self):
        from investflow_pipeline.registry import build_registry

        specs = build_registry().basic_stock_specs()

        self.assertEqual(
            [spec.agent_name for spec in specs],
            ["fundamental", "institutional", "gie"],
        )
        self.assertTrue(specs[0].required)
        self.assertFalse(specs[1].required)
        self.assertTrue(specs[2].required)

    def test_gie_prompt_includes_company_fallback_slot(self):
        from investflow_pipeline.registry import build_registry

        spec = build_registry().get("gie-investment-framework")

        self.assertEqual(
            spec.prompt_template,
            "使用 invest-flow:gie-investment-framework 分析 {ticker} / {company}",
        )


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

    def test_basic_plan_uses_three_prompt_specs(self):
        from investflow_pipeline.planner import create_stock_request, plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        specs = plan_basic_stock_analysis(request, build_registry())

        self.assertEqual(
            [spec.agent_name for spec in specs],
            ["fundamental", "institutional", "gie"],
        )

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

        with self.assertRaisesRegex(ValueError, "unsupported intent"):
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


class ExecutorTests(unittest.TestCase):
    def test_validate_rejects_short_output(self):
        from investflow_pipeline.executor import validate_output

        valid, reason = validate_output("短")

        self.assertFalse(valid)
        self.assertEqual(reason, "输出内容不完整")

    def test_executor_returns_pending_prompt_plan_stage(self):
        import asyncio
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import AnalysisStatus, OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("MRVL", "Marvell Technology")
        spec = build_registry().get("gie-investment-framework")
        executor = PipelineExecutor(
            config=OrchestrationConfig(),
            project_root=Path.cwd(),
        )

        result = asyncio.run(executor.execute_stage(spec, request))

        self.assertEqual(result.status, AnalysisStatus.PENDING)
        self.assertEqual(
            result.prompt,
            "使用 invest-flow:gie-investment-framework 分析 MRVL / Marvell Technology",
        )
        self.assertEqual(result.output, result.prompt)
        self.assertIn("等待 Codex 当前会话执行", result.handoff.data_gaps[0])

    def test_blank_company_formats_as_target(self):
        import asyncio
        from investflow_pipeline.executor import PipelineExecutor
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.planner import create_stock_request
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("MRVL")
        spec = build_registry().get("gie-investment-framework")
        executor = PipelineExecutor(
            config=OrchestrationConfig(),
            project_root=Path.cwd(),
        )

        result = asyncio.run(executor.execute_stage(spec, request))

        self.assertEqual(
            result.prompt,
            "使用 invest-flow:gie-investment-framework 分析 MRVL / MRVL",
        )


class ComposerTests(unittest.TestCase):
    def _pipeline_result(self, stage_results, *, status="partial_success"):
        from investflow_pipeline.models import PipelineResult

        return PipelineResult(
            task_id="task-compose-1",
            status=status,
            intent="stock_decision_basic",
            target="TSLA",
            ticker="TSLA",
            company_name="Tesla",
            started_at="2026-05-25T09:00:00Z",
            ended_at="2026-05-25T09:01:00Z",
            stage_results=stage_results,
            summary_report_path=None,
            orchestration_json_path=None,
        )

    def test_write_outputs_success_creates_json_and_markdown(self):
        from investflow_pipeline.composer import write_outputs
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        success_stage = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.SUCCESS,
            report_path="/tmp/fundamental.md",
            handoff=Handoff(
                recommendation="观望",
                key_evidence=["收入保持增长"],
                risk_flags=["估值回撤风险"],
            ),
        )
        failed_stage = StageResult(
            skill_name="gie-investment-framework",
            agent_name="gie",
            status=AnalysisStatus.FAILED,
            errors=["timeout"],
        )
        result = self._pipeline_result([success_stage, failed_stage])

        with TemporaryDirectory() as tmp:
            written = write_outputs(Path(tmp), result)
            json_path = Path(written.orchestration_json_path)
            md_path = Path(written.summary_report_path)
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            content = md_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertIn("作者：InvestmentFlow", content)
        self.assertEqual(payload["summary_report_path"], written.summary_report_path)

    def test_write_outputs_failed_only_creates_json_without_markdown(self):
        from investflow_pipeline.composer import write_outputs
        from investflow_pipeline.models import AnalysisStatus, StageResult

        failed_stage = StageResult(
            skill_name="institutional-accumulation-analysis",
            agent_name="institutional",
            status=AnalysisStatus.FAILED,
            errors=["no report"],
        )
        result = self._pipeline_result([failed_stage], status="failed")

        with TemporaryDirectory() as tmp:
            written = write_outputs(Path(tmp), result)
            json_path = Path(written.orchestration_json_path)
            payload = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertIsNone(written.summary_report_path)
        self.assertIsNone(written.prompt_plan_path)
        self.assertEqual(payload["failed_count"], 1)

    def test_write_outputs_prompt_plan_creates_plan_markdown_and_json(self):
        from investflow_pipeline.composer import write_outputs
        from investflow_pipeline.models import AnalysisStatus, StageResult

        pending_stage = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.PENDING,
            prompt="使用 invest-flow:fundamental-analysis 分析 MRVL",
        )
        result = self._pipeline_result([pending_stage], status="prompt_plan")
        result.ticker = "MRVL"
        result.target = "MRVL"
        result.company_name = "Marvell Technology"

        with TemporaryDirectory() as tmp:
            written = write_outputs(Path(tmp), result)
            json_path = Path(written.orchestration_json_path)
            plan_path = Path(written.prompt_plan_path)
            self.assertTrue(json_path.exists())
            self.assertTrue(plan_path.exists())
            plan = plan_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertIsNone(written.summary_report_path)
        self.assertIn("Codex Prompt 编排计划", plan)
        self.assertIn("使用 invest-flow:fundamental-analysis 分析 MRVL", plan)
        self.assertEqual(payload["status"], "prompt_plan")
        self.assertEqual(payload["pending_count"], 1)

    def test_write_outputs_sanitizes_symbol_and_keeps_paths_under_summary(self):
        from investflow_pipeline.composer import write_outputs
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        success_stage = StageResult(
            skill_name="fundamental-analysis",
            agent_name="fundamental",
            status=AnalysisStatus.SUCCESS,
            handoff=Handoff(recommendation="观望"),
        )
        result = self._pipeline_result([success_stage])
        result.ticker = "../x"
        result.target = "A/B"

        with TemporaryDirectory() as tmp:
            written = write_outputs(Path(tmp), result)
            summary_dir = (Path(tmp) / "output" / "summary").resolve()
            summary_path = Path(written.summary_report_path).resolve()
            json_path = Path(written.orchestration_json_path).resolve()

        self.assertEqual(summary_path.parent, summary_dir)
        self.assertEqual(json_path.parent, summary_dir)
        self.assertNotIn("/", summary_path.name)
        self.assertNotIn("/", json_path.name)


class RunnerTests(unittest.TestCase):
    def test_overall_status_prompt_plan_when_all_pending(self):
        from investflow_pipeline.models import AnalysisStatus, StageResult
        from investflow_pipeline.runner import _overall_status

        results = [
            StageResult("a", "a", AnalysisStatus.PENDING),
            StageResult("b", "b", AnalysisStatus.PENDING),
        ]

        self.assertEqual(_overall_status(results), "prompt_plan")

    def test_overall_status_success_partial_and_failed(self):
        from investflow_pipeline.models import AnalysisStatus, StageResult
        from investflow_pipeline.runner import _overall_status

        self.assertEqual(
            _overall_status(
                [
                    StageResult("a", "a", AnalysisStatus.SUCCESS),
                    StageResult("b", "b", AnalysisStatus.SUCCESS),
                ]
            ),
            "success",
        )
        self.assertEqual(
            _overall_status(
                [
                    StageResult("a", "a", AnalysisStatus.SUCCESS),
                    StageResult("b", "b", AnalysisStatus.FAILED),
                ]
            ),
            "partial_success",
        )
        self.assertEqual(
            _overall_status([StageResult("a", "a", AnalysisStatus.FAILED)]),
            "failed",
        )

    def test_analyze_stock_sync_writes_prompt_plan_and_json(self):
        from investflow_pipeline.runner import analyze_stock_sync

        with TemporaryDirectory() as tmp:
            result = analyze_stock_sync(
                "MRVL",
                "Marvell Technology",
                project_root=Path(tmp),
            )
            plan_path = Path(result.prompt_plan_path)
            json_path = Path(result.orchestration_json_path)
            self.assertTrue(plan_path.exists())
            self.assertTrue(json_path.exists())

            self.assertEqual(result.status, "prompt_plan")
            self.assertEqual(len(result.stage_results), 3)
            self.assertTrue(all(stage.prompt for stage in result.stage_results))
            self.assertIsNone(result.summary_report_path)
            self.assertEqual(result.failed_required, [])

    def test_sequential_prompt_plan_includes_all_stages_even_when_failure_continue_is_false(self):
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.runner import analyze_stock_sync

        with TemporaryDirectory() as tmp:
            result = analyze_stock_sync(
                "MRVL",
                config=OrchestrationConfig(
                    parallel_execution=False,
                    continue_on_failure=False,
                ),
                project_root=Path(tmp),
            )

        self.assertEqual(result.status, "prompt_plan")
        self.assertEqual(len(result.stage_results), 3)

    def test_analyze_stock_rejects_deprecated_execution_mode(self):
        from investflow_pipeline.models import OrchestrationConfig
        from investflow_pipeline.runner import analyze_stock_sync

        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "外部执行模式已废弃"):
                analyze_stock_sync(
                    "TSLA",
                    config=OrchestrationConfig(execution_mode="legacy"),
                    project_root=Path(tmp),
                )


class OrchestratorCompatibilityTests(unittest.TestCase):
    def _load_orchestrator_module(self):
        import importlib.util

        module_path = SCRIPT_DIR / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("prompt_orchestrator", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_analyze_stock_with_retry_returns_prompt_plan_without_external_execution(self):
        orchestrator = self._load_orchestrator_module()

        with TemporaryDirectory() as tmp:
            result = orchestrator.analyze_stock_with_retry(
                ticker="MRVL",
                company="Marvell Technology",
                project_root=tmp,
            )
            self.assertTrue(Path(result["prompt_plan_path"]).exists())

        self.assertEqual(result["status"], "prompt_plan")
        self.assertEqual(result["total_count"], 3)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["pending_count"], 3)
        self.assertTrue(result["prompt_plan_path"])
        prompts = [stage["prompt"] for stage in result["stage_results"]]
        self.assertEqual(prompts[0], "使用 invest-flow:fundamental-analysis 分析 MRVL")
        self.assertEqual(
            prompts[1],
            "使用 invest-flow:institutional-accumulation-analysis 分析 MRVL",
        )
        self.assertEqual(
            prompts[2],
            "使用 invest-flow:gie-investment-framework 分析 MRVL / Marvell Technology",
        )

    def test_orchestrator_cli_prints_prompt_plan_and_returns_zero(self):
        orchestrator = self._load_orchestrator_module()

        with TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            argv = [
                "orchestrator.py",
                "MRVL",
                "--company",
                "Marvell Technology",
                "--project-root",
                tmp,
            ]
            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                exit_code = orchestrator.main()

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("状态: prompt_plan", output)
        self.assertIn("Prompt计划:", output)
        self.assertIn("使用 invest-flow:fundamental-analysis 分析 MRVL", output)

    def test_scripts_do_not_call_external_agent_runtime(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SCRIPT_DIR.rglob("*.py")
            if "__pycache__" not in path.parts
        )

        self.assertNotIn("sub" + "process" + ".run", combined)
        self.assertNotIn("open" + "code", combined)
        self.assertNotIn("com" + "mand" + "_template", combined)


if __name__ == "__main__":
    unittest.main()
