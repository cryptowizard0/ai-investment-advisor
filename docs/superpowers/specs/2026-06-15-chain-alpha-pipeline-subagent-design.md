# chain-alpha-pipeline subagent 化重构设计

日期：2026-06-15
状态：待用户确认
作者：InvestmentFlow

## 1. 背景与目标

现有 `chain-alpha-pipeline` 在**当前主会话内顺序执行**三步（mismatch-discovery → monopoly-screen → verification），步内的多个环节、多家公司也是串行处理。问题：

- 长主题下三步证据全堆在主会话，上下文容易耗尽。
- 步内本可并行的工作（第二步多环节、第三步多公司）被串行化，慢。

目标：把 pipeline 重构为**主 agent 跨步串行调度、步内 fan-out 到 subagent 并行、主 agent 汇总**的形态，同时保持仓库的平台中立约定（Codex + Claude Code 同一份 SKILL.md 可用）。

## 2. 已确认的设计决策

| 决策点 | 结论 |
|---|---|
| subagent 粒度 | 步内 fan-out：主 agent 跨步串行；第二步每个错位环节 1 个 subagent，第三步每家入选公司 1 个 subagent |
| 平台兼容 | 双模式降级：检测到 subagent 能力（Claude Code）则并行 fan-out；否则（Codex）降级为当前会话内串行，行为与产出格式等价 |
| 改动范围 | 只改编排层 `chain-alpha-pipeline`；三个步骤 skill 零改动 |
| 交接机制 | subagent 既写 output 报告（持久产物），又在 final message 返回结构化交接字段；主 agent 默认用返回字段汇总，必要时回读文件 |
| Step 3 收口 | 主 agent 按 Step 2 的 25 分排序，挑 top-K（默认 6）美股/ADR 候选再 fan-out，不再对全部美股候选逐一验证 |
| 并行批次上限 | 单波并行默认 ≤6 个 subagent，超出分批 |
| 脚本 | 不写 Python 调度脚本；派发是 agent 行为 |

## 3. 架构与数据流

```
主 agent (chain-alpha-pipeline)
│
├─ 能力探测：能否派发 subagent？
│     Claude Code → 并行模式    Codex → 串行降级（行为等价，仅不并行）
│
├─ Step 1：主 agent 自己做（全景不可分，单环节无并行收益）
│     产出：产业链全景 + 2-4 个错位环节 + 错位评分
│     ↓ 交接：环节清单（名称 / 在全景中的位置 / 错位评分 / 需求+供给证据摘要 / 供给约束实证清单）
│
├─ Step 2：fan-out —— 每个错位环节 1 个 subagent（并行，N≤4）
│     每个 subagent：跑 chain-alpha-monopoly-screen（单环节）
│       → 写 output/chain-alpha-monopoly-screen/...{环节}...md
│       → final message 返回结构化交接：候选清单，每家含
│         公司 / Ticker / 子环节 / 25 分 / 占比初值+置信度 / CR3 证据等级 / 是否美股或 ADR / 待第三步核实事项
│     主 agent：收齐 N 份 → 汇总候选池 → 按 25 分排序
│              挑美股/ADR 候选 top-K（默认 K≤6）进入 Step 3
│     ↓
├─ Step 3：fan-out —— 每家入选公司 1 个 subagent（并行，M≤6）
│     每个 subagent：跑 chain-alpha-verification（单公司）
│       → 写 output/chain-alpha-verification/...md
│       → 返回：档位 / 总分 / 仓位上限 / 反证条件 / 跟踪指标
│     主 agent：收齐 M 份
│     ↓
└─ Step 4：主 agent 汇总 → chain-alpha-pipeline 报告（深挖 top 2-3）
```

### 交接字段契约

Step 1 → Step 2（每个错位环节）：环节名称、在全景列表中的位置、错位强度评分、需求/供给证据摘要、供给约束实证清单。

Step 2 → 主 agent（每家候选）：公司名、Ticker、子环节、候选 25 分、占比初值与置信度、CR3 证据等级、是否美股/ADR、待第三步核实事项。

主 agent → Step 3（每家入选公司）：上述候选字段 + 待核实事项，作为单公司 verification 的输入上下文。

Step 3 → 主 agent（每家公司）：档位、总分、仓位上限、反证条件、跟踪指标。

## 4. 失败与降级处理

写入 `references/methodology.md`：

- **Step 2 某环节 subagent 失败/返回空**：不整体中止；用成功环节继续，汇总报告"候选漏斗"标注该环节"未完成（subagent 失败）"，并入降级章节。
- **Step 3 某公司 subagent 失败**：该公司标"验证未完成"，不给档位/仓位，其余正常。
- **能力探测失败或并行不可用（Codex）**：整体降级为串行模式，行为与产出格式与现状一致——双模式的核心承诺，保证两平台报告可比。
- **复用现有降级分支**：Step 1 零错位环节、Step 2 候选全非美股等，沿用现有 methodology 第 3 节规则，不重写。

## 5. 与漏斗纪律的关系

fan-out 不放宽任何门槛。2-4 环节 / 每环节 ≤10 候选 / 深挖 2-3，以及各步骤 skill 的硬门槛（错位双证据、CR3>50%、毛利 25%、占比双轨、100 分四档等）全部不变。subagent 仅为执行单元，纪律仍由编排层和步骤 skill 强制。

## 6. 文件改动

修改：
- `plugins/invest-flow/skills/chain-alpha-pipeline/SKILL.md` —— 工作流改为能力探测 + 步内 fan-out + 主 agent 汇总；保留串行降级；平台中立措辞。
- `plugins/invest-flow/skills/chain-alpha-pipeline/references/methodology.md` —— 新增能力探测、fan-out 规则、并行失败处理、top-K 收口、批次上限；保留现有漏斗纪律与降级分支。

新增：
- `plugins/invest-flow/skills/chain-alpha-pipeline/references/subagent-prompts.md` —— 派发给 Step 2 / Step 3 subagent 的 prompt 模板，含完整交接字段契约。

零改动：
- `chain-alpha-mismatch-discovery`、`chain-alpha-monopoly-screen`、`chain-alpha-verification` 三个步骤 skill。

文档与元数据：
- 如版本需要，可在后续 plan 决定是否 bump invest-flow 版本（本次仅编排层增强，倾向小版本或合并入现有 0.3.0 未发布范围，由 plan 阶段确认）。
- 视情况更新 AGENTS.md / README 对 pipeline 的描述（说明并行/串行双模式）。

## 7. 验证方式

无单测（Markdown skill 包）。验证：

1. `chain-alpha-pipeline/SKILL.md` frontmatter 合法、name 不变、平台中立措辞（出现"agent 会话"或并列 Codex/Claude Code）。
2. `references/subagent-prompts.md` 的派发模板包含完整交接字段契约，与步骤 skill 的输出字段对齐。
3. `git diff` 确认三个步骤 skill 文件零改动。
4. 既有 50 个单测不受影响。
5. 功能冒烟（人工）：在 Claude Code 跑一次完整 pipeline，确认 Step 2/3 并行派发、交接字段完整、降级分支可触发；Codex 串行路径在描述上可行。

## 8. 明确不做（YAGNI）

- Python 调度脚本（派发是 agent 行为，脚本帮不上）。
- 跨会话持久化队列。
- 三个步骤 skill 的任何方法论数字改动。
- 把现有 `multi-agent-stock-analysis` 一并 subagent 化（超出本次范围）。
