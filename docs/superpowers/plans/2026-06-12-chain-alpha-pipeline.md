# chain-alpha 产业链选股工作流实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 `docs/superpowers/specs/2026-06-12-chain-alpha-pipeline-design.md` 新增四个 `chain-alpha-` 前缀的投资 skill（三个步骤 skill + 一个编排 skill），并同步更新仓库文档与 plugin 元数据。

**Architecture:** 每个 skill 为纯 Markdown 包（`SKILL.md` + `references/methodology.md` + `references/report-template.md`），无 Python 脚本。编排 skill 在当前 agent 会话内串联三个步骤 skill 并强制漏斗纪律。硬门槛一票否决先于评分执行；评分决定环节排序、候选排序和公司四档分级（剔除/待验证/通过/金池子）。

**Tech Stack:** Markdown skill 包、YAML frontmatter、现有 invest-flow plugin 结构（Codex + Claude Code 双平台）。

**Worker notes:**
- 全部新文件内容已完整写在本计划中，按原文写入即可，不要自行增删硬门槛数字。
- 中文输出、金融/技术术语保留 English，是仓库的既有约定。
- 每个 task 结束都有验证命令和 commit；commit message 末尾加 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。
- `output/` 目录不被 git 跟踪，skill 运行时自建，不需要创建。

---

