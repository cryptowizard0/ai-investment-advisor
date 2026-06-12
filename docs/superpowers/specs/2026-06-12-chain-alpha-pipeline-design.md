# chain-alpha 产业链选股工作流设计

日期：2026-06-12
状态：待用户确认
作者：InvestmentFlow

## 1. 背景与目标

构建一条"拆解产业链 -> 分析关键环节 -> 找到可投资公司"的多 skill 投资工作流，核心投资逻辑：

1. **找供需错位环节**：需求增量大、供给跟不上的环节（扩产周期长、技术壁垒、公司不愿扩产）。
2. **拆错位环节、找垄断**：拆上中下游，找 CR3 > 50% 的寡头格局，看关键材料/环节占公司收入比重，排除低利润低门槛的低端竞争。
3. **验证公司**：产业位置、环节收入占比、季度增速是否匹配行业、估值透支度，最后推断最大回撤定仓位。

不复用改造现有 skill，而是新建一组带统一前缀的专用 skill，把硬性门槛直接写进各步骤方法论，由编排 skill 串联。

## 2. 已确认的设计决策

| 决策点 | 结论 |
|---|---|
| 第一步入口 | 用户给定大主题（如"AI 数据中心电力"），不做全市场自动扫描 |
| 实现形态 | 三个新步骤 skill + 一个编排 skill，硬门槛写进各 skill 方法论 |
| 统一前缀 | `chain-alpha-` |
| 股票池 | 发现全球（含日韩台欧，保证 CR3 判断不失真），仅 US-listed equities/ADRs 进入第三步验证和仓位建议 |
| 环节收入占比门槛 | 双轨制：≥40% 纯正标的；20-40% 须通过增量贡献测试且仓位减半；<20% 剔除 |
| 仓位规则 | 风险预算法：仓位上限 = 单笔风险预算（默认组合的 2%，可参数化）÷ 预估最大回撤 |
| 脚本 | v1 不写 Python 脚本，仅 SKILL.md + references/（方法论 + 报告模板） |

## 3. 总体架构

```text
用户: 使用 invest-flow:chain-alpha-pipeline 分析 <大主题>
        │
        ▼
chain-alpha-pipeline (编排，漏斗纪律)
        │
        ├─ Step 1: chain-alpha-mismatch-discovery
        │     输入: 大主题
        │     输出: 产业链全景列表 + 2-4 个供需错位环节
        │
        ├─ Step 2: chain-alpha-monopoly-screen   (对每个错位环节运行)
        │     输入: 单个错位环节
        │     输出: ≤10 家候选公司（全球格局，标注 US-investable）
        │
        ├─ Step 3: chain-alpha-verification      (仅 US-listed/ADR 候选)
        │     输入: 候选公司清单
        │     输出: 每家公司验证卡（通过/剔除/观察）+ 仓位上限
        │
        ▼
最终中文汇总报告（深挖 2-3 家）
```

漏斗纪律：2-4 个错位环节 → 每环节 ≤10 家候选 → 最终深挖 2-3 家。每一步的输出文件是下一步的输入，三个步骤 skill 均可脱离 pipeline 单独使用。

## 4. Skill 设计

### 4.1 chain-alpha-mismatch-discovery（第一步：找供需错位环节）

**输入**：用户给定的大主题。

**工作流（两段式，第一段不得跳过）**：

第一段：产业链全景。
- 从终端需求倒推，把整个产业链按 上游 / 中游 / 下游 / 生态支撑 完整列出。
- 每个环节用列表呈现，固定字段：环节名称、作用、需求来源、供给弹性、代表公司、价值池大小。
- 全景必须覆盖整条链，不允许只列感兴趣的部分。全景列表是报告的独立章节，即使最后没找到错位环节，全景本身也是有效产出。

第二段：错位环节识别。
- 在全景列表基础上逐环节做供需错位判断，每个候选错位环节必须回答两个问题并附证据：
  - 需求为什么增加：增量来源、预算来源、单位用量是否非线性。
  - 供给为什么跟不上：扩产周期 / 技术壁垒 / 公司不愿扩产（资本纪律）/ 认证周期，至少落实一项。

**硬门槛**：必须同时具备需求增量证据 + 供给约束实证（价格上涨、交期拉长、订单积压、产能利用率至少一项），否则只能标记"高景气，非错位"，不得进入第二步。

**输出**：2-4 个错位环节，每个标注其在全景列表中的位置。报告保存至 `output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-{主题}-{YYYY-MM-DD}.md`。

### 4.2 chain-alpha-monopoly-screen（第二步：拆环节找垄断）

**输入**：第一步输出的单个错位环节。

**工作流**：
1. 拆该环节的上中下游子环节。
2. 每个子环节列出全球公司格局（必须含日韩台欧供应商，否则 CR3 判断失真）。
3. 应用筛选门槛（见下）。
4. 对存活公司看关键材料/环节占公司收入比重，做占比初筛。

**硬门槛**：
- **集中度**：CR3 > 50%，或有明确证据的寡头/双寡头格局。精确市占率不可得时允许推断，必须标注证据等级（事实/推断/假设）；纯假设的 CR3 不算通过。
- **排除低端竞争**：毛利率持续低于 25% 且无技术/认证壁垒的公司直接剔除。
- **占比初筛**：环节收入占比明显 <20% 的不进入第三步。

