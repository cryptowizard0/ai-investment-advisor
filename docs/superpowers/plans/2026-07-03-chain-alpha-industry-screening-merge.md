# chain-alpha 行业筛选框架合并 Handoff Plan

## Summary

目标：不改 skill 名称，保留 `chain-alpha-mismatch-discovery`，但把用户的行业筛选三步合并进 Step 1 和 pipeline 表述。

合并后的主流程：

```text
行业是什么 -> 增长快吗 -> 哪些环节供需错位 -> 哪些公司有垄断格局 -> 哪些公司可以买
```

## Key Changes

- 保留现有 skill 名称和目录：
  - `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/`
  - `name: chain-alpha-mismatch-discovery`
  - `output/chain-alpha-mismatch-discovery/`

- 更新 Step 1 定位：
  - 从“产业链全景 + 供需错位发现”扩展为“行业定义 + 增长初筛 + 产业链全景 + 供需错位发现”。
  - 新增“行业是什么”：细分行业、解决问题、商业逻辑、终端客户/预算来源、价值链赚钱方式。
  - 新增“增长快吗”：行业/环节增速是否 >20%、为什么快、能持续多久。
  - 保留现有硬门槛：需求增量证据 + 供给约束实证 + 可持续利润增速 >=20%。

- 保持 Step 2 / Step 3 不变：
  - `chain-alpha-monopoly-screen` 继续负责 CR3 >50%、技术/认证壁垒、扩产难、毛利率、环节收入占比、利润增速。
  - `chain-alpha-verification` 继续负责收入占比、利润增速、估值、回撤、仓位。

## Implementation Tasks

- [ ] Update `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`:
  - Rewrite description to include “行业定义、增长初筛、产业链全景、供需错位环节发现”。
  - Add workflow section “行业定义” before产业链全景。
  - Add workflow section “增长判断” before错位环节识别。
  - Explicitly state: industry/revenue growth >20% is an initial screen; sustainable profit growth >=20% remains the release gate; >=30% is preferred.
  - Keep supply-response clock, pricing-degree evidence, 30-point scoring, output path, and file naming unchanged.

- [ ] Update `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/methodology.md`:
  - Add methodology for “行业是什么”：细分行业、解决问题、商业逻辑、终端客户、预算来源、价值链盈利方式。
  - Add methodology for “增长快吗”：增速是否 >20%、增长来源、持续时间、预算落地、渗透率/单位用量/替换周期。
  - Keep existing supply-demand mismatch judgment, hard gates, supply-response clock, pricing-degree scoring, and profit-growth scoring.

- [ ] Update `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/report-template.md`:
  - Add sections:
    - `## 二、行业定义`
    - `## 三、增长判断`
  - Shift existing产业链全景、错位卡片、评分汇总 sections down.
  - Include fields for growth rate, growth driver, expected duration, budget source, evidence source/date.
  - Keep existing output fields for供给响应时钟、错位定价程度、事实/推断/假设、数据来源。

- [ ] Update `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`:
  - Rewrite pipeline investment logic as: “先判断行业是什么和增长是否足够快，再从完整产业链中寻找供需错位环节，随后筛选 CR3 高、壁垒强、扩产难的垄断公司，最后验证利润增速、估值和仓位。”
  - Rename Step 1 heading text only to include “行业定义与增长初筛”。
  - Keep skill name `chain-alpha-mismatch-discovery` and fan-out behavior unchanged.

- [ ] Optionally update `plugins/invest-flow/skills/chain-alpha-pipeline/references/report-template.md`:
  - Add a summary table mapping final results to:
    - 行业是什么
    - 增长快吗
    - 供需关系好的环节
  - Do not alter handoff fields or output path.

- [ ] Update active docs if they describe Step 1 narrowly:
  - `AGENTS.md`
  - `README.md`
  - `README.zh-CN.md`
  - Keep the skill name unchanged; only update wording to include行业定义和增长初筛。

## Test Plan

- Check required wording:
  - `rg "行业是什么|增长快吗|供需关系好的环节" plugins/invest-flow/skills/chain-alpha-* AGENTS.md README.md README.zh-CN.md`
  - `rg "收入增速.*初筛|利润增速.*硬门槛|CR3" plugins/invest-flow/skills/chain-alpha-*`

- Check no accidental rename:
  - `test -d plugins/invest-flow/skills/chain-alpha-mismatch-discovery`
  - `rg "name: chain-alpha-mismatch-discovery" plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`

- Check stale unexpected new name does not appear:
  - `! rg "chain-alpha-industry-mismatch-discovery" plugins AGENTS.md README.md README.zh-CN.md`

## Assumptions

- Skill 名称暂不改，仍使用 `chain-alpha-mismatch-discovery`。
- 这是 Markdown skill/docs 更新，不需要 Python 代码改动。
- 不需要 plugin version bump。
- CR3、技术壁垒、扩产难仍主要放在 `chain-alpha-monopoly-screen`，不前置为 Step 1 硬门槛。
