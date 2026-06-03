# Company Profile Multi-Agent Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a default `company-profile` stage to InvestFlow multi-agent stock analysis so every single-stock run starts with a reusable company primer and the final summary begins with a company profile table.

**Architecture:** Create a focused `company-profile` skill for company understanding, then wire it into the existing prompt-native multi-agent pipeline as the first required stage. Extend the existing handoff model with a nested `CompanyProfile`, use deterministic Markdown extraction for the new skill template, and make the composer render `公司画像摘要` before the investment execution summary.

**Tech Stack:** Python 3.12, standard-library `dataclasses`, `unittest`, Markdown skill documentation, existing InvestFlow prompt-native pipeline under `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/`.

---

## Scope Check

This plan covers one coherent subsystem: adding company context to the existing single-stock multi-agent workflow. It does not split into separate project plans because the skill, model, extractor, registry, composer, tests, and docs all change together and produce one testable behavior: a seven-stage prompt plan with company profile first.

## File Structure

- Create `plugins/invest-flow/skills/company-profile/SKILL.md`
  - Defines the new skill behavior, workflow, output directory, and report persistence rules.
- Create `plugins/invest-flow/skills/company-profile/references/report-template.md`
  - Defines the fixed Markdown template used by the extractor and by users writing reports.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py`
  - Adds `CompanyProfile` and nests it in `Handoff`.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py`
  - Registers `company-profile` and puts it first in `basic_stock_specs()`.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py`
  - Adds deterministic company-profile Markdown extraction and attaches it to `Handoff`.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py`
  - Renders `## 公司画像摘要` before `## 执行摘要`, with fallback behavior if the stage failed.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
  - Adds TDD coverage for models, registry, planner, extractor, composer, runner, and orchestrator compatibility.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`
  - Updates the default flow from six to seven dimensions.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md`
  - Updates workflow and handoff semantics.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md`
  - Documents `CompanyProfile` and the seven-stage default.
- Modify `plugins/invest-flow/skills/multi-agent-stock-analysis/assets/summary-report-template.md`
  - Adds the company profile summary section and seven-item report index.
- Modify `README.md`, `README.zh-CN.md`, and `AGENTS.md`
  - Adds the new skill to user-facing and repo-facing docs.

## Task 1: Add Model Tests For CompanyProfile

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py`

- [ ] **Step 1: Write the failing serialization tests**

Insert these tests in `ModelTests` after `test_stage_result_to_dict_contains_prompt_and_handoff`:

```python
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
```

- [ ] **Step 2: Run the model tests and verify they fail**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k company_profile
```

Expected result: failure with an import error or attribute error because `CompanyProfile` and `Handoff.company_profile` do not exist.

- [ ] **Step 3: Add `CompanyProfile` and extend `Handoff`**

In `models.py`, add this dataclass before `Handoff`:

```python
@dataclass
class CompanyProfile:
    one_liner: str = ""
    business_summary: str = ""
    core_products: List[str] = field(default_factory=list)
    revenue_model: str = ""
    customers_and_end_markets: List[str] = field(default_factory=list)
    technical_advantages: List[str] = field(default_factory=list)
    moat_assessment: str = ""
    industry_chain_position: str = ""
    ai_relevance: str = ""
    ai_value_chain_position: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    industry_position: str = ""
    key_uncertainties: List[str] = field(default_factory=list)
    pre_analysis_questions: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "one_liner": self.one_liner,
            "business_summary": self.business_summary,
            "core_products": list(self.core_products),
            "revenue_model": self.revenue_model,
            "customers_and_end_markets": list(self.customers_and_end_markets),
            "technical_advantages": list(self.technical_advantages),
            "moat_assessment": self.moat_assessment,
            "industry_chain_position": self.industry_chain_position,
            "ai_relevance": self.ai_relevance,
            "ai_value_chain_position": list(self.ai_value_chain_position),
            "competitors": list(self.competitors),
            "industry_position": self.industry_position,
            "key_uncertainties": list(self.key_uncertainties),
            "pre_analysis_questions": list(self.pre_analysis_questions),
            "data_sources": list(self.data_sources),
        }
```

Update `Handoff`:

```python
@dataclass
class Handoff:
    conclusion: str = ""
    recommendation: str = ""
    confidence: Optional[int] = None
    key_evidence: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    contradiction_points: List[str] = field(default_factory=list)
    monitoring_signals: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)
    company_profile: Optional[CompanyProfile] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "key_evidence": list(self.key_evidence),
            "risk_flags": list(self.risk_flags),
            "contradiction_points": list(self.contradiction_points),
            "monitoring_signals": list(self.monitoring_signals),
            "data_gaps": list(self.data_gaps),
            "company_profile": (
                self.company_profile.to_dict() if self.company_profile else None
            ),
        }
```

- [ ] **Step 4: Run model tests and verify they pass**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k company_profile
```

Expected result: `OK`.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/models.py
git commit -m "Add company profile handoff model"
```

## Task 2: Register Company Profile As The First Required Stage

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py`

- [ ] **Step 1: Update registry and planner tests first**

Replace `RegistryTests.test_basic_specs_are_codex_prompt_templates` with:

