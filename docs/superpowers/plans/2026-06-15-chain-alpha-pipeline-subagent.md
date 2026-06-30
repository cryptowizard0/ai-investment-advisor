# chain-alpha-pipeline subagent 化重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `chain-alpha-pipeline` 编排层改造为「主 agent 跨步串行调度 + 步内 fan-out 到 subagent 并行 + 主 agent 汇总」，并保持 Codex/Claude Code 双模式降级，三个步骤 skill 零改动。

**Architecture:** 只改 `chain-alpha-pipeline` 这一个 skill 包。重写 `SKILL.md`（能力探测 + fan-out 工作流 + 串行降级）、扩写 `references/methodology.md`（fan-out 规则、并行失败处理、top-K 收口、批次上限，保留现有漏斗纪律与降级分支）、新增 `references/subagent-prompts.md`（派发模板与交接字段契约）。无 Python 脚本。

**Tech Stack:** Markdown skill 包、YAML frontmatter、subagent 派发（Claude Code Task/Agent；Codex 降级串行）。

**Worker notes:**
- 全部新文件内容已完整写在本计划中，按原文写入即可。
- 三个步骤 skill（mismatch-discovery / monopoly-screen / verification）严禁改动——它们是 subagent 的工作单元。
- 平台中立措辞：说"agent 会话"或并列 Codex/Claude Code，不写死单平台。
- 不 bump 版本：invest-flow 0.3.0 尚未发布（PR 未合并），本次为编排层内容增强，沿用 0.3.0，避免版本号 churn。这是有意决定。
- commit message 末尾加 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。
- 基准 spec：`docs/superpowers/specs/2026-06-15-chain-alpha-pipeline-subagent-design.md`。

---

### Task 1: 新增 subagent 派发模板 references/subagent-prompts.md

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md`

- [ ] **Step 1: 写入 references/subagent-prompts.md**

````markdown
# chain-alpha-pipeline subagent 派发模板

本文件供主 agent 在并行模式下派发 Step 2 / Step 3 子任务使用。每个 subagent 是独立、无本会话记忆的执行单元：prompt 必须自包含，带齐输入上下文与交接字段要求。

## 通用约定

- 每个 subagent 只跑一个步骤 skill、只处理一个工作单元（单环节或单公司）。
- subagent 必须：(1) 读取对应步骤 skill 的 SKILL.md 与 references 后按其规则执行；(2) 把报告写到该 skill 的 output 目录；(3) 在 final message 末尾返回约定的结构化交接字段。
- 主 agent 默认用返回的交接字段汇总，不回读报告文件；仅在字段缺失或需要核对时回读 `report_path`。
- 中文输出；区分 事实 / 推断 / 假设；不得编造数据。

## Step 2 派发模板（每个错位环节一个 subagent）

输入占位符：`{主题}`、`{环节名称}`、`{环节在全景中的位置}`、`{错位强度评分}`、`{需求证据摘要}`、`{供给证据摘要}`、`{供给约束实证清单}`、`{Step1报告路径}`。

```text
你是 chain-alpha 工作流第二步的执行单元。只处理一个错位环节，不要扩展到其他环节。

主题：{主题}
目标环节：{环节名称}（在产业链全景中的位置：{环节在全景中的位置}）
第一步结论：错位强度评分 {错位强度评分}；需求证据={需求证据摘要}；供给证据={供给证据摘要}；供给约束实证={供给约束实证清单}。第一步报告：{Step1报告路径}。

任务：
1. 读取 invest-flow:chain-alpha-monopoly-screen 的 SKILL.md 与 references/methodology.md，严格按其规则执行。
2. 拆该环节上中下游子环节；列全球公司格局（必须含中国大陆及日韩台欧）。
3. 先执行硬门槛（CR3>50% 或寡头证据；毛利<25% 且无壁垒剔除；占比<20% 初筛剔除），再按 25 分候选评分排序，取前 ≤10 家。
4. 把报告写到 output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节名称}-{YYYY-MM-DD}.md（已存在则追加 (1)(2)）。