### Task 1: chain-alpha-mismatch-discovery（第一步：找供需错位环节）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md`
- Create: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/methodology.md`
- Create: `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/references/report-template.md`

- [ ] **Step 1: 写入 SKILL.md**

````markdown
---
name: chain-alpha-mismatch-discovery
description: "chain-alpha 工作流第一步：从用户给定的大主题出发，先输出完整产业链全景列表，再识别需求增量大、供给跟不上的供需错位环节。适用于：(1) 用户要求拆解某主题的完整产业链并找供需错位/瓶颈环节, (2) chain-alpha-pipeline 的第一步, (3) 单独验证某条产业链是否存在真实的供需缺口。输出 2-4 个错位环节及错位强度评分，保存至 ./output/chain-alpha-mismatch-discovery/。"
---

# chain-alpha 供需错位环节发现

## Overview

本 skill 是 chain-alpha 工作流的第一步，从一个大主题出发回答两个问题：这条产业链长什么样（全景），哪些环节存在供需错位（需求增量大、供给跟不上）。

核心原则：先全景、后错位。不允许跳过全景直接给错位结论。即使最后没找到错位环节，全景列表本身也是有效产出。

默认输出目录：`./output/chain-alpha-mismatch-discovery/`

## Trigger

- `使用 invest-flow:chain-alpha-mismatch-discovery 分析 AI 数据中心电力`
- `拆解 <主题> 的完整产业链并找供需错位环节`
- 作为 `chain-alpha-pipeline` 的第一步被调用

输入必须是用户给定的大主题（如"AI 数据中心电力""机器人执行器""先进封装"）。本 skill 不做全市场自动扫描；用户未给主题时必须先要求用户提供。

## Workflow

### 1) 明确主题边界
- 提取主题、地区、时间窗口。
- 用户未指定时，默认全球视角（含中国大陆及日韩台欧），时间窗口 6-24 个月。

### 2) 收集证据
- 涉及需求量、产能、价格、交期、订单、财务、扩产计划时，必须查最新公开来源。
- 优先使用公司财报、Investor Relations、earnings call、交易所公告、行业协会和权威数据。
- 区分 `事实 / 推断 / 假设`；关键数字标注来源和日期；不可得标注"不确定"或"数据暂缺"，不得编造。

### 3) 第一段：产业链全景（不得跳过）
读取 `references/methodology.md`，从终端需求倒推，把整个产业链按 上游 / 中游 / 下游 / 生态支撑 完整列出。

- 每个环节用列表呈现，固定字段：环节名称、作用、需求来源、供给弹性、代表公司、价值池大小。
- 全景必须覆盖整条链，不允许只列感兴趣的部分。
- 全景列表是报告的独立章节。

### 4) 第二段：错位环节识别
在全景列表基础上逐环节做供需错位判断。每个候选错位环节必须回答并附证据：

- **需求为什么增加**：增量来源、预算来源、单位用量是否非线性。
- **供给为什么跟不上**：扩产周期 / 技术壁垒 / 公司不愿扩产（资本纪律）/ 认证周期，至少落实一项。

**硬门槛（一票否决）**：必须同时具备需求增量证据 + 供给约束实证（价格上涨、交期拉长、订单积压、产能利用率至少一项），否则只能标记"高景气，非错位"，不得进入第二步。

### 5) 错位强度评分
对通过硬门槛的环节按 0-5 逐项打分，满分 20：

| 维度 | 分值 |
|---|---|
| 需求增量确定性 | 0-5 |
| 单位用量弹性 | 0-5 |
| 供给约束强度 | 0-5 |
| 证据强度（实证数量与质量） | 0-5 |

得分最高的 2-4 个环节进入第二步（`chain-alpha-monopoly-screen`），其余进入观察池。

### 6) 输出报告
- 使用 `references/report-template.md` 输出中文 Markdown 报告。
- 保存至 `./output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-{主题}-{YYYY-MM-DD}.md`。
- 文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 报告必须包含固定作者字段：`InvestmentFlow`。

## Quality Rules

- 中文输出；金融、技术术语可保留 English。
- 不允许跳过产业链全景直接给错位结论。
- 全景列表必须覆盖整条链，每个环节字段齐全。
- 不允许把"大需求"直接等同于"错位"；没有供给约束实证只能标"高景气，非错位"。
- 公司格局必须含中国大陆及日韩台欧供应商。
- 每个错位环节必须标注其在全景列表中的位置。

## Resources

### references/methodology.md
全景列表字段定义、错位判断证据标准、错位强度评分细则。

### references/report-template.md
固定中文 Markdown 报告模板：主题边界、产业链全景列表、错位环节卡片、评分汇总、观察池、数据来源。
````

- [ ] **Step 2: 写入 references/methodology.md**

````markdown
# chain-alpha-mismatch-discovery 方法论

## 1. 产业链全景列表

从终端需求倒推，按四段组织：上游（材料/设备/部件）、中游（制造/集成）、下游（产品/服务/终端客户）、生态支撑（软件/标准/运维/基础设施）。

每个环节必须填齐六个字段：

| 字段 | 说明 |
|---|---|
| 环节名称 | 可独立影响产能、成本、交期或利润分配的最小一级颗粒度 |
| 作用 | 该环节在链条中解决什么问题 |
| 需求来源 | 需求由哪个下游环节或终端预算驱动 |
| 供给弹性 | 高（6 个月内可扩）/ 中（6-18 个月）/ 低（>18 个月或受技术/认证限制） |
| 代表公司 | 全球代表公司，必须含中国大陆及日韩台欧供应商（如适用） |
| 价值池大小 | 该环节年收入规模量级估计，标注来源或"推断" |

完整性检查：沿着"终端产品由哪些子系统构成、每个子系统需要什么材料/设备/工艺"自问，直到无新环节出现。

## 2. 供需错位判断

错位 = 需求增量大 + 供给跟不上，两侧都要有证据。

### 需求侧（为什么需求增加）
- 增量来源：新应用、渗透率提升、单位用量提升、替换周期缩短，明确属于哪一类。
- 预算来源：谁在花钱，预算是否已落地（资本开支指引、订单、招标）。
- 单位用量弹性：终端每增长 1 单位，该环节用量增长多少；非线性增长（>1 倍）是强信号。

### 供给侧（为什么供给跟不上），至少落实一项并给出证据
- 扩产周期长：新产能从决策到量产 >18 个月（厂房、设备交期、爬坡）。
- 技术壁垒：良率、专利、工艺 know-how 限制新进入者。
- 公司不愿扩产：寡头资本纪律、上一轮过剩记忆、客户不签长约。
- 认证周期：客户验证 6-24 个月，切换供应商成本高。

### 硬门槛（一票否决）
供给约束实证至少一项：价格上涨、交期拉长、订单积压（backlog 增长）、产能利用率高位。只有逻辑推演、没有任何一项实证的环节，标记"高景气，非错位"。

## 3. 错位强度评分（满分 20）

| 维度 | 5 分标准 | 0 分标准 |
|---|---|---|
| 需求增量确定性 | 预算已落地、多客户验证 | 仅叙事，无预算证据 |
| 单位用量弹性 | 单位用量非线性增长且有数据 | 用量随终端线性甚至下降 |
| 供给约束强度 | 扩产 >18 个月且有技术/认证壁垒叠加 | 6 个月内可扩产 |
| 证据强度 | ≥3 项实证（价格/交期/订单/利用率） | 仅 1 项实证 |

取分最高的 2-4 个环节进入第二步；4-11 分进入观察池并写明缺什么证据；硬门槛未过的不评分。
````

- [ ] **Step 3: 写入 references/report-template.md**

````markdown
# chain-alpha 供需错位环节发现报告：{主题}

- 日期：{YYYY-MM-DD}
- 作者：InvestmentFlow
- 主题边界：{地区 / 时间窗口 / 分析目的}

## 一、一句话结论

{是否存在错位环节，最强的环节是什么，置信度}

## 二、产业链全景列表

### 上游
| 环节名称 | 作用 | 需求来源 | 供给弹性 | 代表公司 | 价值池大小 |
|---|---|---|---|---|---|

### 中游
（同上表头）

### 下游
（同上表头）

### 生态支撑
（同上表头）

## 三、错位环节卡片（每个环节一张）

### 环节：{名称}（位于全景列表 {上游/中游/下游} 第 {N} 项）

**需求为什么增加**
- 增量来源 / 预算来源 / 单位用量弹性：{证据 + 来源 + 日期}

**供给为什么跟不上**
- {扩产周期 / 技术壁垒 / 资本纪律 / 认证周期}：{证据 + 来源 + 日期}

**供给约束实证**（硬门槛）
- {价格 / 交期 / 订单 / 产能利用率，至少一项}

**错位强度评分**
| 需求增量确定性 | 单位用量弹性 | 供给约束强度 | 证据强度 | 总分 |
|---|---|---|---|---|

**事实 / 推断 / 假设区分**：{列出关键判断的证据等级}

## 四、评分汇总与第二步交接

| 环节 | 总分 | 处置（进入第二步 / 观察池 / 高景气非错位） |
|---|---|---|

## 五、观察池（缺什么证据可升级）

## 六、数据来源

| 数据 | 来源 | 日期 | 证据等级 |
|---|---|---|---|
````

- [ ] **Step 4: 验证 frontmatter 可解析**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
t = pathlib.Path('plugins/invest-flow/skills/chain-alpha-mismatch-discovery/SKILL.md').read_text(encoding='utf-8')
fm = yaml.safe_load(t.split('---')[1])
assert fm['name'] == 'chain-alpha-mismatch-discovery', fm['name']
assert len(fm['description']) > 50
print('OK:', fm['name'])"
```
Expected: `OK: chain-alpha-mismatch-discovery`