```python
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
```

Replace `RegistryTests.test_basic_specs_include_expected_agents_and_required_flags` with:

```python
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
```

Add this registry test:

```python
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
```

Replace `PlannerTests.test_basic_plan_uses_six_prompt_specs` with:

```python
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
```

- [ ] **Step 2: Run the changed tests and verify they fail**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "basic_specs or company_profile_prompt or basic_plan"
```

Expected result: failures because `company-profile` is not registered.

- [ ] **Step 3: Add the registry spec**

In `registry.py`, update `basic_stock_specs()`:

```python
    def basic_stock_specs(self) -> List[SkillSpec]:
        return [
            self.get("company-profile"),
            self.get("fundamental-analysis"),
            self.get("institutional-accumulation-analysis"),
            self.get("gie-investment-framework"),
            self.get("reflexivity-deep-analysis"),
            self.get("reportify-stock-analysis"),
            self.get("non-consensus-company-discovery"),
        ]
```

In `build_registry()`, add this spec before `fundamental-analysis`:

```python
        _spec(
            skill_name="company-profile",
            agent_name="company_profile",
            stage="single_asset_context",
            prompt_template="使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位",
            output_dir="output/company-profile",
            required=True,
        ),
```

- [ ] **Step 4: Run registry and planner tests**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "basic_specs or company_profile_prompt or basic_plan"
```

Expected result: `OK`.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/registry.py
git commit -m "Add company profile stage to multi-agent registry"
```

## Task 3: Extract Structured Company Profiles From Markdown

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py`

- [ ] **Step 1: Add failing extractor tests**

Insert these tests in `ExtractorTests` after `test_extract_handoff_keeps_child_heading_content_in_parent_section`:

```python
    def test_extract_handoff_reads_company_profile_fields(self):
        from investflow_pipeline.extractors import extract_handoff

        markdown = """
# Marvell Technology（MRVL）公司画像报告

## 一页式公司画像
- 公司一句话定义：Marvell 是面向数据基础设施的半导体公司。
- 核心业务：数据中心、运营商网络、企业网络和存储相关芯片。
- 收入来源：芯片销售、定制 ASIC 和连接解决方案。
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
"""
        handoff = extract_handoff(markdown)
        profile = handoff.company_profile

        self.assertIsNotNone(profile)
        self.assertEqual(profile.one_liner, "Marvell 是面向数据基础设施的半导体公司。")
        self.assertEqual(profile.business_summary, "数据中心、运营商网络、企业网络和存储相关芯片。")
        self.assertEqual(profile.revenue_model, "芯片销售、定制 ASIC 和连接解决方案。")
        self.assertIn("高速 SerDes", profile.technical_advantages)
        self.assertEqual(profile.industry_chain_position, "AI 数据中心芯片和互连基础设施上游供应商。")
        self.assertEqual(profile.ai_relevance, "直接受益")
        self.assertIn("网络互连", profile.ai_value_chain_position)
        self.assertIn("Broadcom", profile.competitors)
        self.assertEqual(profile.industry_position, "数据基础设施芯片的重要供应商。")
        self.assertIn("AI 收入增长是否能覆盖传统存储周期波动？", profile.pre_analysis_questions)
        self.assertIn("公司年报", profile.data_sources)

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
        self.assertIn("company_profile.ai_relevance missing", handoff.data_gaps)
```

- [ ] **Step 2: Run extractor tests and verify they fail**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "company_profile_fields or missing_company_profile"
```

Expected result: failures because `extract_handoff()` does not attach `company_profile`.

- [ ] **Step 3: Add deterministic extraction helpers**

In `extractors.py`, update the imports:

```python
from .models import CompanyProfile, Handoff
```

Add these helpers after `_first_nonempty_line`:

```python
def _label_value(markdown: str, label: str) -> str:
    pattern = re.compile(rf"^[\-*]\s*{re.escape(label)}[:：]\s*(.*?)\s*$")
    for line in markdown.splitlines():
        match = pattern.match(line.strip())
        if match:
            return _strip_markdown_emphasis(match.group(1))
    return ""


def _section_bullets(markdown: str, names: List[str]) -> List[str]:
    return [_strip_markdown_emphasis(value) for value in _bullets(_section(markdown, names))]


def _first_section_line(markdown: str, names: List[str]) -> str:
    return _first_nonempty_line(_section(markdown, names))


def _extract_ai_relevance(markdown: str) -> str:
    labeled = _label_value(markdown, "相关性")
    if labeled:
        return labeled.split("；", 1)[0].split(";", 1)[0].strip()
    summary = _label_value(markdown, "AI 相关性结论")
    if "；" in summary:
        return summary.split("；", 1)[0].strip()
    if ";" in summary:
        return summary.split(";", 1)[0].strip()
    return summary