在 final message 末尾输出如下结构化交接（每家候选一行），不要省略字段：
report_path: <报告路径>
candidates:
- 公司 | Ticker | 子环节 | 候选25分 | 占比初值(置信度) | CR3证据等级 | 是否美股或ADR(是/否/仅粉单) | 待第三步核实事项
若该环节 0 家通过硬门槛：注明"格局分散，暂不可投"并列格局最好的公司作背景。
```

## Step 3 派发模板（每家入选公司一个 subagent）

输入占位符：`{主题}`、`{环节名称}`、`{公司}`、`{Ticker}`、`{子环节}`、`{候选25分}`、`{占比初值与置信度}`、`{CR3证据等级}`、`{待核实事项}`、`{Step2报告路径}`。

```text
你是 chain-alpha 工作流第三步的执行单元。只验证一家公司，不要扩展到其他公司。

主题：{主题}；所属环节：{环节名称}；公司：{公司}（{Ticker}）；子环节：{子环节}。
第二步结论：候选 25 分={候选25分}；占比初值={占比初值与置信度}；CR3 证据等级={CR3证据等级}；待核实事项={待核实事项}。第二步报告：{Step2报告路径}。

任务：
1. 读取 invest-flow:chain-alpha-verification 的 SKILL.md 与 references/methodology.md，严格按其规则执行。
2. 先执行占比双轨硬门槛（≥40% 纯正 / 20-40% 增量贡献测试 / <20% 剔除），再按 100 分模型评分并定四档（金池子≥80 / 通过65-79 / 待验证50-64 / 剔除<50），含负分项。
3. 推断最大回撤（历史/估值压缩/业绩 miss 三情景取最大），按风险预算法算仓位上限（默认风险预算 2%；"通过"×0.5；弹性标的 ×0.5，可叠乘）。
4. 把验证卡写到 output/chain-alpha-verification/chain-alpha-verification-{Ticker}-{YYYY-MM-DD}.md（已存在则追加 (1)(2)）。

在 final message 末尾输出如下结构化交接，不要省略字段：
report_path: <报告路径>
档位: <金池子/通过/待验证/剔除>
总分: <N>/100（含负分 <-N>）
仓位上限: <N>% 或 不适用
反证条件: <要点>
跟踪指标: <要点>
若数据不足无法定档：返回"验证未完成"并说明缺什么数据，不要编造档位或仓位。
```

## 串行降级模式

若当前 agent 会话不支持派发 subagent（如 Codex），主 agent 不使用本文件的派发动作，改为在当前会话内对每个环节/公司顺序套用上述同样的任务说明与交接字段，产出格式完全一致。
````

- [ ] **Step 2: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md
git commit -m "Add chain-alpha-pipeline subagent dispatch prompt templates

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 扩写 references/methodology.md（fan-out 规则 + 并行失败处理）

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md`（整体重写，保留原有第 1/2/3 节内容并扩充）

- [ ] **Step 1: 用以下完整内容覆盖 methodology.md**

````markdown
# chain-alpha-pipeline 编排方法论

## 1. 执行模式与能力探测

主 agent 跨步串行（Step 1 → 2 → 3 → 汇总），步内对可拆分的工作单元 fan-out。

开始时探测当前 agent 会话是否支持派发 subagent（并行子任务）：

- **支持（如 Claude Code）**：进入并行模式，Step 2 按环节、Step 3 按公司 fan-out。
- **不支持（如 Codex）**：降级为串行模式，在当前会话内顺序处理每个环节/公司。

两种模式的硬门槛、漏斗纪律、交接字段、报告格式完全一致；唯一区别是是否并行。降级是默认安全路径——任何探测失败或派发不可用，都回到串行模式，保证两平台报告可比。

