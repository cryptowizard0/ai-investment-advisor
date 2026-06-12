---
name: chain-alpha-pipeline
description: "chain-alpha 产业链选股工作流编排：在当前 agent 会话内依次执行 chain-alpha-mismatch-discovery（产业链全景 + 供需错位环节）、chain-alpha-monopoly-screen（拆环节找垄断）、chain-alpha-verification（验证定仓位），强制漏斗纪律并生成中文汇总报告。适用于：(1) 用户从一个大主题出发想走完整的'拆产业链 -> 找关键环节 -> 找可投公司'流程, (2) 用户说'用 chain-alpha 分析 <主题>'。输出保存至 ./output/chain-alpha-pipeline/。"
---

# chain-alpha 产业链选股工作流

## Overview

本 skill 编排 chain-alpha 三步工作流：拆解产业链 -> 分析关键环节 -> 找到可投资公司。它不引入新的分析逻辑，只负责串联三个步骤 skill、传递交接数据、执行漏斗纪律和生成最终汇总。

投资逻辑：找需求增量大、供给跟不上的错位环节；在错位环节里找 CR3 > 50% 的垄断公司、排除低端竞争；最后验证产业位置、收入占比、业绩、估值，推断最大回撤定仓位。

默认输出目录：`./output/chain-alpha-pipeline/`

## Trigger

- `使用 invest-flow:chain-alpha-pipeline 分析 AI 数据中心电力`
- `用 chain-alpha 分析 <大主题>`
- 用户要求从某主题走完整的产业链选股流程

输入必须是用户给定的大主题。未给主题时先要求用户提供，不做全市场扫描。

## Workflow

在当前 agent 会话内依次执行，每步读取对应 skill 的 SKILL.md 和 references 后按其规则完成：

### Step 1: chain-alpha-mismatch-discovery
- 输入：大主题。
- 产出：产业链全景列表 + 2-4 个错位环节（含错位强度评分）。
- 漏斗规则：最多 4 个环节进入下一步；硬门槛未过的环节不得放行。

### Step 2: chain-alpha-monopoly-screen
- 对每个错位环节单独运行。
- 产出：每环节 ≤10 家候选（25 分评分排序），标注 US-listed/ADR。
- 漏斗规则：仅 US-listed/ADR 候选进入 Step 3。

### Step 3: chain-alpha-verification
- 对全部 US-listed/ADR 候选执行硬门槛 + 100 分模型四档分级。
- 产出：每家公司验证卡（档位 + 仓位上限）。
- 漏斗规则：最终汇总报告深挖档位最高的 2-3 家。

### Step 4: 汇总
- 使用 `references/report-template.md` 生成最终中文汇总报告。
- 保存至 `./output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`。
- 文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 报告必须包含固定作者字段：`InvestmentFlow`。

## 推荐用法

一次完整 pipeline 是重活（三步均需 web 检索取证）。日常建议：

1. 先单独跑 Step 1（成本低）：`使用 invest-flow:chain-alpha-mismatch-discovery 分析 <主题>`。
2. 人工确认错位环节靠谱后，再对选中的 1-2 个环节跑 Step 2、3。

## Quality Rules

- 漏斗纪律强制执行：2-4 个环节 -> 每环节 ≤10 家 -> 深挖 2-3 家。
- 每步必须遵守对应步骤 skill 的硬门槛；编排层不得放宽任何门槛。
- 各步骤的独立报告照常保存到各自输出目录，汇总报告引用其文件路径。
- 中文输出；最终输出是研究与跟踪优先级，不是自动交易指令。

## Resources

### references/methodology.md
漏斗纪律、步骤间交接数据字段、降级处理（某步产出为零时怎么办）。

### references/report-template.md
最终汇总报告模板：主题、全景摘要、错位环节、候选漏斗、Top 2-3 深挖卡、金池子/通过清单、跟踪计划。