- [ ] **Step 5: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-mismatch-discovery
git commit -m "Add chain-alpha-mismatch-discovery skill

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: chain-alpha-monopoly-screen（第二步：拆环节找垄断）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md`
- Create: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/methodology.md`
- Create: `plugins/invest-flow/skills/chain-alpha-monopoly-screen/references/report-template.md`

- [ ] **Step 1: 写入 SKILL.md**

````markdown
---
name: chain-alpha-monopoly-screen
description: "chain-alpha 工作流第二步：把单个供需错位环节拆成上中下游子环节，列出全球公司格局（含中国大陆及日韩台欧），用 CR3>50%/寡头证据、毛利率与壁垒、环节收入占比三道硬门槛筛选，再按 25 分候选评分排序，每环节输出 ≤10 家候选公司。适用于：(1) 已确认某环节供需错位、要找其中的垄断公司, (2) chain-alpha-pipeline 的第二步。输出保存至 ./output/chain-alpha-monopoly-screen/。"
---

# chain-alpha 垄断环节筛选

## Overview

本 skill 是 chain-alpha 工作流的第二步：找壁垒、找垄断、排除低端竞争。输入一个供需错位环节（通常来自 `chain-alpha-mismatch-discovery`），输出该环节内 ≤10 家通过硬门槛的候选公司，并标注哪些是 US-listed/ADR。

默认输出目录：`./output/chain-alpha-monopoly-screen/`

## Trigger

- `使用 invest-flow:chain-alpha-monopoly-screen 筛选 <环节>`
- 作为 `chain-alpha-pipeline` 的第二步被调用
- 用户已有明确的瓶颈环节、想找其中的垄断公司

## Workflow

### 1) 明确输入环节
- 输入为单个错位环节（如"HBM 用 TC bonder""数据中心干式变压器"）。
- 多个环节时每个环节单独运行、单独出报告。

### 2) 拆子环节
- 把该环节拆成上中下游子环节（材料、设备、制造、集成等）。
- 子环节颗粒度：能独立影响产能、良率、成本、交期或认证的最小单位。

### 3) 列全球公司格局
- 每个子环节列出全球公司格局，**必须含中国大陆及日韩台欧供应商**——中国是全球供应链不可缺少的一环，缺了 CR3 判断失真。
- 每家公司标注：总部/上市地、是否 US-listed/ADR、在该子环节的产品和份额估计。

### 4) 硬门槛（一票否决，先于评分执行）
读取 `references/methodology.md`：

- **集中度**：CR3 > 50%，或有明确证据的寡头/双寡头格局。精确市占率不可得时允许推断，必须标注证据等级（事实/推断/假设）；纯假设的 CR3 不算通过。
- **排除低端竞争**：毛利率持续低于 25% 且无技术/认证壁垒的公司直接剔除。
- **占比初筛**：环节收入占公司收入比重明显 <20% 的不进入第三步。

### 5) 候选评分（0-5 逐项，满分 25）

| 维度 | 分值 |
|---|---|
| 集中度/份额地位（是否 CR3 头部、份额趋势） | 0-5 |
| 技术/认证壁垒 | 0-5 |
| 毛利率水平与趋势 | 0-5 |
| 环节收入占比初值 | 0-5 |
| 供给约束受益度（涨价/订单/交期向该公司传导的证据） | 0-5 |

按总分排序，每环节取前 ≤10 家。

### 6) 输出报告
- 使用 `references/report-template.md` 输出中文 Markdown 报告。
- 标注哪些候选是 US-listed/ADR（仅这些进第三步 `chain-alpha-verification`）；非美股垄断者（含中国大陆/港股/A股公司）作为产业格局背景保留在报告中。
- 保存至 `./output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节}-{YYYY-MM-DD}.md`。
- 文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 报告必须包含固定作者字段：`InvestmentFlow`。

## Quality Rules

- 中文输出；金融、技术术语可保留 English。
- 公司必须绑定到具体子环节、产品或材料，不允许只给公司名单。
- CR3 判断必须基于全球格局（含中国大陆及日韩台欧），并标注证据等级。
- 硬门槛先于评分；评分不能救回未过硬门槛的公司。
- 占比、份额、毛利率等关键数字必须标注来源和日期；不可得标注"推断"或"数据暂缺"。

## Resources

### references/methodology.md
子环节拆分标准、CR3 证据等级规则、毛利率/壁垒排除规则、占比初筛口径、25 分候选评分细则。

### references/report-template.md
固定中文 Markdown 报告模板：环节定义、子环节拆解、全球格局表、硬门槛筛选记录、候选评分表、US-investable 候选清单、数据来源。
````

- [ ] **Step 2: 写入 references/methodology.md**

````markdown
# chain-alpha-monopoly-screen 方法论

## 1. 子环节拆分

把输入环节拆成上中下游子环节：关键材料、关键设备、制造/工艺、集成/模组。颗粒度标准：该子环节能否独立影响产能、良率、成本、交期或客户认证；能则单独拆出。

## 2. 集中度门槛（CR3 > 50% 或寡头证据）

- 首选：权威行业数据或公司披露的市占率，直接计算 CR3。
- 次选（允许推断）：通过头部公司收入规模对比、客户披露的供应商名单、产能数据推断格局，结论标注"推断"。
- 寡头/双寡头格局的替代证据：客户公开表示供应商只有 2-3 家可选、认证名单极短、头部公司有持续定价权（连续提价且份额不掉）。
- 纯假设（无任何上述证据）的 CR3 不算通过。
- 证据等级三档：事实（有数源）/ 推断（有间接证据）/ 假设（仅逻辑），每个 CR3 结论必须标注。