## 2. fan-out 规则

| 步骤 | fan-out 维度 | 并行单元数 | 收口 |
|---|---|---|---|
| Step 1 | 不 fan-out（全景不可分） | 主 agent 自己做 | 产出 2-4 个错位环节 |
| Step 2 | 每个错位环节 1 个 subagent | N ≤ 4 | 主 agent 汇总候选池，按 25 分排序 |
| Step 3 | 每家入选公司 1 个 subagent | M ≤ 6 | 主 agent 汇总验证卡 |

- **Step 3 收口（top-K）**：Step 2 的美股/ADR 候选可能很多，主 agent 按 25 分排序只取 **top-K（默认 6）** 进入 Step 3 fan-out，不对全部美股候选逐一验证。
- **批次上限**：单波并行默认 ≤6 个 subagent，超出分批顺序派发。
- 派发模板见 `references/subagent-prompts.md`。

## 3. 漏斗纪律

fan-out 不放宽任何门槛。

| 阶段 | 上限 | 不足时 |
|---|---|---|
| Step 1 错位环节 | 2-4 个 | 0 个则终止流程，输出全景列表 + 观察池，说明缺什么证据 |
| Step 2 每环节候选 | ≤10 家 | 0 家则该环节标"格局分散，暂不可投"，列格局最好的公司作背景 |
| Step 3 深挖 | 2-3 家 | 无"通过"及以上档位时触发兜底规则：列出被剔除但格局最好的公司，不给仓位 |

各步骤 skill 自身的硬门槛（错位双证据、CR3>50%、毛利 25%、占比双轨、100 分四档等）由步骤 skill 强制，编排层不得放宽。

## 4. 步骤间交接数据

Step 1 -> Step 2，每个错位环节传递：环节名称、在全景列表中的位置、错位强度评分、需求/供给证据摘要、供给约束实证清单。

Step 2 -> 主 agent（每家候选）：公司名、Ticker、子环节、候选 25 分、占比初值与置信度、CR3 证据等级、是否美股/ADR、待第三步核实事项。

主 agent -> Step 3（每家入选公司）：上述候选字段 + 待核实事项，作为单公司 verification 的输入上下文。

Step 3 -> 汇总（每家公司）：档位、总分、仓位上限、反证条件、跟踪指标。

主 agent 默认用 subagent final message 返回的交接字段汇总，不回读报告文件；仅在字段缺失或需核对时回读 report_path。

## 5. 失败与降级处理

- **Step 2 某环节 subagent 失败/返回空**：不整体中止；用成功环节继续，汇总报告"候选漏斗"标注该环节"未完成（subagent 失败）"，并入降级章节。
- **Step 3 某公司 subagent 失败/返回"验证未完成"**：该公司标"验证未完成"，不给档位/仓位，其余公司正常汇总。
- **能力探测失败或并行不可用**：整体降级为串行模式，行为与产出格式与并行模式一致。
- **Step 1 全部环节只是"高景气，非错位"**：终止，不强行进入 Step 2；报告给出升级触发条件（出现什么实证再重跑）。
- **Step 2 候选全为非美股**：Step 3 跳过，报告说明可投资性受限于上市地，列出非美股垄断者供参考。
- **数据缺口（占比/CR3 拿不到）**：照常进入下一步但降低置信度标注，不得编造数字。

## 6. 会话成本控制

- 完整 pipeline 建议在单独会话运行，避免主会话上下文耗尽。
- 并行模式下，subagent 各自独立上下文，主会话只保留交接字段，显著降低主会话上下文压力。
- 三步必须顺序执行（后一步输入依赖前一步输出）；步内 fan-out 的多个 subagent 互不依赖，可并行。
````