```

Add this extraction function before `extract_handoff`:

```python
def _extract_company_profile(markdown: str) -> CompanyProfile | None:
    if "公司画像" not in markdown:
        return None

    core_products = _section_bullets(markdown, ["核心业务与收入结构"])
    technical_advantages = _section_bullets(markdown, ["核心技术优势", "技术壁垒"])
    ai_positions = []
    for bullet in _section_bullets(markdown, ["AI 产业链相关性"]):
        if bullet.startswith("位置："):
            ai_positions.append(_strip_markdown_emphasis(bullet.split("：", 1)[1]))
    competitors = _section_bullets(markdown, ["竞争对手与行业地位"])
    pre_questions = _section_bullets(markdown, ["投资分析前置问题"])
    data_sources = _section_bullets(markdown, ["数据来源与不确定性"])

    profile = CompanyProfile(
        one_liner=_label_value(markdown, "公司一句话定义"),
        business_summary=_label_value(markdown, "核心业务"),
        core_products=core_products,
        revenue_model=_label_value(markdown, "收入来源"),
        customers_and_end_markets=[],
        technical_advantages=technical_advantages,
        moat_assessment="",
        industry_chain_position=_first_section_line(markdown, ["产业链位置"]),
        ai_relevance=_extract_ai_relevance(markdown),
        ai_value_chain_position=ai_positions,
        competitors=competitors,
        industry_position=_extract_recommendation_like_line(
            _section(markdown, ["竞争对手与行业地位"]),
            "行业地位",
        ),
        key_uncertainties=[
            value
            for value in [_label_value(markdown, "最重要的不确定性")]
            if value
        ],
        pre_analysis_questions=pre_questions,
        data_sources=data_sources,
    )
    return profile
```

Add this helper before `_extract_company_profile`:

```python
def _extract_recommendation_like_line(text: str, label: str) -> str:
    for line in text.splitlines():
        plain_line = _remove_markdown_markers(line)
        match = re.search(rf"{re.escape(label)}[:：]\s*([^\n\r]+)", plain_line)
        if match:
            return _strip_markdown_emphasis(match.group(1))
    return ""
```

Add this missing-field helper:

```python
def _company_profile_data_gaps(profile: CompanyProfile | None) -> List[str]:
    if profile is None:
        return []
    required_strings = {
        "one_liner": profile.one_liner,
        "business_summary": profile.business_summary,
        "revenue_model": profile.revenue_model,
        "industry_chain_position": profile.industry_chain_position,
        "ai_relevance": profile.ai_relevance,
        "industry_position": profile.industry_position,
    }
    required_lists = {
        "core_products": profile.core_products,
        "technical_advantages": profile.technical_advantages,
        "competitors": profile.competitors,
        "pre_analysis_questions": profile.pre_analysis_questions,
        "data_sources": profile.data_sources,
    }
    gaps = [
        f"company_profile.{name} missing"
        for name, value in required_strings.items()
        if not value
    ]
    gaps.extend(
        f"company_profile.{name} missing"
        for name, values in required_lists.items()
        if not values
    )
    return gaps
```

In `extract_handoff()`, assign and serialize the profile:

```python
    company_profile = _extract_company_profile(markdown)
    data_gaps = _bullets(gaps_section)
    data_gaps.extend(_company_profile_data_gaps(company_profile))

    return Handoff(
        conclusion=conclusion,
        recommendation=_extract_recommendation(markdown),
        confidence=_extract_confidence(markdown),
        key_evidence=_bullets(evidence_section),
        risk_flags=_bullets(risk_section),
        contradiction_points=_bullets(_section(markdown, ["冲突", "分歧"])),
        monitoring_signals=_bullets(monitoring_section),
        data_gaps=data_gaps,
        company_profile=company_profile,
    )
```

- [ ] **Step 4: Run extractor tests**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "ExtractorTests"
```

Expected result: `OK`.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/extractors.py
git commit -m "Extract company profile handoff fields"
```

## Task 4: Render Company Profile Summary In Composer

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py`

- [ ] **Step 1: Add failing composer tests**

Insert these tests in `ComposerTests` before `test_write_outputs_success_creates_json_and_markdown`:

```python
    def test_compose_summary_places_company_profile_before_execution_summary(self):
        from investflow_pipeline.composer import compose_summary
        from investflow_pipeline.models import AnalysisStatus, CompanyProfile, Handoff, StageResult

        result = self._pipeline_result(
            [
                StageResult(
                    skill_name="company-profile",
                    agent_name="company_profile",
                    status=AnalysisStatus.SUCCESS,
                    report_path="output/company-profile/company-profile-TSLA-2026-06-02.md",
                    handoff=Handoff(
                        company_profile=CompanyProfile(
                            one_liner="Tesla 是电动车、储能和软件能力结合的能源技术公司。",
                            business_summary="电动车、储能系统、能源服务和自动驾驶软件。",
                            revenue_model="车辆销售、租赁、能源产品和服务。",
                            technical_advantages=["电池系统集成", "软件 OTA"],
                            industry_chain_position="新能源车整车与储能系统。",
                            ai_relevance="间接受益",
                            ai_value_chain_position=["终端应用", "自动驾驶软件"],
                            competitors=["BYD", "Rivian"],
                            industry_position="全球电动车领先厂商之一。",
                            key_uncertainties=["汽车毛利率压力"],
                        )
                    ),
                )
            ],
            status="success",
        )

        summary = compose_summary(result)

        self.assertLess(summary.index("## 公司画像摘要"), summary.index("## 执行摘要"))
        self.assertIn("| 公司一句话定义 | Tesla 是电动车、储能和软件能力结合的能源技术公司。 |", summary)
        self.assertIn("| AI 相关性 | 间接受益 / 终端应用、自动驾驶软件 |", summary)
        self.assertIn("| 主要竞争对手 | BYD、Rivian |", summary)

    def test_compose_summary_reports_failed_company_profile_as_data_gap(self):
        from investflow_pipeline.composer import compose_summary
        from investflow_pipeline.models import AnalysisStatus, Handoff, StageResult

        result = self._pipeline_result(
            [
                StageResult(
                    skill_name="company-profile",
                    agent_name="company_profile",
                    status=AnalysisStatus.FAILED,
                    errors=["profile report missing"],
                ),
                StageResult(
                    skill_name="fundamental-analysis",
                    agent_name="fundamental",
                    status=AnalysisStatus.SUCCESS,
                    handoff=Handoff(recommendation="观望"),
                ),
            ],
            status="partial_success",
        )

        summary = compose_summary(result)

        self.assertIn("## 公司画像摘要", summary)
        self.assertIn("缺少公司画像会降低整体判断可信度", summary)
        self.assertIn("company-profile(company_profile) 失败: profile report missing", summary)
```