## 3. 排除低端竞争

剔除条件（同时满足）：毛利率持续低于 25%（近 4 个季度或近 2 个财年），且无技术/认证壁垒（新进入者 12 个月内可达到同等供货能力）。
只满足其一的保留并扣分。低毛利但有强认证壁垒（如车规、客户独家认证）不剔除。

## 4. 占比初筛

环节收入占公司收入比重明显 <20% 的不进入第三步。"明显"指即使按有利口径推断也到不了 20%；处于 15-25% 模糊区间且披露口径不清的，标注"待第三步核实"放行。

## 5. 候选评分细则（满分 25）

| 维度 | 5 分 | 3 分 | 0-1 分 |
|---|---|---|---|
| 集中度/份额地位 | CR3 第一且份额上升 | CR3 内但份额持平 | CR3 外 |
| 技术/认证壁垒 | 工艺/专利+认证双壁垒，替代者 >24 个月 | 单一壁垒 | 无壁垒 |
| 毛利率水平与趋势 | ≥40% 且上升 | 25-40% 平稳 | <25% 或下行 |
| 环节收入占比初值 | ≥40% | 20-40% | <20%（应已被初筛剔除） |
| 供给约束受益度 | 已有涨价/加单/交期收益落进财报或指引 | 有订单信号未入财报 | 无传导证据 |

按总分排序取前 ≤10 家。同分时优先 US-listed/ADR。
````

- [ ] **Step 3: 写入 references/report-template.md**

````markdown
# chain-alpha 垄断环节筛选报告：{环节}

- 日期：{YYYY-MM-DD}
- 作者：InvestmentFlow
- 输入环节：{名称}（来源：{chain-alpha-mismatch-discovery 报告路径或用户指定}）

## 一、一句话结论

{该环节是否存在可投资的垄断格局，最强候选是谁}

## 二、子环节拆解

| 子环节 | 类型（材料/设备/制造/集成） | 作用 | 对产能/良率/成本/交期的影响 |
|---|---|---|---|

## 三、全球公司格局（含中国大陆及日韩台欧）

### 子环节：{名称}
| 公司 | 总部/上市地 | US-listed/ADR | 产品 | 份额估计 | 证据等级 |
|---|---|---|---|---|---|

CR3 估计：{数值或区间}，证据等级：{事实/推断/假设}，依据：{来源 + 日期}

## 四、硬门槛筛选记录

| 公司 | 集中度门槛 | 毛利/壁垒门槛 | 占比初筛 | 结果（存活/剔除及原因） |
|---|---|---|---|---|

## 五、候选评分（满分 25）

| 公司 | 份额地位 | 技术壁垒 | 毛利率 | 占比初值 | 受益度 | 总分 |
|---|---|---|---|---|---|---|

## 六、进入第三步的 US-listed/ADR 候选

| 公司 | Ticker | 子环节 | 总分 | 待第三步核实事项 |
|---|---|---|---|---|

非美股垄断者（产业格局背景，不进第三步）：{清单}

## 七、数据来源

| 数据 | 来源 | 日期 | 证据等级 |
|---|---|---|---|
````

- [ ] **Step 4: 验证 frontmatter**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
t = pathlib.Path('plugins/invest-flow/skills/chain-alpha-monopoly-screen/SKILL.md').read_text(encoding='utf-8')
fm = yaml.safe_load(t.split('---')[1])
assert fm['name'] == 'chain-alpha-monopoly-screen', fm['name']
print('OK:', fm['name'])"
```
Expected: `OK: chain-alpha-monopoly-screen`

- [ ] **Step 5: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-monopoly-screen
git commit -m "Add chain-alpha-monopoly-screen skill

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: chain-alpha-verification（第三步：验证定仓位）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`
- Create: `plugins/invest-flow/skills/chain-alpha-verification/references/methodology.md`
- Create: `plugins/invest-flow/skills/chain-alpha-verification/references/report-template.md`

- [ ] **Step 1: 写入 SKILL.md**

````markdown
---
name: chain-alpha-verification
description: "chain-alpha 工作流第三步：对 US-listed/ADR 候选公司做最终验证——环节收入占比双轨硬门槛（≥40% 纯正 / 20-40% 增量贡献测试 / <20% 剔除）、100 分模型四档分级（金池子/通过/待验证/剔除）、最大回撤推断与风险预算法仓位上限。适用于：(1) 验证产业链筛出的候选公司是否可投并定仓位, (2) chain-alpha-pipeline 的第三步。输出保存至 ./output/chain-alpha-verification/。"
---

# chain-alpha 公司验证与仓位

## Overview

本 skill 是 chain-alpha 工作流的第三步：验证候选公司，给出四档结论和仓位上限。输入为 US-listed equities/ADRs 候选（通常来自 `chain-alpha-monopoly-screen`）。

默认输出目录：`./output/chain-alpha-verification/`

## Trigger

- `使用 invest-flow:chain-alpha-verification 验证 <TICKER 或候选清单>`
- 作为 `chain-alpha-pipeline` 的第三步被调用

非美股公司不做验证和仓位建议；用户提供非美股标的时说明范围限制并仅做定性参考。

## Workflow

### 1) 收集证据
- 季度收入、segment 拆分、毛利率：10-K/10-Q、earnings release、IR 材料。
- 估值与股价数据：yfinance / market-data-router。
- 关键数字标注来源和日期；区分 事实 / 推断 / 假设。

