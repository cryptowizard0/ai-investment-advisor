# chain-alpha 非美股市场模式设计

日期：2026-06-16
状态：待用户确认
作者：InvestmentFlow

## 1. 背景与问题

chain-alpha 的第三步 `chain-alpha-verification`（及 pipeline 仓位建议）默认股票池为 `US-listed equities/ADRs`，非美股标的被列为"背景参考、不给仓位"。两次实跑（MLCC 2026-06-13、人形机器人 2026-06-15）暴露结构性失效：这两条产业链最有 alpha 的环节（被动件、机器人传动、磁材）垄断者主要在 A 股 / 日股 / 台股 / 私有公司，导致第三步几乎空转、无可投标的。

用户明确反馈（2026-06-16）：**"不要只聚焦美股，A 股也要观察，不要非美股就剔除。"**

## 2. 核心认知纠正

剔除标准应是**"能不能买到"（可投性）**，不是**"是不是美股"**。

- **可投**：美股/ADR 主板、A 股、港股、日股、台股主板 → 走完整第三步验证 + 仓位。
- **不可投**：未上市（私有，如 GSA、Rollvis）、仅 OTC 粉单（如 HSYDF）→ 列背景参考，不给仓位。

## 3. 已确认的设计决策

| 决策点 | 结论 |
|---|---|
| 默认股票池 | `US-listed equities/ADRs` → **全球主要可投市场（美股/ADR、A 股、港股、日股、台股主板）** |
| 非美股深度 | 完整验证 + 仓位（A 股等与美股同标准走第三步） |
| 验证口径 | 按候选自身上市地：估值用同市场可比中位数；最大回撤用本地市场历史价格；占比双轨、100 分四档、仓位公式不变 |
| 仓位与币种 | 仓位为组合占比 %，与币种无关，公式不变；本地市场跑 |
| 不给仓位的范围 | 仅"未上市 + 仅 OTC 粉单"；非美股不再自动剔除 |
| 范围 | 仅改 chain-alpha 四个 skill；不动 non-consensus-company-discovery 等其他 skill |
| 不变项 | 所有硬门槛数字、漏斗纪律、外部新加的 Codex 并行约束 |

## 4. 各 skill 改动

### 4.1 chain-alpha-verification（改动最大）

- **SKILL.md description 与 Overview**：默认股票池从"US-listed equities/ADRs"改为"全球主要可投市场（美股/ADR、A 股、港股、日股、台股主板）"；非美股不再排除，按各自市场口径验证并给仓位；仅未上市/仅粉单标的列背景不给仓位。
- **references/methodology.md**：
  - 新增"市场口径"小节：估值用**同市场**可比中位数（A 股比 A 股、日股比日股，不跨市场套用）；最大回撤用该标的**本地市场**历史价格（不足 5 年用上市以来）；数据经 market-data-router 降级获取时降低置信度标注。
  - 占比双轨门槛、100 分模型、四档分级、负分项、仓位公式（风险预算 2% ÷ 最大回撤；通过 ×0.5；弹性 ×0.5）**全部不变**。
  - 明确：仓位为组合占比 %，与计价币种无关。
  - 兜底/不可投：未上市或仅 OTC 粉单 → 列背景参考、不给仓位。
- **references/report-template.md**：验证卡加"上市地/市场"字段；估值与回撤行注明所用市场基准。

### 4.2 chain-alpha-monopoly-screen

- **SKILL.md + methodology.md**：删除"仅 US-listed/ADR 候选进第三步"；改为**所有可投市场候选均可进第三步**，每家候选标注上市地与可投性（可投主板 / 仅粉单 / 未上市）。
- 占比初筛、CR3 门槛、25 分候选评分**不变**。
- **report-template.md**：第六节"进入第三步的候选"表头从"US-listed/ADR 候选"改为"可投候选（标注市场）"；保留"仅粉单/未上市的最强格局者"作背景。

### 4.3 chain-alpha-pipeline

- **methodology.md**：
  - §2 Step 3 收口 top-K：从"按 25 分排序只取美股/ADR top-K"改为"**跨市场按 25 分排序取 top-K（默认 6）**"。
  - §5 失败与降级：**删除**"Step 2 候选全为非美股 → Step 3 跳过"；改为"候选全为不可投（未上市/仅粉单）→ Step 3 跳过并列背景"。
  - §3 漏斗纪律的 Step 3 兜底：从"被剔除但格局最好的公司"措辞保留，但语义改为"无通过及以上档位时列最强格局者"，不再隐含按市场剔除。
- **SKILL.md**：Step 2/Step 3 描述里"美股/ADR"措辞改为"可投市场候选"；保留 Codex 并行约束。
- **references/subagent-prompts.md**：
  - "Step 2 → Step 3 主 agent 收口"段：从"只挑美股/ADR 候选 top-K"改为"跨市场按 25 分挑 top-K"。
  - Step 2 模板交接字段"是否美股或ADR(是/否/仅粉单)"改为"**上市地与可投性（可投主板/仅粉单/未上市）**"。
  - Step 3 模板：去掉隐含美股假设，明确按候选上市地市场口径验证。
- **report-template.md**：候选漏斗表"US-listed 进入验证"行改为"可投候选进入验证（标注市场）"。

### 4.4 chain-alpha-mismatch-discovery

- 基本不动；确认"市场范围默认全球（含中国大陆及日韩台欧美）"已在方法论中（现状已满足），如措辞缺失则补一句。

## 5. 交接字段契约变更

Step 2 → 主 agent / Step 3：字段"是否美股或 ADR（是/否/仅粉单）" → **"上市地与可投性"**，取值：可投主板（注明市场，如 A股/港股/日股/台股/美股）、仅粉单、未上市。methodology.md §4 与 subagent-prompts.md 必须同步，保持字段名一致。

## 6. 不做（YAGNI）

- 不做汇率换算/本地货币风险预算细化（仓位为组合占比 %，与币种无关，无需汇率）。
- 不改 non-consensus-company-discovery、company-buyability-score 等其他 skill 的默认股票池。
- 不引入"市场模式全局开关"——验证按每个候选自身上市地的口径走，逐标的自适应。
- 不写 Python 脚本。

## 7. 验证方式

无单测（Markdown skill 包）。验证：
1. 四个 skill frontmatter 合法、name 不变。
2. `chain-alpha-verification` 不再出现"仅 US-listed/ADR"限定；出现"同市场可比""本地市场历史"口径。
3. `chain-alpha-monopoly-screen` 不再有"仅 US-listed 进第三步"；交接字段为"上市地与可投性"。
4. `chain-alpha-pipeline` methodology 不再有"候选全为非美股→跳过"；top-K 为跨市场。
5. 交接字段名在 methodology.md 与 subagent-prompts.md 一致。
6. 既有 50 单测不受影响。
7. 用新规则重跑人形机器人 pipeline：绿的谐波、金力永磁、新剑传动、五洲新春等 A 股进入第三步并拿到档位/仓位（而非被剔除）。

## 8. 重跑产物

skill 改完后用新规则重跑人形机器人完整 pipeline，覆盖（追加 (1) 后缀，不覆盖旧报告）：A 股候选进第三步验证，输出含 A 股标的的档位与仓位的新汇总报告。