- [ ] **Step 2: Run composer tests and verify they fail**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "company_profile_before_execution or failed_company_profile"
```

Expected result: failures because the summary has no company profile section.

- [ ] **Step 3: Add composer helpers**

In `composer.py`, add this import:

```python
from .models import AnalysisStatus, CompanyProfile, PipelineResult, StageResult
```

Replace the existing import line that imports `AnalysisStatus, PipelineResult, StageResult`.

Add these helpers before `compose_summary()`:

```python
def _join_values(values: List[str], fallback: str = "不确定") -> str:
    cleaned = [_normalize_text(value) for value in values if _normalize_text(value)]
    return "、".join(cleaned) if cleaned else fallback


def _find_company_profile_stage(results: List[StageResult]) -> StageResult | None:
    for stage in results:
        if stage.skill_name == "company-profile":
            return stage
    return None


def _profile_from_stage(stage: StageResult | None) -> CompanyProfile | None:
    if stage is None:
        return None
    return stage.handoff.company_profile


def _company_profile_summary(results: List[StageResult]) -> str:
    stage = _find_company_profile_stage(results)
    profile = _profile_from_stage(stage)
    if profile is None:
        if stage is not None and stage.status == AnalysisStatus.FAILED:
            note = "缺少公司画像会降低整体判断可信度。"
        else:
            note = "公司画像未生成，后续结论只能依赖投资维度报告。"
        return (
            "| 项目 | 内容 |\n"
            "| --- | --- |\n"
            f"| 公司画像状态 | {_table_cell(note, '不确定')} |"
        )

    ai_context = profile.ai_relevance or "不确定"
    ai_positions = _join_values(profile.ai_value_chain_position, "")
    if ai_positions:
        ai_context = f"{ai_context} / {ai_positions}"

    rows = [
        ("公司一句话定义", profile.one_liner),
        ("核心业务", profile.business_summary),
        ("收入来源", profile.revenue_model),
        ("核心技术 / 壁垒", _join_values(profile.technical_advantages)),
        ("产业链位置", profile.industry_chain_position),
        ("AI 相关性", ai_context),
        ("主要竞争对手", _join_values(profile.competitors)),
        ("行业地位", profile.industry_position),
        ("关键不确定性", _join_values(profile.key_uncertainties)),
    ]
    lines = ["| 项目 | 内容 |", "| --- | --- |"]
    lines.extend(
        f"| {_table_cell(label, '-')} | {_table_cell(value, '不确定')} |"
        for label, value in rows
    )
    return "\n".join(lines)
```

In `compose_summary()`, insert the company profile section before `## 执行摘要`:

```python
        f"# 综合分析报告 - {result.ticker}\n\n"
        f"作者：InvestmentFlow\n\n"
        f"## 公司画像摘要\n{_company_profile_summary(result.stage_results)}\n\n"
        f"## 执行摘要\n{execution_summary}\n\n"
```

Keep the rest of the return string unchanged.

- [ ] **Step 4: Run composer tests**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "ComposerTests"
```

Expected result: `OK`.

- [ ] **Step 5: Commit Task 4**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/investflow_pipeline/composer.py
git commit -m "Render company profile in summary reports"
```

## Task 5: Update Runner And Orchestrator Expectations To Seven Stages

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py`

- [ ] **Step 1: Update runner assertions**

In `RunnerTests.test_analyze_stock_sync_writes_prompt_plan_and_json`, change:

```python
            self.assertEqual(len(result.stage_results), 6)
```

to:

```python
            self.assertEqual(len(result.stage_results), 7)
            self.assertEqual(result.stage_results[0].skill_name, "company-profile")
```

In `RunnerTests.test_sequential_prompt_plan_includes_all_stages_even_when_failure_continue_is_false`, change:

```python
        self.assertEqual(len(result.stage_results), 6)