- [ ] **Step 2: 验证关键规则齐全**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && grep -c -e "能力探测" -e "top-K" -e "批次上限" -e "subagent 失败" -e "串行" plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md
```
Expected: 输出 ≥5（五个关键规则关键词均出现）。

- [ ] **Step 3: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md
git commit -m "Add fan-out and parallel failure rules to chain-alpha-pipeline methodology

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: 重写 SKILL.md（能力探测 + fan-out 工作流）

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`（整体重写）

- [ ] **Step 1: 用以下完整内容覆盖 SKILL.md**

````markdown
---
name: chain-alpha-pipeline
description: "chain-alpha 产业链选股工作流编排：主 agent 跨步串行调度三步（chain-alpha-mismatch-discovery 产业链全景+供需错位环节、chain-alpha-monopoly-screen 拆环节找垄断、chain-alpha-verification 验证定仓位），步内 fan-out 到 subagent 并行（Claude Code），不支持时降级为会话内串行（Codex），强制漏斗纪律并生成中文汇总报告。适用于：(1) 用户从一个大主题出发想走完整的'拆产业链 -> 找关键环节 -> 找可投公司'流程, (2) 用户说'用 chain-alpha 分析 <主题>'。输出保存至 ./output/chain-alpha-pipeline/。"
---

# chain-alpha 产业链选股工作流

## Overview

本 skill 编排 chain-alpha 三步工作流：拆解产业链 -> 分析关键环节 -> 找到可投资公司。它不引入新的分析逻辑，只负责调度三个步骤 skill、传递交接数据、执行漏斗纪律和生成最终汇总。

调度形态：主 agent 跨步串行；步内对可拆分单元 fan-out 到 subagent 并行（第二步按环节、第三步按公司）。不支持 subagent 派发的 agent 会话降级为会话内串行，产出格式一致。

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
- 支持（如 Claude Code）：并行模式。
- 不支持（如 Codex）：串行降级模式，行为与产出格式等价。

### Step 1: chain-alpha-mismatch-discovery（主 agent 自己做）
- 输入：大主题。
- 产出：产业链全景列表 + 2-4 个错位环节（含错位强度评分）。
- 漏斗规则：最多 4 个环节进入下一步；硬门槛未过的环节不得放行。
- 全景不可分，不 fan-out。

### Step 2: chain-alpha-monopoly-screen（步内 fan-out）
- 并行模式：每个错位环节派一个 subagent（按 `subagent-prompts.md` 的 Step 2 模板），N≤4，单波 ≤6。
- 串行模式：在当前会话内对每个环节顺序执行。
- 每个工作单元产出：该环节 ≤10 家候选（25 分排序），标注是否 US-listed/ADR。
- 主 agent 收齐各环节交接字段，汇总候选池，按 25 分排序，挑美股/ADR 候选 top-K（默认 6）进入 Step 3。

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
Step 2 / Step 3 的 subagent 派发模板与交接字段契约，含串行降级说明。

### references/report-template.md
最终汇总报告模板：主题、全景摘要、错位环节、候选漏斗、Top 2-3 深挖卡、金池子/通过清单、跟踪计划。
````

- [ ] **Step 2: 验证 frontmatter 合法且 name 不变**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
t = pathlib.Path('plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md').read_text(encoding='utf-8')
fm = yaml.safe_load(t.split('---')[1])
assert fm['name'] == 'chain-alpha-pipeline', fm['name']
assert 'subagent' in fm['description'] and 'Codex' in fm['description']
print('OK:', fm['name'])"
```
Expected: `OK: chain-alpha-pipeline`

- [ ] **Step 3: 验证平台中立措辞**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && grep -c -e "Codex" -e "Claude Code" -e "agent 会话" plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md
```
Expected: 输出 ≥3（两平台均被并列提及、且有"agent 会话"中性措辞）。

- [ ] **Step 4: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md
git commit -m "Rewrite chain-alpha-pipeline workflow for subagent fan-out with serial fallback

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: 更新文档描述（AGENTS.md + README.md）

