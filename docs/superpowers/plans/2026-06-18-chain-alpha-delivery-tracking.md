# chain-alpha-delivery-tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建可复用 skill `chain-alpha-delivery-tracking`，对 chain-alpha `待验证` 标的做前瞻性"营收兑现"判断（验证链 5 级阶段闸门 + 增速/归因/动态估值三引擎 + 双向升降档），并回灌 chain-alpha 档位。

**Architecture:** 纯方法论 skill（无脚本，结构对齐 chain-alpha-verification）：`SKILL.md` + `references/methodology.md` + `references/report-template.md`。被 chain-alpha-verification 与 chain-alpha-pipeline 引用；输出到 `output/chain-alpha-delivery-tracking/`。因 Claude Code 按版本号缓存 skill，必须 bump plugin 版本并重新同步后新 skill 才会加载。

**Tech Stack:** Markdown skill authoring（Codex/Claude Code 通用）、`claude plugin validate`/`update` CLI、设计源文件 `docs/superpowers/specs/2026-06-18-chain-alpha-delivery-tracking-design.md`（内容真源）。

**内容真源：** 每个被创建文件的正文按 spec 对应章节落地，并**镜像现有 `plugins/invest-flow/skills/chain-alpha-verification/` 同名文件的格式与语气**。下文给出每个文件的章节骨架与必须编码的硬规则；散文表述以 spec 为准。

**Authoring 提示：** 写 `SKILL.md` 与 references 时遵循 superpowers:writing-skills 的要求（frontmatter 含 name/description；细节放 references；平台中立措辞）。

---

### Task 1: Scaffold 目录与 SKILL.md

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-delivery-tracking/SKILL.md`

- [ ] **Step 1: 建目录并写 SKILL.md**

镜像 `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md` 的结构。frontmatter + 章节：`# chain-alpha 营收兑现追踪` → `## Overview`（定位：verification 下游模块，输入 `待验证`/在监控的 `通过/金池子`，输出兑现度结论+升降档，回灌 chain-alpha；默认输出目录 `./output/chain-alpha-delivery-tracking/`）→ `## Trigger`（`使用 invest-flow:chain-alpha-delivery-tracking 跟踪 688017`；被 verification/pipeline 引用；非美股不排除）→ `## Workflow`（读 references 后按"验证链点灯 → 三引擎 → 升降档映射 → 输出兑现追踪卡"执行；区分 事实/推断/假设）→ `## Quality Rules`（不可跳级、B 评分不得救回未点亮 L4、PE/PS 双轨、历史分位锚、重估须被验证链背书、中文输出、作者字段 `InvestmentFlow`、研究优先非交易指令）→ `## Resources`（指向两份 references）。

frontmatter：
```yaml
---
name: chain-alpha-delivery-tracking
description: "chain-alpha 营收兑现追踪：对 chain-alpha 待验证/观察池标的（如绿的谐波）做前瞻性兑现判断——验证链 5 级阶段闸门（订单→产能→放量→入表→盈利）、增速/归因/动态估值(PE/PS双轨)三引擎、双向升降档并回灌 chain-alpha 档位与仓位。适用于：(1) 跟踪待验证标的营收是否真兑现, (2) chain-alpha-verification 的下游跟踪模块。输出保存至 ./output/chain-alpha-delivery-tracking/。"
---
```

- [ ] **Step 2: 校验清单通过**

Run: `claude plugin validate /Users/webbergao/work/src/ai-investment-advisor/plugins/invest-flow`
Expected: `✔ Validation passed`（确认 SKILL.md frontmatter 合法、无 `interface` 等非法键）。

- [ ] **Step 3: 结构自检**

Run: `head -4 plugins/invest-flow/skills/chain-alpha-delivery-tracking/SKILL.md`
Expected: 第 2 行 `name: chain-alpha-delivery-tracking`，第 3 行有 `description:`。

- [ ] **Step 4: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-delivery-tracking/SKILL.md
git commit -m "feat: scaffold chain-alpha-delivery-tracking SKILL.md"
```

---

### Task 2: references/methodology.md（验证链 + 三引擎 + 升降档）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/methodology.md`

- [ ] **Step 1: 写 methodology.md**

镜像 `chain-alpha-verification/references/methodology.md` 的编号小节风格。必须包含并逐条编码 spec 的以下内容：

