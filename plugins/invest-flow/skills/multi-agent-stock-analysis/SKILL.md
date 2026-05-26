---
name: multi-agent-stock-analysis
description: "多Agent协同股票分析系统 - 同时运行基本面分析、机构资金流向分析和GIE投资框架分析三个维度，自动聚合结果并生成综合投资建议。适用于：(1) 需要多维度验证的投资决策, (2) 寻找高置信度交易机会, (3) 全面评估标的投资价值。MainAgent自动协调，无需手动管理SubAgent。"
---

# 多Agent协同股票分析系统

## 概述

本系统通过命令驱动的轻量 Pipeline 实现多维度股票分析。当前默认兼容流程为：

```text
用户请求
  -> CLI / Python API
  -> Intent Request
  -> Basic Stock Planner
  -> 并行执行 3 个 Skill
       fundamental-analysis
       institutional-accumulation-analysis
       gie-investment-framework
  -> Handoff Extractor
  -> Decision Composer
  -> orchestration JSON + 中文综合摘要
```

Phase 1 保持旧三件套流程兼容；后续阶段会把 `market-data-router`、`reflexivity-*`、`professional-investment-analyst`、`daily-us-market-scan` 和 AI 基建相关 skill 接入更多 workflow preset。

**核心价值：**
- ⚡ **并行处理**：3个维度同时分析，节省时间
- 🎯 **交叉验证**：多维度结论一致时置信度大幅提升
- 🔍 **风险识别**：不同维度发现的风险相互印证
- 🤖 **自动协调**：MainAgent自动管理SubAgent生命周期
- 🔄 **失败重试**：自动检测失败并重试，确保分析完整性

## 快速开始

### 使用方法

只需在对话中说出：

> "请使用多Agent系统分析 TSLA"
> "对 宁德时代 执行全面投资分析"
> "分析 Apple 的多维度投资机会"

系统会自动：
1. 解析股票代码和名称
2. 并行启动3个SubAgent
3. 等待所有分析完成
4. 生成综合投资建议

## 详细工作流程

### Step 1: 解析用户请求

MainAgent识别：
- 股票代码（如 TSLA）
- 公司名称（如 Tesla）
- 分析类型（默认 full）

### Step 2: 生成兼容执行计划

默认 `stock_decision_basic` 计划包含：

| Agent | Skill | 默认命令 |
|---|---|---|
| fundamental | `fundamental-analysis` | `opencode run "/fundamental-analysis {ticker}" --format default` |
| institutional | `institutional-accumulation-analysis` | `opencode run "/institutional-accumulation-analysis {ticker}" --format default` |
| gie | `gie-investment-framework` | `opencode run "/gie-investment-framework {ticker}" --format default` |

命令可通过环境变量覆盖：

```bash
export INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS='opencode run "/fundamental-analysis {ticker}" --format default'
export INVESTFLOW_CMD_INSTITUTIONAL_ACCUMULATION_ANALYSIS='opencode run "/institutional-accumulation-analysis {ticker}" --format default'
export INVESTFLOW_CMD_GIE_INVESTMENT_FRAMEWORK='opencode run "/gie-investment-framework {ticker}" --format default'
```

### Step 3: 监控任务执行

MainAgent等待所有SubAgent完成：
- 总超时：5分钟
- 检查间隔：每5秒
- 错误处理：部分失败时继续其他分析

### Step 4: 聚合结果

收集各SubAgent的输出：
```json
{
  "ticker": "TSLA",
  "fundamental": {
    "report_path": "./output/fundamental-analysis/...",
    "stock_type": "Growth",
    "pe_ratio": 290,
    "recommendation": "..."
  },
  "institutional": {
    "report_path": "./output/institutional-accumulation-analysis/...",
    "classification": "派发初级",
    "confidence": 65
  },
  "gie": {
    "report_path": "./output/gie-investment-framework/...",
    "shovel_tier": "Tier 1",
    "investment_rating": "持有"
  }
}
```

### Step 5: 调用SummaryAgent

将聚合数据传递给SummaryAgent生成综合报告。

### Step 6: 输出结果

系统输出两类文件：

- `output/summary/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`
- `output/summary/综合分析-{TICKER}-{YYYY-MM-DD}.md`

综合报告必须包含固定作者字段：`InvestmentFlow`。

## 输出文件结构

