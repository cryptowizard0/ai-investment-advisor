# InvestFlow

[英文版本](README.md)

InvestFlow 是一个仓库内置的投资研究插件，同时兼容 Codex 和 Claude Code。它把市场扫描、产业链研究、非共识发现、个股分析、财报解读、反身性分析和市场数据路由封装成可复用的技能。

它的旗舰工作流是 **chain-alpha 产业链选股**——从一个大主题出发，经"产业链 → 可投公司"漏斗筛选，并持续跟踪营收兑现。详见下方「首推工作流：chain-alpha 产业链选股」。

概览：技能按"你带什么进来"分成三大用户类（外加一个基础设施支撑层）：

| 分类 | 输入 | 入口 Skill | 用来 |
|---|---|---|---|
| **一、找机会** | 一个主题 | `chain-alpha-pipeline` | 把一个大主题变成可投公司 |
| **二、研究一只股票** | 一个股票代码 | `multi-agent-stock-analysis` | 从多个独立视角判断一家公司 |
| **三、日常与定期跟踪** | 一个日历 | `daily-us-market-scan` | 周期性复盘，适合设为定时任务 |

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
使用 InvestFlow 发现 AI 数据中心电力里的非共识公司
使用 InvestFlow 分析 HBM 产业链
```

如果插件没有出现，先确认这些文件存在：

- Codex：`plugins/invest-flow/.codex-plugin/plugin.json` 和 `.agents/plugins/marketplace.json`
- Claude Code：`plugins/invest-flow/.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`

## 首推工作流：chain-alpha 产业链选股

chain-alpha 是 InvestFlow 的旗舰工作流：把一个大主题转化为可投资的公司，并持续跟踪它们的营收是否真兑现。五个技能构成闭环，由 `chain-alpha-pipeline` 端到端编排：

```text
主题 ─▶ mismatch-discovery ─▶ monopoly-screen ─▶ verification ⇄ delivery-tracking
       行业定义+增长初筛       拆子环节+≤10候选     四档分级+定仓位    按季营收/利润
       +产业链全景+错位环节                                          兑现追踪
       └──────────────── 由 chain-alpha-pipeline 编排 ──────────────┘