```

to:

```python
        self.assertEqual(len(result.stage_results), 7)
        self.assertEqual(result.stage_results[0].agent_name, "company_profile")
```

- [ ] **Step 2: Update orchestrator compatibility assertions**

In `OrchestratorCompatibilityTests.test_analyze_stock_with_retry_returns_prompt_plan_without_external_execution`, replace the count and prompt assertions with:

```python
        self.assertEqual(result["total_count"], 7)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["pending_count"], 7)
        self.assertTrue(result["prompt_plan_path"])
        prompts = [stage["prompt"] for stage in result["stage_results"]]
        self.assertEqual(
            prompts[0],
            "使用 invest-flow:company-profile 分析 MRVL / Marvell Technology，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位",
        )
        self.assertEqual(prompts[1], "使用 invest-flow:fundamental-analysis 分析 MRVL")
        self.assertEqual(
            prompts[2],
            "使用 invest-flow:institutional-accumulation-analysis 分析 MRVL",
        )
        self.assertEqual(
            prompts[3],
            "使用 invest-flow:gie-investment-framework 分析 MRVL / Marvell Technology",
        )
        self.assertEqual(prompts[4], "使用 invest-flow:reflexivity-deep-analysis 分析 MRVL")
        self.assertEqual(prompts[5], "使用 invest-flow:reportify-stock-analysis 分析 MRVL")
        self.assertEqual(
            prompts[6],
            "使用 invest-flow:non-consensus-company-discovery 评估 MRVL / Marvell Technology 的非共识重估机会",
        )
```

In `OrchestratorCompatibilityTests.test_orchestrator_cli_prints_prompt_plan_and_returns_zero`, add:

```python
        self.assertIn("使用 invest-flow:company-profile 分析 MRVL / Marvell Technology", output)
```

- [ ] **Step 3: Run runner and orchestrator tests**

Run:

```bash
python -m unittest plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py -k "RunnerTests or OrchestratorCompatibilityTests"
```

Expected result: `OK`.

- [ ] **Step 4: Commit Task 5**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py
git commit -m "Update prompt plan expectations for company profile"
```

## Task 6: Create The Company Profile Skill

**Files:**
- Create: `plugins/invest-flow/skills/company-profile/SKILL.md`
- Create: `plugins/invest-flow/skills/company-profile/references/report-template.md`

- [ ] **Step 1: Create the skill directory**

Run:

```bash
mkdir -p plugins/invest-flow/skills/company-profile/references
```

Expected result: directory exists under `plugins/invest-flow/skills/company-profile/`.

- [ ] **Step 2: Add `SKILL.md`**

Create `plugins/invest-flow/skills/company-profile/SKILL.md` with:

```markdown
---
name: company-profile
description: "公司画像 (Company Profile) - 为单个公司生成投资分析前置画像，覆盖公司简介、核心业务、收入来源、核心技术优势、产业链位置、AI 相关性、竞争格局和行业地位。适用于：(1) 用户第一次了解某家公司, (2) multi-agent-stock-analysis 的默认前置公司认知, (3) 投资判断前的业务与行业定位梳理。生成报告并保存至 ./output/company-profile/ 目录。"
---

# Company Profile (公司画像)

## Overview

This skill builds a company primer before investment analysis. It explains what the company does, how it makes money, where it sits in the industry chain, why it may have durable advantages, and who it competes with.

It does not issue buy, sell, or hold recommendations. Downstream skills handle valuation, trading, reflexivity, capital flow, and final decision synthesis.

**Output**: Markdown reports saved to `./output/company-profile/`

## Workflow

### 1. Identify The Target

- Determine the ticker symbol.
- Determine the company name.
- Identify the main exchange, reporting currency, and primary sector when available.

### 2. Gather Current Company Context

Use current reliable sources where available:

- company investor relations pages
- latest annual report or 10-K
- latest quarterly report or 10-Q
- earnings presentation
- official product pages
- credible industry sources
- competitor investor materials

Separate facts, reasoned inference, and uncertainty. Do not treat market narrative as proven business exposure.

### 3. Build The Company Profile

Use `references/report-template.md` and cover:

- company overview
- core business and revenue structure
- customers and downstream demand
- core technology advantages and barriers
- industry-chain position
- AI value-chain relevance when evidence supports it
- competitors and industry position
- business model quality
- pre-analysis questions for downstream investment work
- data sources and uncertainty

### 4. AI Relevance Rules

Classify AI relevance as one of:

- `直接受益`
- `间接受益`
- `弱相关`
- `无明显相关`
- `不确定`

Only call a company AI-relevant when there is evidence from revenue exposure, customers, products, capex linkage, or disclosed strategy. If AI relevance is mainly market narrative, say so explicitly.

### 5. Save Report

- **Output Directory**: `./output/company-profile/`
- **Filename Format**: `company-profile-{TICKER}-{YYYY-MM-DD}.md`
- **Conflict Handling**: If a file with the same name exists, append a numbered suffix: `company-profile-{TICKER}-{YYYY-MM-DD}(1).md`
- Ensure the output directory exists before saving.
- Every generated report must include `作者：InvestmentFlow`.
- Confirm to the user with the actual saved path.

## Handoff Fields

When this skill is used inside `multi-agent-stock-analysis`, preserve these fields for summary composition:

- `one_liner`
- `business_summary`
- `core_products`
- `revenue_model`
- `customers_and_end_markets`
- `technical_advantages`
- `moat_assessment`
- `industry_chain_position`
- `ai_relevance`
- `ai_value_chain_position`
- `competitors`
- `industry_position`
- `key_uncertainties`
- `pre_analysis_questions`
- `data_sources`

## Resources

### references/

- `report-template.md` - Company profile report template.
```

