---
name: multi-agent-stock-analysis
description: "多Agent协同股票分析系统 - 在 Codex 当前会话中按 prompt 编排公司画像、基本面、机构资金、GIE、反身性、Reportify 和非共识分析，并聚合为中文综合投资判断。适用于：(1) 需要多维度验证的投资决策, (2) 寻找高置信度交易机会, (3) 全面评估标的投资价值。"
---

# 多Agent协同股票分析系统

## 概述

本 skill 的当前真实入口是 Codex 会话内的 prompt 编排：解析用户给出的 ticker/company，依次调用七个 InvestFlow 子 skill，收集公司画像、结论、证据、风险、置信度、数据缺口和非共识变量，然后直接输出中文综合报告。

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

Python 脚本仅保留为 prompt plan / handoff 汇总辅助能力，不负责启动另一个 agent，也不执行外部命令。

## 推荐使用方式

在 Codex 中直接说：

```text
使用 invest-flow:multi-agent-stock-analysis 分析 MRVL
```

如果用户提供公司名，同时保留公司名：

```text
使用 invest-flow:multi-agent-stock-analysis 分析 MRVL / Marvell Technology
```

## 执行步骤

### Step 1: 解析标的

- `ticker`：标准化为大写，例如 `MRVL`
- `company`：如果用户提供则保留，例如 `Marvell Technology`；否则使用 ticker

### Step 2: 执行七段子 Skill Prompt

按顺序在当前 Codex 会话中执行：

```text
使用 invest-flow:company-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
```

```text
使用 invest-flow:fundamental-analysis 分析 {ticker}
```

```text
使用 invest-flow:institutional-accumulation-analysis 分析 {ticker}
```

```text
使用 invest-flow:gie-investment-framework 分析 {ticker} / {company}
```

```text
使用 invest-flow:reflexivity-deep-analysis 分析 {ticker}
```

```text
使用 invest-flow:reportify-stock-analysis 分析 {ticker}
```

```text
使用 invest-flow:non-consensus-company-discovery 评估 {ticker} / {company} 的非共识重估机会
```

执行每个子 skill 后，提取以下 handoff 字段：

- `conclusion`：核心结论
- `recommendation`：操作建议或评级
- `confidence`：置信度
- `key_evidence`：关键证据
- `risk_flags`：风险信号
- `contradiction_points`：与其他维度冲突的观点
- `monitoring_signals`：后续监控指标
- `data_gaps`：缺失数据或待验证事实

七个维度的职责：

| 维度 | 目标 |
| --- | --- |
| company-profile | 公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位 |
| fundamental-analysis | 公司基本面、财务、估值和技术面 |
| institutional-accumulation-analysis | 资金行为、量价结构和主力意图 |
| gie-investment-framework | 1-3 年金铲子属性、供需瓶颈和择时 |
| reflexivity-deep-analysis | 叙事、价格、现实验证和反转风险 |
| reportify-stock-analysis | 统一八段式事实-解释-决策报告 |
| non-consensus-company-discovery | 非共识重估假设、催化剂和反证条件 |

### Step 3: 生成综合报告

最终输出中文 Markdown 报告，固定包含：

```markdown
# 综合分析报告 - {ticker}

作者：InvestmentFlow

## 公司画像摘要
## 执行摘要
## 七维度结论对照
## 证据汇总
## 分歧与冲突
## 风险清单
## 决策看板
## 数据缺口与待验证事项
## 后续跟踪信号
## 投资免责声明
```

综合结论必须说明：

- 七个维度是否互相印证
- 反身性阶段处于启动、强化、透支还是反转
- Reportify 的标准化结论是否支持其他维度
- 是否存在可验证的非共识重估变量
- 哪些证据最强，哪些证据最弱
- 是否存在明显分歧
- 当前适合 `买入 / 观察 / 减仓 / 回避` 中的哪一类动作
- 置信度与触发重新评估的条件

## Prompt Plan 辅助脚本

如需生成可复制的 prompt plan，可从仓库根目录运行：

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py MRVL --company "Marvell Technology"
```

该脚本只输出：

- `output/summary/prompt-plan-{TICKER}-{YYYYMMDD-HHMMSS}.md`
- `output/summary/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`

它不会执行七个子 skill。真实分析仍由 Codex 当前会话按上面的七段 prompt 完成。

## 汇总已有 Handoff

如果用户已经提供子报告或 handoff，跳过对应子 skill 执行，直接按综合模板汇总。部分缺失时：

- 明确标注缺失维度
- 不用缺失维度推断强结论
- 将缺失内容写入“数据缺口与待验证事项”

## 输出路径约定

```text
output/
├── company-profile/
├── fundamental-analysis/
├── institutional-accumulation-analysis/
├── gie-investment-framework/
├── reflexivity-deep-analysis/
├── reportify-stock-analysis/
├── non-consensus-company-discovery/
└── summary/
    ├── prompt-plan-{TICKER}-{YYYYMMDD-HHMMSS}.md
    ├── orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json
    └── 综合分析-{TICKER}-{YYYY-MM-DD}.md
```

如输出文件已存在，脚本应追加 `(1)`、`(2)` 等编号，避免覆盖。

## 注意事项

1. 金融数据和新闻信息具有时效性；分析时必须使用当前可得事实。
2. 七个维度结论不一致时，不要强行给高置信度结论。
3. 机构资金流和技术信号只能作为概率证据，不能替代基本面判断。
4. GIE 框架偏 1-3 年中期弹性，不能直接等同短线交易信号。
5. 本报告仅用于研究与教育目的，不构成投资建议。

## 资源

### references/
- `workflow-guide.md` - prompt-native 工作流文档
- `data-structure.md` - 当前 prompt plan / handoff 数据结构

### assets/
- `summary-report-template.md` - 综合报告模板