```

一条命令跑完整漏斗：

```text
使用 invest-flow:chain-alpha-pipeline 分析具身智能（人形机器人）
```

漏斗纪律：行业定义与增长门槛 → 2-4 个错位环节 → 每环节 ≤10 候选 → top-6 进入验证 → 深挖 2-3 家。行业/关键环节收入增速必须 >20%、增长原因清楚、持续窗口至少 6 个月，才进入后续环节；最终仍必须落到可持续利润增速：≥30% 优先，20% 是最低放行线，<20% 筛掉。落在 `待验证` 的标的，用 `chain-alpha-delivery-tracking` 按季跟踪营收兑现，其升降档结论回灌 `chain-alpha-verification`。每一步也可单独运行——先用 `chain-alpha-mismatch-discovery` 低成本完成行业定义、增长门槛并确认错位环节，再决定是否跑完整流程。

## 技能分类

InvestFlow 的技能按"你带什么进来"分成三大用户类——主题、股票代码、还是日历——外加一个支撑性的基础设施层。

### 一、找机会（你带一个主题进来）

把一个大主题变成可投公司。`chain-alpha-pipeline` 是旗舰——见 [首推工作流：chain-alpha](#首推工作流chain-alpha-产业链选股)。

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `chain-alpha-pipeline` | 编排 chain-alpha 三步，步内 fan-out 到 subagent（Claude Code 原生并行；Codex 工具可用时并行；否则串行降级）并强制漏斗纪律。 | 想一次跑完"主题 → 公司"的完整流程。 |
| `chain-alpha-mismatch-discovery` | 行业白话定义 + 增长门槛与产业周期定位（四阶段时间表 + 当前节点）+ 产业链全景 + 供需错位环节发现。 | 有一个大主题，需要用白话搞懂行业到底是什么、处于哪个产业周期阶段、增速为何能维持高位、拆出整条产业链，并找到需求超过供给且能落到利润增速的错位环节。 |
| `chain-alpha-monopoly-screen` | 错位环节拆子环节 + 用 CR3/毛利/收入占比/利润增速硬门槛做垄断筛选。 | 已确认某个错位环节，需要找出其中最强的 ≤10 家公司。 |
| `chain-alpha-verification` | 100 分四档公司验证 + 利润增速硬门槛 + 基于回撤的仓位上限。 | 有候选公司，需要金池子/通过/待验证/剔除分级和仓位上限。 |
| `chain-alpha-delivery-tracking` | 对待验证标的做前瞻性营收/利润兑现追踪：5 级验证链 + 兑现窗口超时判死 + 增速/归因/动态估值引擎 + 格局哨兵 + 双向升降档。 | 持有待验证标的（如绿的谐波），需要按季判断营收和利润增速是否真兑现。（同时也是季度跟踪任务——见第三类。） |
| `ai-infrastructure-sector-discovery` | 每周扫描并评分 AI 基建板块，交接队列直接喂给 chain-alpha。 | 想每周确定最值得研究的 AI 基建方向。（同时也是每周跟踪任务——见第三类。） |
| `non-consensus-company-discovery` | 从主题到公司，发现高潜力非共识机会。 | 想寻找市场仍用旧框架定价的公司。 |

### 二、研究一只股票（你带一个股票代码进来）

从多个独立视角判断一家公司。`multi-agent-stock-analysis` 在一次会话里编排下面这些技能。

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `multi-agent-stock-analysis` | 在当前 agent 会话中编排下面的个股技能（公司画像 → 基本面 → 资金流 → 反身性 → Reportify → 非共识）。 | 想从多个独立视角交叉验证一只股票。 |
| `company-profile` | 生成投资分析前置公司画像。 | 用户第一次听说某家公司时，用于快速理解公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争对手和行业地位。 |
| `fundamental-analysis` | 做单股基本面、估值和技术面分析。 | 需要快速形成一家公司是否值得继续研究的结构化判断。 |
| `institutional-accumulation-analysis` | 分析机构吸筹、派发和资金行为。 | 想判断主力资金是在买入、出货还是对冲。 |
| `reflexivity-analysis` | 索罗斯反身性分析，含快扫（5 分钟阶段判断）和深度（完整周期）两档。 | 想快速判断叙事处于启动/强化/透支/反转，或做完整的叙事、价格、现实、反转风险拆解。 |
| `reportify-stock-analysis` | 生成标准化八段式个股报告，决策层含买方级三情景估值、可证伪假设、催化剂和跟踪 Dashboard。 | 需要可比较、可复盘、有证据链的正式投研报告。 |
| `earnings-report-analysis` | 从机构视角分析财报、指引、电话会和预期差。 | 公司刚发布财报，需要判断投资逻辑是否改变。 |

### 三、日常与定期跟踪（你带一个日历进来）

适合设为定时任务的周期性复盘。

| 技能 | 频率 | 用途 |
|---|---|---|
| `daily-us-market-scan` | 每日（美股收盘后） | 生成中文美股收盘复盘和次日计划，结论先行、有长度预算、板块/主题动态排序 + 新动态雷达。 |
| `ai-infrastructure-sector-discovery` | 每周 | 扫描 AI 基建板块，交接队列喂给 chain-alpha（同时列在第一类）。 |
| `index-pe-sensitivity` | 每周 / 按需 | 指数估值价格敏感性表（±涨跌 → TTM 整体法 P/E → N 年分位），单口径一致性护栏 + 周期盈利失真检查。 |
| `chain-alpha-delivery-tracking` | 每季 / 财报时 | 对待验证标的做营收/利润兑现追踪（同时列在第一类）。 |
| `gold-trend-analysis` | 月度 / 按需 | 分析黄金趋势、泡沫风险和宏观驱动。 |

### 基础设施（支撑层，本身不产投资观点）

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `market-data-router` | 路由行情数据并提供降级兜底。 | 其他研究流程需要 K 线、报价、期权背景或缓存市场数据。 |
| `output-report-index` | 为已生成报告构建 Markdown 和静态 HTML 索引页。 | 明确要求生成或更新 `output/` 下的报告索引。 |

## 在智能体内使用技能

在 Codex 或 Claude Code 智能体中用自然语言调用 InvestFlow。需要指定流程时，建议直接写出技能名称：

```text
使用 invest-flow:multi-agent-stock-analysis 分析 TSLA
使用 invest-flow:daily-us-market-scan 扫描今天的美股收盘
使用 invest-flow:non-consensus-company-discovery 发现 AI 数据中心电力里的非共识机会
使用 invest-flow:chain-alpha-pipeline 分析具身智能（人形机器人）产业链
使用 invest-flow:reflexivity-analysis 快扫 NVIDIA 当前叙事阶段
使用 invest-flow:earnings-report-analysis 解读 NVIDIA 最新财报
```

如果需要接入外部市场数据源，可从 `.env_example` 创建本地 `.env`，再填写相关密钥。

## 输出路径

报告和缓存文件会写入 `output/`：

| 流程 | 输出路径 |
|---|---|
| 公司画像 | `output/company-profile/` |
| 基本面分析 | `output/fundamental-analysis/` |
| 财报分析 | `output/earnings-report-analysis/` |
| AI 基建板块扫描 | `output/ai-infrastructure-sector-discovery/` |
| chain-alpha 错位发现 | `output/chain-alpha-mismatch-discovery/` |
| chain-alpha 垄断筛选 | `output/chain-alpha-monopoly-screen/` |
| chain-alpha 公司验证 | `output/chain-alpha-verification/` |
| chain-alpha 流程汇总 | `output/chain-alpha-pipeline/` |
| chain-alpha 营收兑现追踪 | `output/chain-alpha-delivery-tracking/` |
| 机构资金分析 | `output/institutional-accumulation-analysis/` |
| 非共识公司发现 | `output/non-consensus-company-discovery/` |
| 黄金分析 | `output/gold-analysis/` |
| 反身性分析 | `output/reflexivity-analysis/` |
| Reportify 个股报告 | `output/reportify-stock-analysis/` |
| 美股日报 | `output/daily-us-market-scan/` |
| 多智能体汇总报告 | `output/summary/` |
| 市场数据缓存 | `output/cache/market-data/` |

已有文件不应被覆盖。技能会在需要时追加 `(1)`、`(2)` 等后缀。

## 维护说明

- 这是仓库内置插件，不是远程市场包。
- 投资技能只维护在 `plugins/invest-flow/skills/`，两个平台共享同一份。
- Codex 插件发现元数据位于 `.agents/plugins/marketplace.json`，Claude Code 位于 `.claude-plugin/marketplace.json`。
- 插件打包信息变更时，需同步更新两个清单（`.codex-plugin/plugin.json` 和 `.claude-plugin/plugin.json`）并保持版本一致。
- README 中的技能名称应与 `plugins/invest-flow/skills/` 下的目录保持一致。
