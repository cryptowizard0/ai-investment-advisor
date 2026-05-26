# 多Agent协同分析 - 数据结构定义

当前代码中的数据模型位于：

`scripts/investflow_pipeline/models.py`

核心模型：

- `TaskRequest`
- `SkillSpec`
- `StageResult`
- `Handoff`
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

## SkillSpec

表示一个子 skill 的 prompt plan 配置。

```python
SkillSpec(
    skill_name="gie-investment-framework",
    agent_name="gie",
    stage="single_asset_validation",
    prompt_template="使用 invest-flow:gie-investment-framework 分析 {ticker} / {company}",
    output_dir="output/gie-investment-framework",
    required=True,
    extractor_type="markdown",
)
```

`stock_decision_basic` 默认三件套：

| agent_name | skill_name | prompt_template | required |
| --- | --- | --- | --- |
| fundamental | fundamental-analysis | 使用 invest-flow:fundamental-analysis 分析 {ticker} | true |
| institutional | institutional-accumulation-analysis | 使用 invest-flow:institutional-accumulation-analysis 分析 {ticker} | false |
| gie | gie-investment-framework | 使用 invest-flow:gie-investment-framework 分析 {ticker} / {company} | true |

## StageResult

表示一个维度的状态。生成 prompt plan 时状态为 `pending`；汇总已完成 handoff 时可为 `success` 或 `failed`。

```python
StageResult(
    skill_name="fundamental-analysis",
    agent_name="fundamental",
    status=AnalysisStatus.PENDING,
    output="使用 invest-flow:fundamental-analysis 分析 MRVL",
    prompt="使用 invest-flow:fundamental-analysis 分析 MRVL",
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
    orchestration_json_path="output/summary/orchestration-MRVL-20260526-120001.json",
    prompt_plan_path="output/summary/prompt-plan-MRVL-20260526-120001.md",
)
```

汇总报告示例：

```python
PipelineResult(
    status="partial_success",
    summary_report_path="output/summary/综合分析-MRVL-2026-05-26.md",
    orchestration_json_path="output/summary/orchestration-MRVL-20260526-121000.json",
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

`execution_mode` 只接受 `prompt`。子 skill 的真实执行由 Codex 当前会话完成。

## 输出文件

```text
output/summary/
├── prompt-plan-{TICKER}-{YYYYMMDD-HHMMSS}.md
├── orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json
└── 综合分析-{TICKER}-{YYYY-MM-DD}.md
```

只有 prompt plan 时不生成综合投资结论；只有至少一个成功 handoff 时才生成综合 Markdown 报告。