1. **验证链 5 级阶段闸门**（spec §2）：L1 订单/定点、L2 产能/供应链、L3 下游放量、L4 入表（分水岭）、L5 盈利兑现。每级给"点亮标准（可证伪硬证据）"与"伪信号"两列。硬规则成文：**逐级点灯、不可跳级；估值只能按已点亮最高级给；低级热高级暗=纯预期不算兑现。**
2. **引擎 A 增速判定**（spec §3）：收入/净利 YoY（辅 QoQ）、连续达标季数；三锚=①估值隐含增速(主)②指引隐含③同环节可比中位数；输出 达标/相当/miss。
3. **引擎 B 归因判定**（spec §3，阈值可调不写死）：质（剔理财/补贴/汇兑/并表/口径一次性）、量（目标业务增量÷总增量≥可配阈值，默认判"主导"，注明 50% 仅举例）、势（占比连续≥2 季升）；不达标=账面兑现非业务兑现，L4 不点亮。
4. **引擎 C 动态估值**（spec §3）：PE/PS 双轨（PS↔L4 收入、PE↔L5 利润；恒等式 `PS÷净利率=PE`；增收不增利=降档钩子）；历史分位锚（比该股自身历史 PS/PE 分位，不看绝对）；重估开关（regime change，重估须被验证链背书：L3/L4 亮→换新带/SOTP；L1-L2 热 L4 暗→记透支）；SOTP 分部估值。
5. **升降档规则与 chain-alpha 档位映射**（spec §4）：升档=灯进 L4 ∧ A 达标 ∧ B 达标 ∧ C(进合理带或重估被背书)，触发 chain-alpha 仓位（通过×0.5，弹性再×0.5）；降档=灯熄∨A 连续 miss∨B 恶化∨C 透支重扩 任一；维持=列明差哪一项。回灌：更新 verification 验证卡档位+仓位，给本期 vs 上期 delta；回撤推断与仓位公式沿用 verification。
6. **可选 B 评分**（spec §1/§4）：0-100 兑现度分仅用于观察池排序，不得凌驾阶段闸门、不能救回未点亮 L4 的标的。
7. **市场口径与数据源**（spec §6）：A 股比 A 股/日股比日股；历史分位与回撤用本地市场；market-data-router 降级取数降低置信度并标注；区分 事实/推断/假设。

- [ ] **Step 2: 关键规则在位自检**

Run: `grep -c -e "不可跳级" -e "PS" -e "重估" -e "归因" -e "升档" -e "降档" plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/methodology.md`
Expected: 输出 ≥ 6（六个关键词均出现至少一次）。

- [ ] **Step 3: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/methodology.md
git commit -m "feat: add delivery-tracking methodology (5-gate ladder + 3 engines + grade mapping)"
```

---

### Task 3: references/report-template.md（兑现追踪卡）

**Files:**
- Create: `plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/report-template.md`

- [ ] **Step 1: 写 report-template.md**

镜像 `chain-alpha-verification/references/report-template.md` 风格，固定中文模板，标题 `# chain-alpha 营收兑现追踪卡：{公司}（{TICKER}）`，含 `- 日期：{YYYY-MM-DD}` `- 作者：InvestmentFlow`，并落地 spec §5 的 10 个字段为章节：
1. 标的/Ticker/所属环节/本期日期/上次复盘日期
2. 验证链灯带（L1–L5 亮/部分/暗 + 相对上期灯位变化）—— 用表格
3. 引擎 A：收入与净利 YoY、三锚对比、连续达标季数
4. 引擎 B：质（一次性剔除明细）/量（目标业务增量占比）/势（占比轨迹）+ 归因结论
5. 引擎 C：forward PS / forward PE 双轨 vs 各自历史分位带；重估状态（无/候选/成立）；SOTP（如适用）
6. 预期差对账：上期指引 vs 本期实际
7. 本期结论：升/降/维持 + 触发的具体项
8. 回灌 chain-alpha：新档位、新仓位上限、delta
9. 反证条件更新 + 下次复盘时间
10. 数据来源（事实/推断/假设）

- [ ] **Step 2: 字段在位自检**

