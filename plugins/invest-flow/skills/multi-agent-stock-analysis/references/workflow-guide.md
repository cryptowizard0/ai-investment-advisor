# 多Agent协同分析 - 详细工作流指南

> 当前实现为 Phase 1 命令驱动 Pipeline。历史文档中出现的 `delegate_task` 伪代码仅表示目标架构概念，不是当前脚本调用方式。当前真实入口是 `scripts/orchestrator.py`，核心逻辑位于 `scripts/investflow_pipeline/`。

## 当前执行路径（Phase 1）

```text
用户请求
  -> CLI / Python API
  -> Pipeline
  -> Planner
  -> Executor
  -> Extractor
  -> Composer
  -> output/summary/orchestration-*.json + 综合分析 Markdown
```

## 阶段说明

### 阶段1: Request -> Planner

- 输入：ticker/company/analysis_type（默认 `full`）
- 输出：`stock_decision_basic` 计划
- 默认包含三个分析维度：
  - `fundamental-analysis`
  - `institutional-accumulation-analysis`
  - `gie-investment-framework`

### 阶段2: Planner -> Executor

Executor 根据计划并行执行命令。默认命令模板：

```bash
opencode run "/fundamental-analysis {ticker}" --format default
opencode run "/institutional-accumulation-analysis {ticker}" --format default
opencode run "/gie-investment-framework {ticker}" --format default
```

可通过环境变量覆盖：

```bash
export INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS='opencode run "/fundamental-analysis {ticker}" --format default'
export INVESTFLOW_CMD_INSTITUTIONAL_ACCUMULATION_ANALYSIS='opencode run "/institutional-accumulation-analysis {ticker}" --format default'
export INVESTFLOW_CMD_GIE_INVESTMENT_FRAMEWORK='opencode run "/gie-investment-framework {ticker}" --format default'
```

### 阶段3: Executor -> Extractor

Extractor 汇总各维度产出并标准化 handoff 数据：

- 报告路径
- 关键结论/风险
- 执行状态（成功、失败、重试次数）

失败控制由配置项决定：

- `max_retries`
- `timeout_seconds`
- `parallel_execution`
- `continue_on_failure`

### 阶段4: Extractor -> Composer

Composer 生成最终输出：

- `output/summary/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`
- `output/summary/综合分析-{TICKER}-{YYYY-MM-DD}.md`

综合报告固定作者字段：`InvestmentFlow`。

## 入口示例

### CLI

```bash
python scripts/orchestrator.py TSLA --execution-mode command
python scripts/orchestrator.py TSLA --execution-mode mock
```

### Python API

```python
from scripts.orchestrator import analyze_stock_with_retry, OrchestrationConfig

result = analyze_stock_with_retry(
    ticker="TSLA",
    company="Tesla",
    config=OrchestrationConfig(
        execution_mode="command",
        max_retries=1,
        timeout_seconds=240,
        parallel_execution=True,
        continue_on_failure=True,
    ),
)
```

## 历史设计参考（非当前执行路径）

- “MainAgent / SubAgent / SummaryAgent” 术语仅用于表达职责分层。
- 真实运行时以 `scripts/orchestrator.py` + `scripts/investflow_pipeline/` 为准。