**输出**：每个环节 ≤10 家候选，标注哪些是 US-listed/ADR（仅这些进第三步），非美股垄断者作为产业格局背景保留在报告中。保存至 `output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节}-{YYYY-MM-DD}.md`。

### 4.3 chain-alpha-verification（第三步：验证定仓位）

**输入**：第二步输出的 US-listed/ADR 候选公司。

**固定 checklist**，逐项给"通过 / 剔除 / 待验证"：

1. **产业位置**：是否做高端、份额多少、客户是谁。
2. **环节收入占比（双轨制门槛）**：
   - ≥40%：纯正标的，走完整验证 + 全额仓位规则。
   - 20-40%：弹性标的，必须额外通过增量贡献测试——该环节贡献公司未来 1-2 年收入增量的 ≥50%，或占比有明确上升轨迹和管理层指引；通过的仓位上限为纯正标的的一半，不通过的进观察池。
   - <20%：剔除。
   - 占比允许推断值 + 置信度标注；公司 segment 披露口径不拆分时必须明确说明。
3. **季度收入同比增速**：对照同环节可比公司中位数；跑输行业的必须解释原因。
4. **估值**：当前估值 + 远期估值，结合增速判断透支程度。
5. **最大回撤推断**：历史回撤、估值压缩情景、业绩 miss 情景三者取最大。
6. **仓位**：风险预算法，仓位上限 = 单笔风险预算（默认组合的 2%，可参数化）÷ 预估最大回撤。例：预估回撤 40%，风险预算 2%，仓位上限 5%。

**兜底规则**：若某环节经 40% 纯正门槛筛选后为零，报告列出"因占比不足被剔除但格局最好的公司"作为参考（不给仓位建议）。

**输出**：每家公司一张验证卡（含通过/剔除/观察结论、仓位上限、反证条件）。保存至 `output/chain-alpha-verification/chain-alpha-verification-{TICKER}-{YYYY-MM-DD}.md`，多公司汇总时为 `chain-alpha-verification-{环节}-{YYYY-MM-DD}.md`。

### 4.4 chain-alpha-pipeline（编排）

**触发**：`使用 invest-flow:chain-alpha-pipeline 分析 <大主题>`。

**职责**：
- 在当前 agent 会话内依次执行三个步骤 skill，传递每步输出。
- 强制漏斗纪律：第一步保留 2-4 个错位环节；第二步每环节 ≤10 家候选；第三步深挖 2-3 家。
- 生成最终中文汇总报告，保存至 `output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`。

**推荐用法（写进 SKILL.md）**：一次完整 pipeline 是重活（三步均需 web 检索取证）。日常建议先单独跑第一步（成本低），人工确认错位环节靠谱后，再对选中的 1-2 个环节跑二、三步。

## 5. 通用约定

- 中文输出；金融/技术术语保留 English。
- 必须区分 事实 / 推断 / 假设；关键数字标注来源和日期；不可得标注"不确定"或"数据暂缺"，不得编造。
- 输出文件已存在时追加 `(1)`, `(2)`，不覆盖。
- 所有报告含固定作者字段 `InvestmentFlow`。
- 每个 skill 目录结构：`SKILL.md` + `references/methodology.md` + `references/report-template.md`。

## 6. 可实施性约束（写进方法论的诚实提醒）

- **CR3 是最难程序化的指标**：精确市占率多在付费行业报告中，依赖 web search + 财报/IR 披露估计，必须用证据等级兜底。
- **环节收入占比依赖披露口径**：10-K segment 数据未必按目标环节拆分，允许推断值 + 置信度，不追求假精确。
- **增速与估值数据最可靠**：美股季度收入、估值可由 yfinance/现有 market-data-router 获得；行业基准定义为同环节可比公司中位数。

## 7. 变更范围

新增：
- `plugins/invest-flow/skills/chain-alpha-mismatch-discovery/`（SKILL.md + references/）
- `plugins/invest-flow/skills/chain-alpha-monopoly-screen/`（同上）
- `plugins/invest-flow/skills/chain-alpha-verification/`（同上）
- `plugins/invest-flow/skills/chain-alpha-pipeline/`（同上）
- `output/` 下四个对应子目录

同步更新：
- `AGENTS.md`（仓库结构、Active packaged skills、Output Conventions）
- `README.md`
- 四个元数据文件版本号同步：`plugins/invest-flow/.codex-plugin/plugin.json`、`plugins/invest-flow/.claude-plugin/plugin.json`、`.agents/plugins/marketplace.json`、`.claude-plugin/marketplace.json`

## 8. 验证方式

v1 无脚本，无 unittest。验证方式：
1. 四个 SKILL.md frontmatter 合法（name + description），结构符合仓库 Skill Layout 约定。
2. 用一个真实主题（如"AI 数据中心电力"）跑一次第一步，检查全景列表完整性和错位门槛执行。
3. 对选中环节跑二、三步，检查 CR3 证据等级标注、双轨占比门槛和仓位公式输出。

## 9. 明确不做（YAGNI）

- 全市场自动扫描入口。
- Python 报告骨架脚本（如后续模板稳定可补，参照 non-consensus-company-discovery 的 generate_report.py 模式）。
- 非美股标的的验证与仓位建议。
- 自动交易指令；所有输出是研究与跟踪优先级。