Run: `grep -c -e "验证链灯带" -e "引擎 A" -e "引擎 B" -e "引擎 C" -e "预期差" -e "回灌" -e "数据来源" plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/report-template.md`
Expected: 输出 7。

- [ ] **Step 3: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-delivery-tracking/references/report-template.md
git commit -m "feat: add delivery-tracking 兑现追踪卡 report template"
```

---

### Task 4: 接入 chain-alpha-verification 与 chain-alpha-pipeline

**Files:**
- Modify: `plugins/invest-flow/skills/chain-alpha-verification/SKILL.md`（Resources 末尾追加引用）
- Modify: `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md`（跟踪/推荐用法处引用）

- [ ] **Step 1: verification SKILL.md 追加跟踪指引**

在 `chain-alpha-verification/SKILL.md` 的 `## Resources` 区块之前（"Quality Rules" 末尾后）新增一节：

```markdown
## 下游跟踪

`待验证` 与在监控的 `通过/金池子` 标的，用 `invest-flow:chain-alpha-delivery-tracking` 做周期性营收兑现追踪（验证链阶段闸门 + 增速/归因/动态估值三引擎），并据其结论回灌本 skill 的档位与仓位。
```

- [ ] **Step 2: pipeline SKILL.md 在"推荐用法"引用**

在 `chain-alpha-pipeline/SKILL.md` 的"## 推荐用法"小节末尾追加一条：

```markdown
4. 进入 `待验证` 的标的，后续用 `使用 invest-flow:chain-alpha-delivery-tracking 跟踪 <TICKER>` 做按季兑现追踪与升降档，不必每次重跑完整 pipeline。
```

- [ ] **Step 3: 校验未破坏清单**

Run: `claude plugin validate /Users/webbergao/work/src/ai-investment-advisor/plugins/invest-flow`
Expected: `✔ Validation passed`

- [ ] **Step 4: Commit**

```bash
git add plugins/invest-flow/skills/chain-alpha-verification/SKILL.md plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md
git commit -m "feat: wire delivery-tracking into verification and pipeline skills"
```

---

### Task 5: 更新 AGENTS.md 与 README.md

**Files:**
- Modify: `AGENTS.md`（Active packaged skills 列表 + Output Conventions）
- Modify: `README.md`（skill 表 line ~64 后 + output 路径表 line ~116 后）

- [ ] **Step 1: AGENTS.md skill 列表追加**

在 `AGENTS.md` 的 "Active packaged skills" 列表中 `chain-alpha-pipeline` 条目之后追加：

```markdown
- `chain-alpha-delivery-tracking` - chain-alpha follow-on: forward-looking revenue-delivery tracking for 待验证 candidates via a 5-gate validation ladder (order→capacity→ramp→revenue→profit), growth/attribution/dynamic-valuation (PE&PS dual-track) engines, and symmetric grade up/down that feeds back into chain-alpha
```

- [ ] **Step 2: AGENTS.md Output Conventions 追加**

在 Output Conventions 列表的 `Chain-alpha pipeline summary` 行之后追加：

```markdown
- Chain-alpha delivery tracking: `output/chain-alpha-delivery-tracking/chain-alpha-delivery-tracking-{TICKER}-{YYYY-MM-DD}.md`
```

- [ ] **Step 3: README.md skill 表追加**

在 `README.md` line 64（`chain-alpha-pipeline` 行）之后插入：

```markdown
| `chain-alpha-delivery-tracking` | Forward-looking revenue-delivery tracking for 待验证 candidates with a 5-gate ladder, growth/attribution/dynamic-valuation engines, and symmetric grade up/down. | You hold a 待验证 name (e.g. 绿的谐波) and need a quarterly read on whether revenue is actually being delivered. |
```

- [ ] **Step 4: README.md output 路径表追加**

在 `README.md` line 116（`Chain-alpha pipeline summary` 行）之后插入：

```markdown
| Chain-alpha delivery tracking | `output/chain-alpha-delivery-tracking/` |
```

- [ ] **Step 5: 自检**

Run: `grep -c chain-alpha-delivery-tracking AGENTS.md README.md`
Expected: `AGENTS.md:2` 与 `README.md:2`。

- [ ] **Step 6: Commit**

```bash
git add AGENTS.md README.md
git commit -m "docs: register chain-alpha-delivery-tracking in AGENTS.md and README.md"
```