- [ ] **Step 3: Add `report-template.md`**

Create `plugins/invest-flow/skills/company-profile/references/report-template.md` with:

```markdown
# {{company}}（{{ticker}}）公司画像报告

作者：InvestmentFlow  
分析日期：{{YYYY-MM-DD}}  
研究对象：{{company}} / {{ticker}}  
交易所：{{exchange}}  
币种：{{currency}}

---

## 一页式公司画像

- 公司一句话定义：{{one_liner}}
- 核心业务：{{business_summary}}
- 主要客户 / 下游需求：{{customers_and_end_markets}}
- 收入来源：{{revenue_model}}
- 核心竞争力：{{core_competitiveness}}
- 行业地位：{{industry_position}}
- AI 相关性结论：{{ai_relevance}}；{{ai_value_chain_position}}
- 最重要的不确定性：{{key_uncertainty}}

## 1. 公司简介

| 问题 | 回答 | 依据 | 类型 |
|---|---|---|---|
| 公司是谁 | {{company_identity}} | {{source}} | 事实 |
| 为谁服务 | {{served_customers}} | {{source}} | 事实 |
| 解决什么问题 | {{problem_solved}} | {{source}} | 推断 |
| 如何收费 | {{pricing_or_revenue_model}} | {{source}} | 事实 |
| 公司一句话定义 | {{one_liner}} | {{source}} | 推断 |

## 2. 核心业务与收入结构

- {{core_product_or_segment_1}}
- {{core_product_or_segment_2}}
- {{core_product_or_segment_3}}

业务结构判断：{{business_structure_assessment}}

## 3. 核心技术优势与技术壁垒

- {{technical_advantage_1}}
- {{technical_advantage_2}}
- {{technical_advantage_3}}

护城河判断：{{moat_assessment}}

## 4. 产业链位置

{{industry_chain_position}}

上游：{{upstream_dependencies}}  
下游：{{downstream_customers}}  
关键瓶颈：{{value_chain_bottleneck}}

## 5. AI 产业链相关性

- 相关性：{{ai_relevance}}
- 位置：{{ai_value_chain_position_1}}
- 位置：{{ai_value_chain_position_2}}
- 收入 / 客户证据：{{ai_revenue_or_customer_evidence}}
- 叙事成分：{{ai_narrative_exposure}}
- 反证点：{{ai_counter_evidence}}

## 6. 竞争对手与行业地位

- {{competitor_1}}
- {{competitor_2}}
- {{competitor_3}}

行业地位：{{industry_position}}

竞争结论：{{competitive_assessment}}

## 7. 商业模式质量

| 维度 | 判断 | 依据 |
|---|---|---|
| 收入可见度 | {{revenue_visibility}} | {{source}} |
| 毛利率结构 | {{gross_margin_quality}} | {{source}} |
| 客户集中度 | {{customer_concentration}} | {{source}} |
| 研发效率 | {{rd_efficiency}} | {{source}} |
| 规模经济 | {{scale_economics}} | {{source}} |

## 8. 投资分析前置问题

- {{pre_analysis_question_1}}
- {{pre_analysis_question_2}}
- {{pre_analysis_question_3}}

## 9. 数据来源与不确定性

- {{data_source_1}}
- {{data_source_2}}
- {{data_source_3}}

主要不确定性：

- {{key_uncertainty_1}}
- {{key_uncertainty_2}}
- {{key_uncertainty_3}}
```

- [ ] **Step 4: Verify frontmatter and paths**

Run:

```bash
python - <<'PY'
from pathlib import Path
skill = Path("plugins/invest-flow/skills/company-profile/SKILL.md")
template = Path("plugins/invest-flow/skills/company-profile/references/report-template.md")
assert skill.exists()
assert template.exists()
text = skill.read_text(encoding="utf-8")
assert text.startswith("---\nname: company-profile")
assert "Output" in text
print("company-profile skill files OK")
PY
```

Expected result:

```text
company-profile skill files OK
```

- [ ] **Step 5: Commit Task 6**

Run:

```bash
git add plugins/invest-flow/skills/company-profile/SKILL.md plugins/invest-flow/skills/company-profile/references/report-template.md
git commit -m "Add company profile skill"
```

## Task 7: Update Multi-Agent Skill Documentation And Templates