### 2) 硬门槛（一票否决，不进入评分）
- **环节收入占比 <20%：直接剔除。**
- **20-40% 弹性标的**：必须通过增量贡献测试——该环节贡献公司未来 1-2 年收入增量的 ≥50%，或占比有明确上升轨迹和管理层指引；不通过的最高只能归入"待验证"档。
- 占比允许推断值 + 置信度标注；公司 segment 披露口径不拆分时必须明确说明。

### 3) 100 分模型评分
读取 `references/methodology.md` 逐项评分：

| 维度 | 权重 |
|---|---:|
| 产业位置（高端定位、份额趋势、客户质量） | 20 |
| 环节收入占比与增量贡献 | 25 |
| 业绩验证（季度收入同比 vs 同环节可比中位数） | 20 |
| 估值与透支度 | 20 |
| 格局延续性（供给约束与垄断格局 6-24 个月可持续性） | 15 |

负分项（0 到 -15，计入总分）：客户集中砍单风险、技术替代风险、扩产过剩风险。

### 4) 四档分级

| 总分 | 档位 | 处置 |
|---|---|---|
| ≥80 | 金池子 | 重点跟踪，全额风险预算法仓位 |
| 65-79 | 通过 | 可建仓，仓位上限 × 0.5 |
| 50-64 | 待验证 | 观察池，列出补齐哪些证据可升档，不给仓位 |
| <50 | 剔除 | 除非出现新的强催化剂 |

### 5) 最大回撤推断与仓位
- 最大回撤取三者最大值：历史回撤、估值压缩情景、业绩 miss 情景。
- 仓位上限 = 单笔风险预算（默认组合的 2%，可参数化）÷ 预估最大回撤。
- 档位"通过"再 × 0.5；弹性标的（占比 20-40%）再 × 0.5（可叠乘）。
- 例：预估回撤 40%，风险预算 2%，仓位上限 5%；档位"通过"则 2.5%。

### 6) 输出验证卡
- 使用 `references/report-template.md`，每家公司一张验证卡（评分明细、档位、仓位上限、反证条件）。
- 单公司保存至 `./output/chain-alpha-verification/chain-alpha-verification-{TICKER}-{YYYY-MM-DD}.md`；多公司汇总为 `chain-alpha-verification-{环节}-{YYYY-MM-DD}.md`。
- 文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 报告必须包含固定作者字段：`InvestmentFlow`。

**兜底规则**：若某环节筛选后无公司进入"通过"及以上档位，报告列出"因占比或总分不足被剔除但格局最好的公司"作为参考，不给仓位建议。

## Quality Rules

- 中文输出；金融术语可保留 English。
- 硬门槛先于评分；评分不能救回不过硬门槛的公司。
- 占比为推断值时必须标注置信度和推断依据。
- 跑输同环节可比中位数的增速必须解释原因，不得回避。
- 估值透支判断必须同时看当前估值和远期估值。
- 输出是研究与跟踪优先级，不是自动交易指令。

## Resources

### references/methodology.md
双轨占比门槛与增量贡献测试细则、100 分模型逐维度评分标准、负分项标准、回撤三情景估计方法、仓位公式。

### references/report-template.md
公司验证卡模板：硬门槛记录、评分明细表、档位、回撤推断、仓位计算、反证条件、跟踪指标。
````

- [ ] **Step 2: 写入 references/methodology.md**

````markdown
# chain-alpha-verification 方法论

## 1. 环节收入占比（双轨硬门槛）

- 占比口径：目标环节相关收入 ÷ 公司总收入，用最近 4 个季度或最近财年。
- segment 不拆分时的推断方法：产品线收入披露、管理层电话会表述、客户/订单规模反推；结果标注置信度（高/中/低）和推断依据。
- **≥40%**：纯正标的，进入评分，全额仓位规则。
- **20-40%**：弹性标的，必须通过增量贡献测试，且仓位上限 × 0.5。
- **<20%**：直接剔除，不评分。

增量贡献测试（满足其一）：
1. 该环节贡献公司未来 1-2 年收入增量的 ≥50%（用指引、订单、产能爬坡估算）。
2. 占比有明确上升轨迹（连续 ≥2 个季度提升）且管理层指引继续提升。

不通过的最高归入"待验证"档。

## 2. 100 分模型评分标准

### 产业位置（20 分）
- 16-20：环节内高端产品主力供应商，份额第一或上升，客户为头部厂商。
- 10-15：CR3 内但份额持平，客户质量中等。
- 0-9：中低端产品为主，份额下滑，客户分散且议价弱。

### 环节收入占比与增量贡献（25 分）
- 20-25：占比 ≥40% 且仍在上升，或 20-40% 但增量贡献 ≥70%。
- 12-19：占比 ≥40% 平稳，或 20-40% 且通过增量贡献测试。
- 0-11：20-40% 且增量贡献测试勉强通过、证据置信度低。

### 业绩验证（20 分）
- 16-20：季度收入同比 ≥ 同环节可比中位数，且连续 ≥2 个季度。可比公司取第二步候选清单中同子环节的公司，不足 3 家时扩展至同环节全球公司。
- 10-15：与中位数相当，或单季跑赢。
- 0-9：跑输中位数；必须写明原因（公司问题还是口径问题）。

### 估值与透支度（20 分）
- 16-20：当前与远期估值（NTM P/E 或 EV/S）低于增速合理水平，透支度低。
- 10-15：估值与增速匹配，无明显透支。
- 0-9：远期估值已计入 2 年以上的高增长（透支），或增速下行而估值未调整。

### 格局延续性（15 分）
- 12-15：第二步确认的供给约束与垄断格局在 6-24 个月内有持续证据（扩产慢、认证壁垒未破）。
- 6-11：格局稳定但有新产能/新进入者在路上。
- 0-5：供给缺口正在闭合或技术路线面临替代。