---

### Task 6: 版本 bump + 重新同步（让新 skill 实际加载）

**Files:**
- Modify: `plugins/invest-flow/.claude-plugin/plugin.json`（version → 0.3.2）
- Modify: `plugins/invest-flow/.codex-plugin/plugin.json`（version → 0.3.2）

- [ ] **Step 1: 两份 plugin.json 版本同步 bump**

把两文件的 `"version": "0.3.1"` 改为 `"version": "0.3.2"`（marketplaces 不带版本，无需改）。

- [ ] **Step 2: 校验 + JSON 合法**

Run: `claude plugin validate /Users/webbergao/work/src/ai-investment-advisor/plugins/invest-flow && python3 -c "import json;[json.load(open(f)) for f in ['plugins/invest-flow/.claude-plugin/plugin.json','plugins/invest-flow/.codex-plugin/plugin.json']];print('json ok')"`
Expected: `✔ Validation passed` 且 `json ok`。

- [ ] **Step 3: Commit**

```bash
git add plugins/invest-flow/.claude-plugin/plugin.json plugins/invest-flow/.codex-plugin/plugin.json
git commit -m "chore: bump invest-flow to 0.3.2 for chain-alpha-delivery-tracking"
```

- [ ] **Step 4: 刷新 marketplace 并升级已安装插件**

Run: `claude plugin marketplace update investflow-local && claude plugin update invest-flow@investflow-local`
Expected: `Plugin "invest-flow" updated from 0.3.1 to 0.3.2 ... Restart to apply changes.`

- [ ] **Step 5: 确认新 skill 进入缓存**

Run: `ls /Users/webbergao/.claude/plugins/cache/investflow-local/invest-flow/0.3.2/skills/chain-alpha-delivery-tracking/`
Expected: 列出 `SKILL.md` 与 `references/`。

---

### Task 7: 验收 smoke run（绿的谐波 688017）

> 需重启 Claude Code 使 0.3.2 生效后执行；本任务为 spec §8 验收，跑通即完成。可在新会话进行。

**Files:**
- Output: `output/chain-alpha-delivery-tracking/chain-alpha-delivery-tracking-688017-2026-06-18.md`（运行时生成）

- [ ] **Step 1: 触发 skill**

在（重启后的）会话中执行：`使用 invest-flow:chain-alpha-delivery-tracking 跟踪 688017`，输入沿用 verification 已有结论（待验证、谐波占比~80%、PE~290、2025 营收+47%/净利+121%）。

- [ ] **Step 2: 验收检查（对照 spec §8）**

确认生成的兑现追踪卡满足：
- 给出当前最高点亮级别（绿的谐波应判 L1/L2 亮、L4 未明确点亮）。
- 三引擎读数齐全；引擎 C 含 PS/PE 双轨 + 历史分位 + 重估状态。
- 给出 升/降/维持 结论 + 触发项（应为"维持待验证：差 L4 入表 + C 仍透支"）。
- 回灌段给出档位/仓位（维持待验证，不给仓位）。
- 阶段闸门未被 B 评分绕过；区分 事实/推断/假设；未排除非美股。

- [ ] **Step 3: 归档（如需）**

确认文件落在 `output/chain-alpha-delivery-tracking/`；如已存在则自动追加 `(1)(2)` 未覆盖。

---

## 自检（spec coverage）

- spec §2 验证链 → Task 2.1。spec §3 三引擎 → Task 2.2-2.4。spec §4 升降档映射 → Task 2.5。spec §5 模板 → Task 3。spec §6 数据源 → Task 2.7 + Task 3 字段10。spec §7 落地形态（SKILL/目录/触发/引用/维护）→ Task 1、4、5、6。spec §8 验收 → Task 7。spec §1 可选 B 评分 → Task 2.6。spec §9 YAGNI（无脚本/无定时/无下单）→ 全程未引入脚本任务，已遵守。
- 命名一致性：全程 skill 名 `chain-alpha-delivery-tracking`、输出前缀 `chain-alpha-delivery-tracking-{TICKER}-{YYYY-MM-DD}.md`、版本目标 0.3.2，前后一致。
- 无 placeholder：每个 Task 给出确切路径、要编码的硬规则、确切校验命令与期望输出。