**Files:**
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md`
- Modify: `plugins/invest-flow/skills/multi-agent-stock-analysis/assets/summary-report-template.md`

- [ ] **Step 1: Update `SKILL.md` flow and required sections**

In `plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md`, update the overview flow so it starts with:

```text
用户请求
  -> 解析 ticker/company
  -> 执行 company-profile prompt
  -> 执行 fundamental-analysis prompt
  -> 执行 institutional-accumulation-analysis prompt
  -> 执行 gie-investment-framework prompt
  -> 执行 reflexivity-deep-analysis prompt
  -> 执行 reportify-stock-analysis prompt
  -> 执行 non-consensus-company-discovery prompt
  -> 汇总七维度 handoff
  -> 输出中文综合报告
```

Add this prompt before the existing fundamental prompt:

```text
使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
```

Update the final report section list to include:

```markdown
## 公司画像摘要
## 执行摘要
## 七维度结论对照
```

Update the dimension table to include:

```markdown
| company-profile | 公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位 |
```

- [ ] **Step 2: Update `workflow-guide.md`**

In `workflow-guide.md`, change "六个分析维度" wording to "七个分析维度" and add `company-profile` as the first default dimension. Add this prompt in the prompt list:

```text
使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
```

Add this handoff note:

```markdown
`company-profile` 的 handoff 额外包含 `company_profile` 结构化字段。Composer 必须优先使用该字段生成 `## 公司画像摘要`；字段缺失时回退到 conclusion 和 key_evidence。
```

- [ ] **Step 3: Update `data-structure.md`**

Add `CompanyProfile` to the core model list:

```markdown
- `CompanyProfile`
```

Replace the default dimension table with a seven-row version:

```markdown
| agent_name | skill_name | prompt_template | required |
| --- | --- | --- | --- |
| company_profile | company-profile | 使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位 | true |
| fundamental | fundamental-analysis | 使用 invest-flow:fundamental-analysis 分析 {ticker} | true |
| institutional | institutional-accumulation-analysis | 使用 invest-flow:institutional-accumulation-analysis 分析 {ticker} | false |
| gie | gie-investment-framework | 使用 invest-flow:gie-investment-framework 分析 {ticker} / {company} | true |
| reflexivity_deep | reflexivity-deep-analysis | 使用 invest-flow:reflexivity-deep-analysis 分析 {ticker} | false |
| reportify | reportify-stock-analysis | 使用 invest-flow:reportify-stock-analysis 分析 {ticker} | false |
| non_consensus | non-consensus-company-discovery | 使用 invest-flow:non-consensus-company-discovery 评估 {ticker} / {company} 的非共识重估机会 | false |
```

Add this section after `Handoff`:

````markdown
### CompanyProfile

`company-profile` 阶段会在 `Handoff.company_profile` 中提供结构化公司画像：

```python
CompanyProfile(
    one_liner="Marvell 是面向数据基础设施的半导体公司。",
    business_summary="核心业务包括数据中心、运营商网络、企业网络和存储芯片。",
    core_products=["高速互连芯片", "定制 ASIC", "存储控制器"],
    revenue_model="通过芯片销售、定制设计和连接解决方案收费。",
    technical_advantages=["高速 SerDes", "网络互连 IP"],
    industry_chain_position="AI 数据中心芯片和互连基础设施上游供应商。",
    ai_relevance="直接受益",
    ai_value_chain_position=["网络互连", "定制 ASIC"],
    competitors=["Broadcom", "NVIDIA"],
    industry_position="数据基础设施芯片的重要供应商。",
)
```
````

- [ ] **Step 4: Update `summary-report-template.md`**

Add this section after the report header and before `## 执行摘要`:

```markdown
## 公司画像摘要

| 项目 | 内容 |
|---|---|
| 公司一句话定义 | {company_one_liner} |
| 核心业务 | {company_business_summary} |
| 收入来源 | {company_revenue_model} |
| 核心技术 / 壁垒 | {company_technical_advantages} |
| 产业链位置 | {company_industry_chain_position} |
| AI 相关性 | {company_ai_relevance} |
| 主要竞争对手 | {company_competitors} |
| 行业地位 | {company_industry_position} |
| 关键不确定性 | {company_key_uncertainties} |

---
```

Add `company-profile` to every subreport index list:

```markdown
- **company-profile：** [{company_profile_report_path}]({company_profile_report_link})
```

- [ ] **Step 5: Run a documentation consistency scan**

Run:

```bash
rg -n "六维度|六个维度|六段子|六个子|6 个|6个" plugins/invest-flow/skills/multi-agent-stock-analysis
```

Expected result: no stale default-flow wording that still describes the default multi-agent flow as six stages. If matches appear only in historical explanatory context, rewrite them to mention the new seven-stage default.

- [ ] **Step 6: Commit Task 7**

Run:

```bash
git add plugins/invest-flow/skills/multi-agent-stock-analysis/SKILL.md plugins/invest-flow/skills/multi-agent-stock-analysis/references/workflow-guide.md plugins/invest-flow/skills/multi-agent-stock-analysis/references/data-structure.md plugins/invest-flow/skills/multi-agent-stock-analysis/assets/summary-report-template.md
git commit -m "Document company profile multi-agent workflow"
```

## Task 8: Update Repository README And AGENTS Guidance

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update README skill lists and workflows**

In `README.md`, add `company-profile` to the skills table:

```markdown
| `company-profile` | Builds a company primer before investment analysis. | Use when a user is hearing about a company for the first time and needs business, technology, value-chain, AI relevance, competitors, and industry-position context. |
```

In `README.md`, update the quick single-stock workflow row to say:

```markdown
| Quick single-stock research | Use `multi-agent-stock-analysis` to start with `company-profile`, then cross-check fundamentals, capital flow, GIE, reflexivity, Reportify, and non-consensus views. |
```

In `README.md`, add the output path:

```markdown
| Company profile | `output/company-profile/` |
```

- [ ] **Step 2: Update Chinese README**

In `README.zh-CN.md`, add `company-profile` to the skills table:

```markdown
| `company-profile` | 生成投资分析前置公司画像。 | 用户第一次听说某家公司时，用于快速理解公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争对手和行业地位。 |
```

Update the fast single-stock workflow row:

```markdown
| 快速研究单只股票 | 用 `multi-agent-stock-analysis` 先生成 `company-profile` 公司画像，再交叉验证基本面、资金流、GIE、反身性、Reportify 和非共识视角。 |
```

Add the output path:

```markdown
| 公司画像 | `output/company-profile/` |
```

- [ ] **Step 3: Update AGENTS.md**

In `AGENTS.md`, add `company-profile` to active packaged skills:

```markdown
- `company-profile` - company primer covering overview, core business, technology barriers, industry-chain position, AI relevance, competitors, and industry position
```

Add the output convention:

```markdown
- Company profile: `output/company-profile/company-profile-{TICKER}-{YYYY-MM-DD}.md`
```

Update the multi-agent notes to say the orchestrator generates seven prompts:

```markdown
- generates seven Codex skill prompts for the basic stock-analysis workflow: company profile, fundamental, institutional, GIE, reflexivity deep, reportify, and non-consensus
```

- [ ] **Step 4: Run documentation scan**

Run:

```bash
rg -n "company-profile|公司画像|six|六维度|六个维度|六段子" README.md README.zh-CN.md AGENTS.md
```

Expected result: `company-profile` appears in all three files; stale six-stage wording is removed or explicitly historical.

- [ ] **Step 5: Commit Task 8**

Run:

```bash
git add README.md README.zh-CN.md AGENTS.md
git commit -m "Update docs for company profile workflow"
```

## Task 9: Run Full Verification

**Files:**
- No planned source edits unless verification finds a defect.

- [ ] **Step 1: Run the full helper test suite**

Run:

```bash
python -m unittest discover plugins/invest-flow -p 'test_*.py'
```

Expected result: all tests pass.

- [ ] **Step 2: Generate a prompt plan for MRVL**

Run:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py MRVL --company "Marvell Technology"
```

Expected output includes:

```text
状态: prompt_plan
待执行: 7/7
1. 使用 invest-flow:company-profile 分析 MRVL / Marvell Technology，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
2. 使用 invest-flow:fundamental-analysis 分析 MRVL
```

- [ ] **Step 3: Inspect generated prompt plan Markdown**

Find the printed prompt plan path, then run:

```bash
sed -n '1,120p' output/summary/prompt-plan-MRVL-*.md
```

Expected result: the first child skill section is `company-profile`, and the plan lists seven child skill prompts.

- [ ] **Step 4: Inspect orchestration JSON**

Find the printed orchestration JSON path, then run:

```bash
python - <<'PY'
import json
from pathlib import Path

paths = sorted(Path("output/summary").glob("orchestration-MRVL-*.json"))
payload = json.loads(paths[-1].read_text(encoding="utf-8"))
assert payload["total_count"] == 7
assert payload["pending_count"] == 7
assert payload["stage_results"][0]["skill_name"] == "company-profile"
assert payload["stage_results"][0]["handoff"]["company_profile"] is None
print(paths[-1])
print("orchestration JSON OK")
PY
```

Expected result:

```text
orchestration JSON OK
```

- [ ] **Step 5: Commit verification fixes if any were needed**

If verification required source changes, run:

```bash
git add plugins/invest-flow README.md README.zh-CN.md AGENTS.md
git commit -m "Fix company profile workflow verification issues"
```

If no fixes were needed, do not create an empty commit.

## Task 10: Final Review Before Handoff

**Files:**
- No planned source edits unless review finds a defect.

- [ ] **Step 1: Confirm git status**

Run:

```bash
git status --short
```

Expected result: only intentional generated output files may be untracked or modified. Do not stage `output/` files unless the repository already tracks that exact generated artifact and the user requested it.

- [ ] **Step 2: Review final diff**

Run:

```bash
git log --oneline -10
git diff HEAD~8..HEAD --stat
```

Expected result: commits cover model, registry, extractor, composer, skill docs, repo docs, and verification fixes when needed.

- [ ] **Step 3: Summarize implementation outcome**

Report:

```text
Implemented company-profile as the first required multi-agent stage.
Verified with python -m unittest discover plugins/invest-flow -p 'test_*.py'.
Verified MRVL prompt plan starts with company-profile and has 7 stages.
Generated output files were left unstaged.
```

Do not claim that real investment reports were generated unless the child skills were actually executed and saved.
