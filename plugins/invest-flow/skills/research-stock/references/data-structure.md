# 多Agent协同分析 - 数据结构定义

当前代码中的数据模型位于：

`scripts/investflow_pipeline/models.py`

核心模型：

- `TaskRequest`
- `SkillSpec`
- `StageResult`
- `Handoff`
- `CompanyProfile`
- `PipelineResult`
- `OrchestrationConfig`

## TaskRequest

表示一次股票分析请求。

```python
TaskRequest(
    task_id="ma_20260526_120000_ab12cd34",
    intent="stock_decision_basic",
    target="MRVL",
    ticker="MRVL",
    company_name="Marvell Technology",
    market="unknown",
    horizon="mixed",
requested_outputs=["summary", "handoff_json"],
)
```

实际执行完整分析时，`requested_outputs` 隐含要求每个子 skill 同时产出 Markdown 子报告路径；`handoff_json` 只用于综合，不替代子报告。

## SkillSpec

表示一个子 skill 的 prompt plan 配置。

```python
SkillSpec(
    skill_name="research-fundamentals",
    agent_name="fundamental",
    stage="single_asset_validation",
    prompt_template="使用 invest-flow:research-fundamentals 分析 {ticker}",
    output_dir="output/research-fundamentals",
    required=True,
    extractor_type="markdown",
)
```

`stock_decision_basic` 默认五维度：

| agent_name | skill_name | prompt_template | required |
| --- | --- | --- | --- |
| company_profile | research-profile | 使用 invest-flow:research-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位 | true |
| fundamental | research-fundamentals | 使用 invest-flow:research-fundamentals 分析 {ticker} | true |
| institutional | research-institutional | 使用 invest-flow:research-institutional 分析 {ticker} | false |
| reflexivity | research-reflexivity | 使用 invest-flow:research-reflexivity 对 {ticker} 做深度反身性分析 | false |
| reportify | research-reportify | 使用 invest-flow:research-reportify 分析 {ticker} | false |

`research-earnings` 作为可选 registry spec 保留，仅在用户明确指定报告期或出现相关新财报事件时加入；它不属于 `basic_stock_specs()`。

## StageResult

表示一个维度的状态。生成 prompt plan 时状态为 `pending`；汇总已完成 handoff 时可为 `success` 或 `failed`。

```python
StageResult(
    skill_name="research-fundamentals",
    agent_name="fundamental",
    status=AnalysisStatus.PENDING,
    output="使用 invest-flow:research-fundamentals 分析 MRVL",
    prompt="使用 invest-flow:research-fundamentals 分析 MRVL",
)
```

序列化字段：

- `skill_name`
- `agent_name`
- `status`
- `report_path`
- `handoff`
- `errors`
- `duration`
- `retry_count`
- `prompt`

`retry_count` 仅保留兼容字段；当前 prompt-native 运行面不会自动重试子 skill。

完整分析中，`success` 阶段必须带有 `report_path`，且路径应指向该阶段对应目录下的 Markdown 文件，例如 `output/research-fundamentals/research-fundamentals-HPE-Hewlett-Packard-Enterprise-2026-06-03.md`。如果只有 handoff、没有 `report_path`，应视为 `partial` 或补跑，而不是完整成功。

## Handoff

所有子 skill 输出都应尽量压缩为以下结构，供综合报告使用：

```python
Handoff(
    conclusion="核心结论",
    recommendation="观望",
    confidence=65,
    key_evidence=["证据1", "证据2"],
    risk_flags=["风险1"],
    contradiction_points=["分歧1"],
    monitoring_signals=["跟踪指标1"],
    data_gaps=["缺失数据1"],
)
```

Handoff 是综合报告的结构化摘要；它不能替代子报告。MainAgent 汇总前必须同时保存原始子报告路径，供综合报告的 `## 子报告索引` 引用。

### CompanyProfile

`research-profile` 阶段会在 `Handoff.company_profile` 中提供结构化公司画像：

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

## PipelineResult

表示一次编排的最终状态。

Prompt plan 示例：

```python
PipelineResult(
    task_id="ma_20260526_120000_ab12cd34",
    status="prompt_plan",
    intent="stock_decision_basic",
    target="MRVL",
    ticker="MRVL",
    company_name="Marvell Technology",
    started_at="2026-05-26T12:00:00",
    ended_at="2026-05-26T12:00:01",
    stage_results=[...],
    summary_report_path=None,
    orchestration_json_path="output/research-stock/orchestration-MRVL-20260526-120001.json",
    prompt_plan_path="output/research-stock/prompt-plan-MRVL-20260526-120001.md",
)
```

汇总报告示例：

```python
PipelineResult(
    status="partial_success",
    summary_report_path="output/research-stock/research-stock-MRVL-2026-05-26.md",
    orchestration_json_path="output/research-stock/orchestration-MRVL-20260526-121000.json",
    prompt_plan_path=None,
    stage_results=[...],
)
```

`to_dict()` 会计算：

- `completed_count`
- `failed_count`
- `pending_count`
- `total_count`
- `agents`

## OrchestrationConfig

当前只保留 prompt-native 配置面：

```python
OrchestrationConfig(
    execution_mode="prompt",
    parallel_execution=True,
    continue_on_failure=True,
)
```

`execution_mode` 只接受 `prompt`。子 skill 的真实执行由当前 agent 会话完成。

## 输出文件

```text
output/research-stock/
├── prompt-plan-{TICKER}-{YYYYMMDD-HHMMSS}.md
├── orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json
└── research-stock-{TICKER}-{YYYY-MM-DD}.md
```

只有 prompt plan 时不生成综合投资结论；只有至少一个成功 handoff 时才生成综合 Markdown 报告。

正式综合个股分析还应生成五个默认子报告目录中的 Markdown 文件：

```text
output/research-profile/
output/research-fundamentals/
output/research-institutional/
output/research-reflexivity/
output/research-reportify/
```

若某个维度没有 `report_path`，综合报告必须在 `## 数据缺口与待验证事项` 和 `## 子报告索引` 中标注；默认行为是先补跑该维度，而不是直接用 handoff 汇总。