### 负分项（0 到 -15，计入总分）
- 客户集中砍单风险：单一客户 >40% 收入且该客户有自研/二供动作，-5 起。
- 技术替代风险：替代路线已有头部客户验证，-5 起。
- 扩产过剩风险：行业在建产能 / 当前需求 >1.5 倍，-5 起。

## 3. 最大回撤推断（三情景取最大）

1. 历史回撤：过去 5 年（不足则上市以来）最大回撤。
2. 估值压缩情景：估值回到历史中位数或可比公司中位数对应的跌幅。
3. 业绩 miss 情景：收入增速降到行业中位数、毛利率回落 3-5pct 后，按当前估值体系推算的跌幅。

## 4. 仓位公式

仓位上限 = 单笔风险预算（默认组合的 2%，可参数化）÷ 预估最大回撤
- 档位"金池子"：全额。
- 档位"通过"：× 0.5。
- 弹性标的（占比 20-40%）：再 × 0.5，可与档位折扣叠乘。
- "待验证"与"剔除"不给仓位。
````

- [ ] **Step 3: 写入 references/report-template.md**

````markdown
# chain-alpha 公司验证卡：{公司} ({TICKER})

- 日期：{YYYY-MM-DD}
- 作者：InvestmentFlow
- 所属环节：{环节}（来源：{chain-alpha-monopoly-screen 报告路径或用户指定}）

## 一、结论

- 档位：{金池子 / 通过 / 待验证 / 剔除}
- 总分：{N}/100（含负分项 {-N}）
- 仓位上限：{N}%（计算见第六节）或 不适用

## 二、硬门槛记录

| 项目 | 数值 | 置信度 | 依据 | 结果 |
|---|---|---|---|---|
| 环节收入占比 | {N}%（{事实/推断}） | {高/中/低} | {来源+日期} | {纯正/弹性/剔除} |
| 增量贡献测试（弹性标的适用） | {通过/不通过} | | {依据} | |

## 三、评分明细

| 维度 | 得分 | 满分 | 评分依据 |
|---|---|---|---|
| 产业位置 | | 20 | |
| 环节收入占比与增量贡献 | | 25 | |
| 业绩验证 | | 20 | 同环节可比中位数 {N}% vs 本公司 {N}% |
| 估值与透支度 | | 20 | |
| 格局延续性 | | 15 | |
| 负分项 | | 0 到 -15 | |
| **总分** | | 100 | |

## 四、业绩与估值细节

- 近 4 个季度收入同比：{列出}
- 同环节可比公司及中位数：{清单 + 中位数}
- 当前估值 / 远期估值：{NTM P/E、EV/S 等}
- 透支度判断：{结论 + 依据}

## 五、最大回撤推断

| 情景 | 推算回撤 | 依据 |
|---|---|---|
| 历史回撤 | | |
| 估值压缩 | | |
| 业绩 miss | | |
| **取最大** | | |

## 六、仓位计算

仓位上限 = {风险预算}% ÷ {最大回撤}% = {N}%
{× 0.5 档位折扣（如适用）} {× 0.5 弹性标的折扣（如适用）} = 最终 {N}%

## 七、反证条件（出现即降档或剔除）

1. {条件}
2. {条件}

## 八、跟踪指标

| 指标 | 当前值 | 跟踪频率 | 触发动作 |
|---|---|---|---|

## 九、数据来源

| 数据 | 来源 | 日期 | 证据等级 |
|---|---|---|---|
````

- [ ] **Step 4: 验证 frontmatter**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
t = pathlib.Path('plugins/invest-flow/skills/chain-alpha-verification/SKILL.md').read_text(encoding='utf-8')
fm = yaml.safe_load(t.split('---')[1])
assert fm['name'] == 'chain-alpha-verification', fm['name']
print('OK:', fm['name'])"
```
Expected: `OK: chain-alpha-verification`

- [ ] **Step 5: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-verification
git commit -m "Add chain-alpha-verification skill

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: chain-alpha-pipeline（编排）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`
- Create: `plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md`
- Create: `plugins/invest-flow/skills/chain-alpha-pipeline/references/report-template.md`

- [ ] **Step 1: 写入 SKILL.md**

````markdown
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
````

- [ ] **Step 2: 写入 references/methodology.md**

````markdown
# chain-alpha-pipeline 编排方法论

## 1. 漏斗纪律

| 阶段 | 上限 | 不足时 |
|---|---|---|
| Step 1 错位环节 | 2-4 个 | 0 个则终止流程，输出全景列表 + 观察池，说明缺什么证据 |
| Step 2 每环节候选 | ≤10 家 | 0 家则该环节标"格局分散，暂不可投"，列格局最好的公司作背景 |
| Step 3 深挖 | 2-3 家 | 无"通过"及以上档位时触发兜底规则：列出被剔除但格局最好的公司，不给仓位 |

## 2. 步骤间交接数据

Step 1 -> Step 2，每个错位环节传递：环节名称、在全景列表中的位置、错位强度评分、需求/供给证据摘要、供给约束实证清单。

Step 2 -> Step 3，每家候选传递：公司名、Ticker、子环节、候选评分、占比初值与置信度、CR3 证据等级、待核实事项。

Step 3 -> 汇总，每家公司传递：档位、总分、仓位上限、反证条件、跟踪指标。

## 3. 降级处理

- Step 1 全部环节只是"高景气，非错位"：终止，不强行进入 Step 2；报告给出升级触发条件（出现什么实证再重跑）。
- Step 2 候选全为非美股：Step 3 跳过，报告说明该环节的可投资性受限于上市地，列出非美股垄断者供参考。
- 数据缺口（占比/CR3 拿不到）：照常进入下一步但降低置信度标注，不得编造数字。

