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

    def test_company_profile_to_dict_serializes_all_fields(self):
        from investflow_pipeline.models import CompanyProfile

        profile = CompanyProfile(
            one_liner="Tesla 是一家垂直整合的电动车和能源技术公司。",
            business_summary="核心业务包括电动车、储能、能源服务和软件能力。",
            core_products=["Model 3", "Model Y", "Megapack"],
            revenue_model="主要通过车辆销售、租赁、能源产品和服务收费。",
            customers_and_end_markets=["消费者", "车队客户", "电力公用事业"],
            technical_advantages=["电池系统集成", "软件 OTA", "制造自动化"],
            moat_assessment="规模、品牌、软件和制造学习曲线构成复合壁垒。",
            industry_chain_position="新能源车整车、储能系统和能源基础设施。",
            ai_relevance="间接受益",
            ai_value_chain_position=["终端应用", "数据", "自动驾驶软件"],
            competitors=["BYD", "Rivian", "Lucid"],
            industry_position="全球电动车领先厂商之一。",
            key_uncertainties=["价格战是否压缩利润率"],
            pre_analysis_questions=["软件和储能能否抵消汽车毛利压力"],
            data_sources=["公司 10-K", "投资者关系材料"],
        )

        data = profile.to_dict()

        self.assertEqual(data["one_liner"], "Tesla 是一家垂直整合的电动车和能源技术公司。")
        self.assertEqual(data["core_products"], ["Model 3", "Model Y", "Megapack"])
        self.assertEqual(data["ai_relevance"], "间接受益")
        self.assertEqual(data["competitors"], ["BYD", "Rivian", "Lucid"])
        self.assertEqual(data["data_sources"], ["公司 10-K", "投资者关系材料"])

    def test_handoff_serializes_nested_company_profile(self):
        from investflow_pipeline.models import CompanyProfile, Handoff

        handoff = Handoff(
            conclusion="公司画像已完成。",
            company_profile=CompanyProfile(
                one_liner="Marvell 是数据基础设施半导体公司。",
                business_summary="面向数据中心、运营商和企业网络销售芯片。",
                ai_relevance="直接受益",
                competitors=["Broadcom", "NVIDIA"],
            ),
        )

        data = handoff.to_dict()

        self.assertEqual(data["company_profile"]["one_liner"], "Marvell 是数据基础设施半导体公司。")
        self.assertEqual(data["company_profile"]["ai_relevance"], "直接受益")
        self.assertEqual(data["company_profile"]["competitors"], ["Broadcom", "NVIDIA"])

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
                "company-profile",
                "fundamental-analysis",
                "institutional-accumulation-analysis",
                "gie-investment-framework",
                "reflexivity-deep-analysis",
                "reportify-stock-analysis",
                "non-consensus-company-discovery",
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
            [
                "company_profile",
                "fundamental",
                "institutional",
                "gie",
                "reflexivity_deep",
                "reportify",
                "non_consensus",
            ],
        )
        self.assertTrue(specs[0].required)
        self.assertTrue(specs[1].required)
        self.assertFalse(specs[2].required)
        self.assertTrue(specs[3].required)
        self.assertFalse(specs[4].required)
        self.assertFalse(specs[5].required)
        self.assertFalse(specs[6].required)

    def test_company_profile_prompt_captures_business_context(self):
        from investflow_pipeline.registry import build_registry

        spec = build_registry().get("company-profile")

        self.assertEqual(spec.agent_name, "company_profile")
        self.assertEqual(spec.stage, "single_asset_context")
        self.assertTrue(spec.required)
        self.assertEqual(spec.output_dir, "output/company-profile")
        self.assertEqual(
            spec.prompt_template,
            "使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位",
        )

    def test_gie_prompt_includes_company_fallback_slot(self):
        from investflow_pipeline.registry import build_registry

        spec = build_registry().get("gie-investment-framework")

        self.assertEqual(
            spec.prompt_template,
            "使用 invest-flow:gie-investment-framework 分析 {ticker} / {company}",
        )

    def test_non_consensus_prompt_evaluates_single_stock_revaluation_thesis(self):
        from investflow_pipeline.registry import build_registry

        spec = build_registry().get("non-consensus-company-discovery")

        self.assertEqual(spec.agent_name, "non_consensus")
        self.assertEqual(spec.stage, "thesis_challenge")
        self.assertEqual(
            spec.prompt_template,
            "使用 invest-flow:non-consensus-company-discovery 评估 {ticker} / {company} 的非共识重估机会",
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

    def test_basic_plan_uses_seven_prompt_specs_with_company_profile_first(self):
        from investflow_pipeline.planner import create_stock_request, plan_basic_stock_analysis
        from investflow_pipeline.registry import build_registry

        request = create_stock_request("TSLA", "Tesla")
        specs = plan_basic_stock_analysis(request, build_registry())

        self.assertEqual(
            [spec.agent_name for spec in specs],
            [
                "company_profile",
                "fundamental",
                "institutional",
                "gie",
                "reflexivity_deep",
                "reportify",
                "non_consensus",
            ],
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

    def test_extract_handoff_reads_company_profile_fields(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# Marvell Technology（MRVL）公司画像报告

## 一页式公司画像
- 公司一句话定义：Marvell 是面向数据基础设施的半导体公司。
- 核心业务：数据中心、运营商网络、企业网络和存储相关芯片。
- 收入来源：芯片销售、定制 ASIC 和连接解决方案。
- 主要客户 / 下游需求：云厂商，AI 数据中心；运营商网络, 企业网络
- AI 相关性结论：直接受益；网络互连、定制 ASIC、数据中心基础设施。
- 最重要的不确定性：AI 定制芯片放量节奏和传统业务复苏速度。

## 2. 核心业务与收入结构
- 数据中心互连芯片
- 定制 ASIC
- 存储控制器

## 3. 核心技术优势与技术壁垒
- 高速 SerDes
- 网络互连 IP
- 与云客户协同设计能力

护城河判断：高速互连 IP、客户协同设计和产品组合构成壁垒。

## 4. 产业链位置
AI 数据中心芯片和互连基础设施上游供应商。

## 5. AI 产业链相关性
- 相关性：直接受益
- 位置：网络互连
- 位置：定制 ASIC

## 6. 竞争对手与行业地位
- Broadcom
- NVIDIA
- Astera Labs

行业地位：数据基础设施芯片的重要供应商。

## 8. 投资分析前置问题
- AI 收入增长是否能覆盖传统存储周期波动？
- 定制 ASIC 毛利率是否低于标准产品？

## 9. 数据来源与不确定性
- 公司年报
- 投资者日材料
主要不确定性：
- 传统存储业务复苏慢于预期
- 定制 ASIC 价格压力高于预期
"""
        handoff = extract_handoff(markdown)
        profile = handoff.company_profile

        self.assertIsNotNone(profile)
        self.assertEqual(profile.one_liner, "Marvell 是面向数据基础设施的半导体公司。")
        self.assertEqual(profile.business_summary, "数据中心、运营商网络、企业网络和存储相关芯片。")
        self.assertEqual(profile.revenue_model, "芯片销售、定制 ASIC 和连接解决方案。")
        self.assertIn("AI 数据中心", profile.customers_and_end_markets)
        self.assertIn("数据中心互连芯片", profile.core_products)
        self.assertIn("高速 SerDes", profile.technical_advantages)
        self.assertEqual(profile.moat_assessment, "高速互连 IP、客户协同设计和产品组合构成壁垒。")
        self.assertEqual(profile.industry_chain_position, "AI 数据中心芯片和互连基础设施上游供应商。")
        self.assertEqual(profile.ai_relevance, "直接受益")
        self.assertIn("网络互连", profile.ai_value_chain_position)
        self.assertIn("Broadcom", profile.competitors)
        self.assertEqual(profile.industry_position, "数据基础设施芯片的重要供应商。")
        self.assertIn("AI 定制芯片放量节奏和传统业务复苏速度。", profile.key_uncertainties)
        self.assertIn("传统存储业务复苏慢于预期", profile.key_uncertainties)
        self.assertIn("AI 收入增长是否能覆盖传统存储周期波动？", profile.pre_analysis_questions)
        self.assertIn("公司年报", profile.data_sources)
        self.assertNotIn("传统存储业务复苏慢于预期", profile.data_sources)

    def test_extract_handoff_marks_missing_company_profile_fields_as_data_gaps(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# Unknown（UNKN）公司画像报告

## 一页式公司画像
- 公司一句话定义：信息很少的公司。
"""
        handoff = extract_handoff(markdown)

        self.assertIsNotNone(handoff.company_profile)
        self.assertIn("company_profile.business_summary missing", handoff.data_gaps)
        self.assertIn("company_profile.moat_assessment missing", handoff.data_gaps)
        self.assertIn("company_profile.ai_relevance missing", handoff.data_gaps)
        self.assertIn("company_profile.customers_and_end_markets missing", handoff.data_gaps)
        self.assertIn("company_profile.ai_value_chain_position missing", handoff.data_gaps)
        self.assertIn("company_profile.key_uncertainties missing", handoff.data_gaps)


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

    def test_compose_summary_includes_monitoring_signals(self):
        from investflow_pipeline.composer import compose_summary
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = self._pipeline_result(
            [
                StageResult(
                    skill_name="fundamental-analysis",
                    agent_name="fundamental",
                    status=AnalysisStatus.SUCCESS,
                    handoff=Handoff(
                        monitoring_signals=[
                            "毛利率连续两个季度改善",
                            "订单增速跌破收入增速",
                        ],
                    ),
                )
            ],
            status="success",
        )

        summary = compose_summary(result)

        self.assertIn("## 后续跟踪信号", summary)
        self.assertIn("毛利率连续两个季度改善", summary)
        self.assertIn("订单增速跌破收入增速", summary)


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
            self.assertEqual(len(result.stage_results), 6)
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
        self.assertEqual(len(result.stage_results), 6)

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
        self.assertEqual(result["total_count"], 6)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["pending_count"], 6)
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
        self.assertEqual(prompts[3], "使用 invest-flow:reflexivity-deep-analysis 分析 MRVL")
        self.assertEqual(prompts[4], "使用 invest-flow:reportify-stock-analysis 分析 MRVL")
        self.assertEqual(
            prompts[5],
            "使用 invest-flow:non-consensus-company-discovery 评估 MRVL / Marvell Technology 的非共识重估机会",
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