```
./output/
├── fundamental-analysis/
│   └── {ticker}-{company}-{date}.md
├── institutional-accumulation-analysis/
│   └── 机构操作分析-{date}-{ticker}.md
├── gie-investment-framework/
│   └── gie-{title}-{date}.md
└── summary/
    └── 综合分析-{ticker}-{date}.md  ← 最终报告
```

## 失败重试机制

### 自动重试策略

当某个SubAgent执行失败时，系统会自动重试（最多1次）：

```
Agent执行 → 结果验证 → 有效? → 是 → 返回结果
                ↓
               否
                ↓
         失败类型判断
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
  空结果      超时        异常
    ↓           ↓           ↓
  重试        重试        重试
```

### 重试触发条件

| 失败类型 | 检测方式 | 重试策略 |
|---------|---------|---------|
| **空输出** | 内容长度<100字符 | 立即重试 |
| **超时** | 超过240秒 | 立即重试 |
| **异常** | 代码抛出异常 | 立即重试 |
| **内容不完整** | 缺少关键词 | 立即重试 |

### 重试配置

```python
OrchestrationConfig(
    max_retries=1,           # 最大重试次数
    timeout_seconds=240,     # 单次超时(秒)
    retry_on_empty=True,     # 空结果时重试
    retry_on_timeout=True,   # 超时时重试
    parallel_execution=True  # 并行执行
)
```

### 降级处理

- 重试后仍失败？→ 标记为失败，但继续其他Agent
- 必要Agent失败？→ 根据配置决定是否中止
- 部分成功？→ 基于成功维度生成报告

## 错误处理

### 部分失败模式
如果3个SubAgent中有2个成功：
- SummaryAgent使用成功数据生成报告
- 在报告中标注缺失的维度和原因

### 全部失败
- MainAgent返回错误信息
- 提供失败原因和重试建议

## 使用示例

### 示例 1: 完整分析
**用户**: "分析 TSLA"

**系统执行**:
1. 启动3个SubAgent并行分析
2. 等待约10-15分钟
3. 生成综合报告
4. 输出投资建议

### 示例 2: 指定分析维度
**用户**: "只用基本面和GIE框架分析 宁德时代"

**系统执行**:
1. 仅启动2个SubAgent（跳过机构分析）
2. 基于2个维度生成报告

## 使用 Orchestrator 脚本

### 方式1: Python API

```python
from scripts.orchestrator import analyze_stock_with_retry

# 简单调用
result = analyze_stock_with_retry(
    "TSLA",
    "Tesla",
    max_retries=1,
    execution_mode="command",  # command | mock
)

# 完整配置
result = analyze_stock_with_retry(
    ticker="TSLA",
    company="Tesla",
    max_retries=1,
    timeout=240,
    retry_on_empty=True,
    retry_on_timeout=True,
    parallel_execution=True,
    execution_mode="command",
)
```

### 方式2: 命令行

```bash
# 默认 command 模式（真实执行）
python scripts/orchestrator.py TSLA --execution-mode command

# 调试时可用 mock 模式
python scripts/orchestrator.py TSLA --execution-mode mock
```

### 方式3: 自定义每个 SubAgent 的执行命令（推荐）

```bash
# 按需覆盖默认命令模板（支持 {ticker}/{company} 变量）
export INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS='opencode run "/fundamental-analysis {ticker}" --format default'
export INVESTFLOW_CMD_INSTITUTIONAL_ACCUMULATION_ANALYSIS='opencode run "/institutional-accumulation-analysis {ticker}" --format default'
export INVESTFLOW_CMD_GIE_INVESTMENT_FRAMEWORK='opencode run "/gie-investment-framework {ticker}" --format default'
```

## 注意事项

1. **执行时间**：完整分析通常需要10-15分钟
2. **网络依赖**：SubAgent需要搜索最新数据
3. **部分结果**：即使某个SubAgent失败，也会基于成功维度生成报告
4. **数据时效**：报告基于分析时的最新数据，建议定期更新
5. **重试机制**：失败会自动重试1次，提高成功率

## 资源

### references/
- **workflow-guide.md** - 详细工作流文档
- **data-structure.md** - 数据结构和接口定义

### assets/
- **summary-report-template.md** - 综合报告模板

## 版本信息

**版本**: 1.0.0
**创建日期**: 2026-02-06
**最后更新**: 2026-02-06