## 4. 会话成本控制

- 完整 pipeline 建议在单独会话运行，避免上下文耗尽。
- 三步必须顺序执行（后一步输入依赖前一步输出），同一步内多个环节/公司可并行研究。
````

- [ ] **Step 3: 写入 references/report-template.md**

````markdown
# chain-alpha 产业链选股汇总报告：{主题}

- 日期：{YYYY-MM-DD}
- 作者：InvestmentFlow
- 各步骤报告：
  - Step 1: {output/chain-alpha-mismatch-discovery/ 文件路径}
  - Step 2: {output/chain-alpha-monopoly-screen/ 文件路径，每环节一份}
  - Step 3: {output/chain-alpha-verification/ 文件路径}

## 一、一句话结论

{最终金池子/通过的公司，核心逻辑链：错位环节 -> 垄断地位 -> 验证结果}

## 二、产业链全景摘要

{Step 1 全景列表的压缩版：四段各列环节名，标注错位环节}

## 三、错位环节

| 环节 | 错位强度评分 | 需求驱动 | 供给约束 | 实证 |
|---|---|---|---|---|

## 四、候选漏斗

| 阶段 | 数量 | 说明 |
|---|---|---|
| 全景环节 | | |
| 错位环节 | | |
| 硬门槛存活候选 | | |
| US-listed 进入验证 | | |
| 通过及以上档位 | | |

## 五、Top 2-3 深挖卡

### {公司} ({TICKER}) — {金池子/通过}，总分 {N}
- 所属环节与垄断地位：
- 占比与增量贡献：
- 业绩 vs 行业：
- 估值与透支度：
- 仓位上限与计算：
- 反证条件：

## 六、金池子 / 通过 / 待验证清单

| 公司 | Ticker | 档位 | 总分 | 仓位上限 | 关键跟踪指标 |
|---|---|---|---|---|---|

## 七、跟踪计划

| 信号 | 频率 | 触发动作 |
|---|---|---|

## 八、数据来源汇总

{引用各步骤报告的数据来源章节}
````

- [ ] **Step 4: 验证 frontmatter**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
t = pathlib.Path('plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md').read_text(encoding='utf-8')
fm = yaml.safe_load(t.split('---')[1])
assert fm['name'] == 'chain-alpha-pipeline', fm['name']
print('OK:', fm['name'])"
```
Expected: `OK: chain-alpha-pipeline`

- [ ] **Step 5: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-pipeline
git commit -m "Add chain-alpha-pipeline orchestration skill

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 更新 AGENTS.md

**Files:**
- Modify: `AGENTS.md`（三处：结构树、Active packaged skills 列表、Output Conventions）

- [ ] **Step 1: 在结构树中加入四个 skill 目录**

在 `Current Repository Structure` 的 `skills/` 树中，`├── company-profile/` 之前（按现有顺序风格，放在 `ai-infrastructure-sector-discovery/` 之后即可）插入：

```text
│           ├── chain-alpha-mismatch-discovery/
│           ├── chain-alpha-monopoly-screen/
│           ├── chain-alpha-verification/
│           ├── chain-alpha-pipeline/
```

同时在 `output/` 树中 `├── company-profile/` 之前插入：

```text
│   ├── chain-alpha-mismatch-discovery/
│   ├── chain-alpha-monopoly-screen/
│   ├── chain-alpha-verification/
│   ├── chain-alpha-pipeline/
```

- [ ] **Step 2: 在 Active packaged skills 列表加四行**

在 `Skill Layout` 节的 active skills 列表中，`- company-buyability-score` 之前插入：

```markdown
- `chain-alpha-mismatch-discovery` - chain-alpha step 1: full industry-chain panorama list plus supply-demand mismatch link discovery with hard evidence gates and 20-point mismatch scoring
- `chain-alpha-monopoly-screen` - chain-alpha step 2: sub-link breakdown, global landscape including mainland China and JP/KR/TW/EU, CR3/margin/revenue-share hard gates, 25-point candidate scoring
- `chain-alpha-verification` - chain-alpha step 3: dual-track revenue-share gate, 100-point four-tier grading (gold pool/pass/pending/reject), drawdown inference and risk-budget position sizing for US-listed candidates
- `chain-alpha-pipeline` - chain-alpha orchestration: runs the three steps in-session with funnel discipline (2-4 links, <=10 candidates per link, 2-3 deep dives) and a Chinese summary report
```

- [ ] **Step 3: 在 Output Conventions 加四行**

在 `- Company profile:` 行之前插入：

```markdown
- Chain-alpha mismatch discovery: `output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-{主题}-{YYYY-MM-DD}.md`
- Chain-alpha monopoly screen: `output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节}-{YYYY-MM-DD}.md`
- Chain-alpha verification: `output/chain-alpha-verification/chain-alpha-verification-{TICKER或环节}-{YYYY-MM-DD}.md`
- Chain-alpha pipeline summary: `output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`
```

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "Document chain-alpha skills in AGENTS.md

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: 更新 README.md

**Files:**
- Modify: `README.md`（四处：Common tasks 表、Skill List 表、Use Skills In Agent 示例、Output Paths 表）

- [ ] **Step 1: Common tasks 表加一行**

在 README 的 common-tasks 表（约 45-52 行附近）中加：

```markdown
| Find investable companies from an industry chain | Use `chain-alpha-pipeline` for the full mismatch -> monopoly -> verification funnel, or run `chain-alpha-mismatch-discovery` alone first to confirm the mismatch links cheaply. |
```

- [ ] **Step 2: Skill List 表按字母序加四行**

在 `ai-infrastructure-scarcity-radar` 行之后、`company-profile` 行之前插入：

```markdown
| `chain-alpha-mismatch-discovery` | Full industry-chain panorama and supply-demand mismatch link discovery. | You have a big theme and need the whole chain mapped plus the links where demand outruns supply. |
| `chain-alpha-monopoly-screen` | Sub-link breakdown and monopoly screening with CR3, margin, and revenue-share gates. | You confirmed a mismatch link and need the <=10 strongest companies in it. |
| `chain-alpha-verification` | 100-point four-tier company verification with drawdown-based position sizing. | You have US-listed candidates and need a buy/watch/reject grade plus a position cap. |
| `chain-alpha-pipeline` | In-session orchestration of the three chain-alpha steps with funnel discipline. | You want the full theme-to-company workflow in one run. |
```

- [ ] **Step 3: Use Skills In Agent 代码块加一行**

```text
Use invest-flow:chain-alpha-pipeline to find investable companies in AI data center power.
```

- [ ] **Step 4: Output Paths 表加四行**

```markdown
| Chain-alpha mismatch discovery | `output/chain-alpha-mismatch-discovery/` |
| Chain-alpha monopoly screen | `output/chain-alpha-monopoly-screen/` |
| Chain-alpha verification | `output/chain-alpha-verification/` |
| Chain-alpha pipeline summary | `output/chain-alpha-pipeline/` |
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Document chain-alpha skills in README

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: 更新 plugin 元数据（版本同步）

