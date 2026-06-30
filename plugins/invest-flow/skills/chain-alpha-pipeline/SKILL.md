---
name: chain-alpha-pipeline
description: "chain-alpha 产业链选股工作流编排：主 agent 跨步串行调度三步（chain-alpha-mismatch-discovery 产业链全景+供需错位环节、chain-alpha-monopoly-screen 拆环节找垄断、chain-alpha-verification 验证定仓位），步内默认 fan-out 到 subagent 并行（Claude Code 原生支持；Codex 在 subagent 派发工具可用时默认启用），不满足并行条件时降级为会话内串行，强制漏斗纪律并生成中文汇总报告。适用于：(1) 用户从一个大主题出发想走完整的'拆产业链 -> 找关键环节 -> 找可投公司'流程, (2) 用户说'用 chain-alpha 分析 「主题」'。输出保存至 ./output/chain-alpha-pipeline/。"
---

# chain-alpha 产业链选股工作流

## Overview

本 skill 编排 chain-alpha 三步工作流：拆解产业链 -> 分析关键环节 -> 找到可投资公司。它不引入新的分析逻辑，只负责调度三个步骤 skill、传递交接数据、执行漏斗纪律和生成最终汇总。

调度形态：主 agent 跨步串行；步内对可拆分单元 fan-out 到 subagent 并行（第二步按环节、第三步按公司）。支持且允许 subagent 派发的 agent 会话进入并行模式；不满足并行条件时降级为会话内串行，产出格式一致。

投资逻辑：找需求增量大、供给跟不上的错位环节；在错位环节里找 CR3 > 50% 的垄断公司、排除低端竞争；最后验证产业位置、收入占比、业绩、估值，推断最大回撤定仓位。

默认输出目录：`./output/chain-alpha-pipeline/`

## Trigger

- `使用 invest-flow:chain-alpha-pipeline 分析 AI 数据中心电力`
- `用 chain-alpha 分析 <大主题>`
- 用户要求从某主题走完整的产业链选股流程

输入必须是用户给定的大主题。未给主题时先要求用户提供，不做全市场扫描。

## Workflow

读取 `references/methodology.md`（执行模式、fan-out 规则、失败处理）和 `references/subagent-prompts.md`（派发模板）后执行。

### Step 0: 能力探测
判断当前 agent 会话是否支持派发 subagent：
- Claude Code：若平台支持 Task/subagent 派发，进入并行模式。
- Codex：若当前会话暴露 subagent 派发工具，默认进入并行模式。
- 其他情况（工具不可用、探测失败或派发失败）：串行降级模式，行为与产出格式等价。

### Step 1: chain-alpha-mismatch-discovery（主 agent 自己做）
- 输入：大主题。
- 产出：产业链全景列表 + 2-4 个错位环节（含错位强度评分）。
- 漏斗规则：最多 4 个环节进入下一步；硬门槛未过的环节不得放行。
- 全景不可分，不 fan-out。

### Step 2: chain-alpha-monopoly-screen（步内 fan-out）
- 并行模式：每个错位环节派一个 subagent（按 `subagent-prompts.md` 的 Step 2 模板），N≤4（在单波 ≤6 上限内，无需分批）。
- 串行模式：在当前会话内对每个环节顺序执行。
- 每个工作单元产出：该环节 ≤10 家候选（25 分排序），标注上市地与可投性。
- 主 agent 收齐各环节交接字段，汇总候选池，跨市场按 25 分排序，挑可投主板候选 top-K（默认 6）进入 Step 3。

### Step 3: chain-alpha-verification（步内 fan-out）
- 并行模式：每家入选公司派一个 subagent（按 Step 3 模板），M≤6，单波 ≤6。
- 串行模式：在当前会话内对每家公司顺序执行。
- 每个工作单元产出：占比双轨硬门槛 + 100 分模型四档 + 验证卡（档位 + 仓位上限）。
- 主 agent 收齐验证卡交接字段。

### Step 4: 汇总（主 agent）
- 使用 `references/report-template.md` 生成最终中文汇总报告。
- 深挖档位最高的 2-3 家。
- 保存至 `./output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`。
- 文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 报告必须包含固定作者字段：`InvestmentFlow`。

## 推荐用法

一次完整 pipeline 是重活（三步均需 web 检索取证）。日常建议：

1. 先单独跑 Step 1（成本低）：`使用 invest-flow:chain-alpha-mismatch-discovery 分析 <主题>`。
2. 人工确认错位环节靠谱后，再对选中的 1-2 个环节跑 Step 2、3。
3. 完整 pipeline 建议在单独会话运行；并行模式下 subagent 各自独立上下文，主会话只保留交接字段。
4. 进入 `待验证` 的标的，后续用 `使用 invest-flow:chain-alpha-delivery-tracking 跟踪 <TICKER>` 做按季营收兑现追踪与升降档，不必每次重跑完整 pipeline。

## Quality Rules

- 漏斗纪律强制执行：2-4 个环节 -> 每环节 ≤10 家 -> 深挖 2-3 家。fan-out 不放宽任何门槛。
- 每步必须遵守对应步骤 skill 的硬门槛；编排层不得放宽。
- 并行与串行两模式的硬门槛、交接字段、报告格式必须一致。
- subagent 失败不整体中止：按 `methodology.md` 第 5 节标注并降级。
- 各步骤的独立报告照常保存到各自输出目录，汇总报告引用其文件路径。
- 中文输出；最终输出是研究与跟踪优先级，不是自动交易指令。

## Resources

### references/methodology.md
执行模式与能力探测、fan-out 规则、漏斗纪律、交接字段、并行失败与降级处理、会话成本控制。

### references/subagent-prompts.md
Step 2 / Step 3 的 subagent 派发模板与交接字段契约，含 Codex 并行约束与串行降级说明。

### references/report-template.md
最终汇总报告模板：主题、全景摘要、错位环节、候选漏斗、Top 2-3 深挖卡、金池子/通过清单、跟踪计划。
