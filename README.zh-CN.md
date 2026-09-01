# InvestFlow

[英文版本](README.md)

InvestFlow 是一个仓库内置的投资研究插件，同时兼容 Codex 和 Claude Code。它把市场扫描、产业链研究、个股分析、财报解读、反身性分析和市场数据路由封装成可复用的技能。

它的旗舰工作流是 **chain-alpha 产业链选股**——从一个大主题出发，经"产业链 → 可投公司"漏斗筛选，并持续跟踪营收兑现。详见下方「首推工作流：chain-alpha 产业链选股」。

概览：技能按用途分成三大用户类（外加一个基础设施支撑层）：

| 分类 | 输入 | 入口 Skill | 用来 |
|---|---|---|---|
| **Chain Alpha** | 一个主题 | `chain-alpha` | 把一个大主题变成可投公司 |
| **Research** | 一个股票代码 | `research-stock` | 从多个独立视角判断一家公司 |
| **Monitor** | 一个日历或指数 | 选择对应的 `monitor-*` skill | 执行定期检查和事件触发更新 |

完整清单（含基础设施层）见 [技能分类](#技能分类)。

标准插件包位于 `plugins/invest-flow/`。所有打包技能位于 `plugins/invest-flow/skills/`，两个平台共享同一份技能。

## 快速上手

### Codex

1. 在 Codex 中打开这个仓库。
2. 重新加载 Codex，让它读取 `.agents/plugins/marketplace.json`。
3. 在本地插件市场安装 `InvestFlow`。
4. 在 Codex 对话中直接调用技能。

### Claude Code

1. 在本仓库目录启动 `claude`。
2. 添加本地插件市场：`/plugin marketplace add .`
3. 安装插件：`/plugin install invest-flow@investflow-local`
4. 在对话中直接调用技能，或用 `/invest-flow:技能名` 显式触发。

示例（两个平台通用）：

```text
使用 InvestFlow 分析 TSLA
使用 InvestFlow 生成今天的美股收盘复盘
使用 InvestFlow 用 chain-alpha 研究 AI 数据中心电力产业链
使用 InvestFlow 分析 HBM 产业链
```

如果插件没有出现，先确认这些文件存在：

- Codex：`plugins/invest-flow/.codex-plugin/plugin.json` 和 `.agents/plugins/marketplace.json`
- Claude Code：`plugins/invest-flow/.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`

## 首推工作流：chain-alpha 产业链选股

chain-alpha 是 InvestFlow 的旗舰工作流：把一个大主题转化为可投资的公司，定出买点与仓位，并持续跟踪营收是否真兑现。六个技能构成闭环，由 `chain-alpha` 端到端编排：

```text
主题 ─▶ chain-alpha-industry-analysis ─▶ chain-alpha-company-discovery ─▶ chain-alpha-company-verification ─▶ chain-alpha-position-plan ⇄ monitor-chain-alpha-delivery
       行业定义+增长初筛             错位拆解+≤10候选           四档分级             估值分位+潜在风险      按季营收/利润
       +产业链全景+错位环节                         （只验证）       +建仓计划定仓位         兑现追踪
       └────────────────────── 由 chain-alpha 编排 ────────────────────────────────┘
```

一条命令跑完整漏斗：

```text
使用 invest-flow:chain-alpha 分析具身智能（人形机器人）
```

漏斗纪律：行业定义与增长门槛 → 2-4 个错位环节 → 每环节 ≤10 候选 → top-6 进入验证 → 通过及以上进入第四步定仓 → 深挖 2-3 家。行业/关键环节收入增速必须 >20%、增长原因清楚、持续窗口至少 6 个月，才进入后续环节；最终仍必须落到可持续利润增速：≥30% 优先，20% 是最低放行线，<20% 筛掉。第三步 `chain-alpha-company-verification` 只做验证分级；仓位统一由第四步 `chain-alpha-position-plan` 给出（仓位上限 = 回撤预算 ÷ 潜在风险，档位/弹性折扣叠乘）。落在 `待验证` 的标的，用 `monitor-chain-alpha-delivery` 按季跟踪营收兑现，其升降档结论回灌 `chain-alpha-company-verification`，升档触发建仓时重跑第四步定仓。每一步也可单独运行——先用 `chain-alpha-industry-analysis` 低成本完成行业定义、增长门槛并确认错位环节，再决定是否跑完整流程。

## 技能分类

InvestFlow 的技能按用途分成三大用户类：Chain Alpha、Research 和 Monitor，外加一个支撑性的基础设施层。

### Chain Alpha（你带一个主题进来）

把一个大主题变成可投公司。`chain-alpha` 是旗舰——见 [首推工作流：chain-alpha](#首推工作流chain-alpha-产业链选股)。

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `chain-alpha` | 编排 chain-alpha 四步（错位发现 → 垄断筛选 → 验证分级 → 估值定仓），步内 fan-out 到 subagent（Claude Code 原生并行；Codex 工具可用时并行；否则串行降级）并强制漏斗纪律。 | 想一次跑完"主题 → 公司 → 仓位"的完整流程。 |
| `chain-alpha-industry-analysis` | 行业白话定义 + 增长门槛与产业周期定位（四阶段时间表 + 当前节点）+ 产业链全景 + 供需错位环节发现。 | 有一个大主题，需要用白话搞懂行业到底是什么、处于哪个产业周期阶段、增速为何能维持高位、拆出整条产业链，并找到需求超过供给且能落到利润增速的错位环节。 |
| `chain-alpha-company-discovery` | 错位环节拆子环节 + 用 CR3/毛利/收入占比/利润增速硬门槛做垄断筛选。 | 已确认某个错位环节，需要找出其中最强的 ≤10 家公司。 |
| `chain-alpha-company-verification` | 100 分四档公司验证 + 利润增速硬门槛（只验证分级，不定仓位）。 | 有候选公司，需要金池子/通过/待验证/剔除分级；通过及以上交给第四步定仓。 |
| `chain-alpha-position-plan` | chain-alpha 第四步：类型闸门 → PE/PS 选尺（含警戒线）→ 5 年 TTM 分位带 → 潜在风险两腿取大 → 增速消化核对（成长模型合理 PE，防机械读分位）→ 建仓计划（仓位上限 = 回撤预算 ÷ 潜在风险，档位/弹性结构折扣叠乘；信号层两系数均 ≤1 永不放大：警戒线触发新仓归零、仅一档硬证据可放宽半仓，透支再 ×0.5）。 | verification 给出档位后，需要买点判断和仓位上限。（同时列在第二类。） |

### Research（你带一个股票代码进来）

从多个独立视角判断一家公司。`research-stock` 在一次会话里编排下面这些技能。

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `research-stock` | 在当前 agent 会话中编排五个默认阶段（公司画像 → 基本面 → 机构资金 → 反身性 → Reportify）。 | 想从多个独立视角交叉验证一只股票。 |
| `research-profile` | 生成投资分析前置公司画像。 | 用户第一次听说某家公司时，用于快速理解公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争对手和行业地位。 |
| `research-fundamentals` | 做单股基本面、估值和技术面分析。 | 需要快速形成一家公司是否值得继续研究的结构化判断。 |
| `research-institutional` | 分析机构吸筹、派发和资金行为。 | 想判断主力资金是在买入、出货还是对冲。 |
| `research-reflexivity` | 索罗斯反身性分析，含快扫（5 分钟阶段判断）和深度（完整周期）两档。 | 想快速判断叙事处于启动/强化/透支/反转，或做完整的叙事、价格、现实、反转风险拆解。 |
| `research-reportify` | 生成标准化八段式个股报告，决策层含买方级三情景估值、可证伪假设、催化剂和跟踪 Dashboard。 | 需要可比较、可复盘、有证据链的正式投研报告。 |
| `research-earnings` | 从机构视角分析财报、指引、电话会和预期差；不属于 `research-stock` 默认五阶段。 | 用户指定报告期，或公司刚发布相关新财报时。 |

### Monitor（你带一个日历进来）

适合设为定时任务的周期性复盘。

| 技能 | 固定频率 | 补充触发 | 用途 |
|---|---|---|---|
| `monitor-us-market` | 每个完整美股交易日收盘后 | 重大盘后事件 | 生成中文美股收盘复盘和次日计划，结论先行、有长度预算、板块/主题动态排序 + 新动态雷达。 |
| `monitor-ai-infrastructure` | 每周 | hyperscaler capex、架构、订单或产能发生重大变化 | 扫描 AI 基建板块，达标队列交给 `chain-alpha-industry-analysis` 或 `chain-alpha`。 |
| `monitor-index-cycle` | 每个交易日做轻量检查 | 状态变化或定期复核时生成完整报告 | 使用收盘价反转阈值维护指数牛熊状态和稳定周期报告。 |
| `monitor-index-valuation` | 每月 | 指数涨跌至少 ±5%、成分调整或盈利口径重大变化 | 生成指数估值价格敏感性表，并执行单口径一致性和周期盈利失真检查。 |
| `monitor-gold` | 每周 | FOMC、CPI、实际利率、地缘政治或异常价格事件 | 分析黄金趋势、泡沫风险和宏观驱动。 |
| `monitor-chain-alpha-delivery` | 每次季度财报后 | 重大订单、产能、客户、指引或竞争结构变化 | 跟踪营收/利润兑现，回灌 Chain Alpha 档位，并可重新触发 `chain-alpha-position-plan`。 |

### 基础设施（支撑层，本身不产投资观点）

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `market-data-router` | 路由行情数据并提供降级兜底。 | 其他研究流程需要 K 线、报价、期权背景或缓存市场数据。 |
| `output-report-index` | 为已生成报告构建 Markdown 和静态 HTML 索引页。 | 明确要求生成或更新 `output/` 下的报告索引。 |

## 在智能体内使用技能

在 Codex 或 Claude Code 智能体中用自然语言调用 InvestFlow。需要指定流程时，建议直接写出技能名称：

```text
使用 invest-flow:research-stock 分析 TSLA
使用 invest-flow:monitor-us-market 扫描今天的美股收盘
使用 invest-flow:chain-alpha 分析具身智能（人形机器人）产业链
使用 invest-flow:research-reflexivity 快扫 NVIDIA 当前叙事阶段
使用 invest-flow:monitor-index-cycle 更新 SOX 牛熊周期表
使用 invest-flow:chain-alpha-position-plan 判断 NVDA 的估值分位与潜在风险
使用 invest-flow:research-earnings 解读 NVIDIA 最新财报
```

如果需要接入外部市场数据源，可从 `.env_example` 创建本地 `.env`，再填写相关密钥。

## 输出路径

报告和缓存文件会写入 `output/`：

| 流程 | 输出路径 |
|---|---|
| chain-alpha 系列 | `output/chain-alpha/` |
| Research 系列 | `output/research/` |
| Monitor 系列 | `output/monitor/` |
| 报告索引 | `output/index.md`、`output/index.html` |
| 市场数据缓存 | `output/cache/market-data/` |

输出根目录仅保留以上三个主题目录、`cache/` 和两个根级索引文件。

同一个系列目录下用 skill 前缀区分文件名，例如：`chain-alpha-industry-analysis-...`、`research-fundamentals-...`、`monitor-us-market-...` 等；若同名文件重复，仍使用 `(1)`、`(2)` 后缀分流。

报告生成类技能通常不覆盖已有文件，而是在需要时追加 `(1)`、`(2)` 等后缀。指数牛熊周期文档是例外：它使用稳定文件名原地更新，确保每个指数始终只有一份最新牛市表和一份最新熊市表。

## 维护说明

- 这是仓库内置插件，不是远程市场包。
- 投资技能只维护在 `plugins/invest-flow/skills/`，两个平台共享同一份。
- Codex 插件发现元数据位于 `.agents/plugins/marketplace.json`，Claude Code 位于 `.claude-plugin/marketplace.json`。
- 插件打包信息变更时，需同步更新两份 manifest 和两份 marketplace，并保持四处版本一致。
- README 中的技能名称应与 `plugins/invest-flow/skills/` 下的目录保持一致。