**Files:**
- Modify: `plugins/invest-flow/.codex-plugin/plugin.json`
- Modify: `plugins/invest-flow/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.agents/plugins/marketplace.json`（无版本字段，确认无需改动即可）

- [ ] **Step 1: 两个 plugin.json 版本 0.2.1 -> 0.3.0，并补充描述与关键词**

两个文件都做：
- `"version": "0.2.1"` 改为 `"version": "0.3.0"`。
- `keywords` 数组追加：`"industry-chain", "supply-demand", "chain-alpha"`。
- `description` 末尾的 `and market data routing.` 改为 `chain-alpha industry-chain stock selection pipeline, and market data routing.`（保持单句结构通顺即可）。

仅 `.codex-plugin/plugin.json` 额外在 `interface.defaultPrompt` 数组追加：

```json
"Use InvestFlow to run the chain-alpha pipeline on AI data center power."
```

- [ ] **Step 2: 更新 .claude-plugin/marketplace.json 描述**

`plugins[0].description` 改为（在原句中加入 chain-alpha）：

```json
"Investment research, reflexivity analysis, and market data workflows: multi-agent stock analysis, chain-alpha industry-chain stock selection, buyability scoring, earnings review, daily US market scans, non-consensus discovery, and report indexing."
```

`.agents/plugins/marketplace.json` 无版本和描述字段需要变更，检查后保持原样。

- [ ] **Step 3: 验证 JSON 合法且版本一致**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && python -c "
import json
a = json.load(open('plugins/invest-flow/.codex-plugin/plugin.json'))
b = json.load(open('plugins/invest-flow/.claude-plugin/plugin.json'))
json.load(open('.claude-plugin/marketplace.json')); json.load(open('.agents/plugins/marketplace.json'))
assert a['version'] == b['version'] == '0.3.0', (a['version'], b['version'])
print('OK: versions', a['version'])"
```
Expected: `OK: versions 0.3.0`

- [ ] **Step 4: Commit**

```bash
git add plugins/invest-flow/.codex-plugin/plugin.json plugins/invest-flow/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Bump invest-flow to 0.3.0 with chain-alpha skills

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 最终验证

- [ ] **Step 1: 四个 skill frontmatter 与目录结构批量校验**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -c "
import yaml, pathlib
names = ['chain-alpha-mismatch-discovery','chain-alpha-monopoly-screen','chain-alpha-verification','chain-alpha-pipeline']
for n in names:
    base = pathlib.Path('plugins/invest-flow/skills')/n
    fm = yaml.safe_load((base/'SKILL.md').read_text(encoding='utf-8').split('---')[1])
    assert fm['name'] == n, (fm['name'], n)
    assert (base/'references/methodology.md').exists(), n
    assert (base/'references/report-template.md').exists(), n
print('OK: all 4 skills valid')"
```
Expected: `OK: all 4 skills valid`

- [ ] **Step 2: 既有测试套件未受影响**

Run:
```bash
cd /Users/webbergao/work/src/ai-investment-advisor && source .venv/bin/activate && python -m unittest \
  plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py \
  plugins/invest-flow/skills/company-buyability-score/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py
```
Expected: 全部 `OK`（与改动无关，确认未误伤）。

- [ ] **Step 3: 对照 spec 复核硬门槛数字**

逐项确认写入的文件与 spec 一致：错位硬门槛（需求+供给实证）、错位评分满分 20、候选评分满分 25、CR3>50%、毛利 25% 剔除线、占比 <20% 剔除 / 20-40% 增量贡献测试 / ≥40% 纯正、100 分四档分数线（80/65/50）、负分项 0 到 -15、风险预算默认 2%、"通过"×0.5、弹性标的 ×0.5。

- [ ] **Step 4: 功能性冒烟（人工，可选）**

在新会话中运行 `使用 invest-flow:chain-alpha-mismatch-discovery 分析 AI 数据中心电力`，检查：全景列表覆盖四段、错位环节带评分、报告落盘路径正确。