**Files:**
- Modify: `AGENTS.md`（Active packaged skills 列表中 chain-alpha-pipeline 行）
- Modify: `README.md`（Skill List 表中 chain-alpha-pipeline 行）

- [ ] **Step 1: 更新 AGENTS.md 的 chain-alpha-pipeline 描述**

把这一行：

```markdown
- `chain-alpha-pipeline` - chain-alpha orchestration: runs the three steps in-session with funnel discipline (2-4 links, <=10 candidates per link, 2-3 deep dives) and a Chinese summary report
```

替换为：

```markdown
- `chain-alpha-pipeline` - chain-alpha orchestration: main agent runs the three steps serially with in-step subagent fan-out (parallel on Claude Code, serial fallback on Codex), enforces funnel discipline (2-4 links, <=10 candidates per link, 2-3 deep dives), and writes a Chinese summary report
```

- [ ] **Step 2: 更新 README.md 的 chain-alpha-pipeline 行**

把这一行：

```markdown
| `chain-alpha-pipeline` | In-session orchestration of the three chain-alpha steps with funnel discipline. | You want the full theme-to-company workflow in one run. |
```

替换为：

```markdown
| `chain-alpha-pipeline` | Orchestrates the three chain-alpha steps with in-step subagent fan-out (parallel on Claude Code, serial fallback on Codex) and funnel discipline. | You want the full theme-to-company workflow in one run. |
```

- [ ] **Step 3: 确认替换生效**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && grep -c "subagent fan-out" AGENTS.md README.md
```
Expected:
```
AGENTS.md:1
README.md:1
```

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md README.md
git commit -m "Document chain-alpha-pipeline subagent fan-out in AGENTS.md and README

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 最终验证

- [ ] **Step 1: 三个步骤 skill 文件零改动**

重构起点是 `694155e`（chain-alpha 四 skill 初版的最后一个提交）。本次重构只允许动 `chain-alpha-pipeline`，三个步骤 skill 自该点起不得被触碰。

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && git diff --name-only 694155e..HEAD -- \
  plugins/invest-flow/skills/chain-alpha-mismatch-discovery \
  plugins/invest-flow/skills/chain-alpha-monopoly-screen \
  plugins/invest-flow/skills/chain-alpha-verification
```
Expected: 空输出（694155e 之后三个步骤 skill 未被改动；若有输出说明误改，需还原）。

- [ ] **Step 2: chain-alpha-pipeline 包结构完整且 frontmatter 合法**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
base = pathlib.Path('plugins/invest-flow/skills/chain-alpha-pipeline')
fm = yaml.safe_load((base/'SKILL.md').read_text(encoding='utf-8').split('---')[1])
assert fm['name'] == 'chain-alpha-pipeline', fm['name']
for f in ['references/methodology.md','references/report-template.md','references/subagent-prompts.md']:
    assert (base/f).exists(), f
print('OK: pipeline package complete')"
```
Expected: `OK: pipeline package complete`

- [ ] **Step 3: 既有单测不受影响**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -m unittest \
  plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py \
  plugins/invest-flow/skills/company-buyability-score/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py 2>&1 | tail -3
```
Expected: 全部 `OK`（与本次改动无关，确认未误伤）。

- [ ] **Step 4: 对照 spec 复核**

逐项确认：fan-out 粒度（Step1 主 agent / Step2 按环节 / Step3 按公司）、双模式降级、交接字段契约（Step2 含"是否美股"、Step3 含档位/仓位）、top-K=6、批次上限 6、并行失败处理三条、三个步骤 skill 零改动、未 bump 版本。

- [ ] **Step 5: 功能性冒烟（人工，可选）**

在 Claude Code 新会话中跑一次完整 `使用 invest-flow:chain-alpha-pipeline 分析 <某主题>`，确认：Step 2/3 确实并行派发 subagent、交接字段完整、某 subagent 失败时按降级规则标注。Codex 环境确认串行路径产出格式一致。
