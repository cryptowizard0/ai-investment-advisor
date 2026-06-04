# InvestFlow

[英文版本](README.md)

InvestFlow 是一个仓库内置的 Codex 投资研究插件。它把市场扫描、产业链研究、非共识发现、个股分析、买入可行性评分、财报解读、反身性分析和市场数据路由封装成可复用的技能。

标准插件包位于 `plugins/invest-flow/`。所有打包技能位于 `plugins/invest-flow/skills/`。

## 快速上手

1. 在 Codex 中打开这个仓库。
2. 重新加载 Codex，让它读取 `.agents/plugins/marketplace.json`。
3. 在本地插件市场安装 `InvestFlow`。
4. 在 Codex 对话中直接调用技能。

示例：

```text
使用 InvestFlow 分析 TSLA
使用 InvestFlow 生成今天的美股收盘复盘
使用 InvestFlow 发现 AI 数据中心电力里的非共识公司
使用 InvestFlow 分析 HBM 产业链
```

如果插件没有出现，先确认这些文件存在：

- `plugins/invest-flow/.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

## 推荐工作流

| 目标 | 推荐流程 |
|---|---|
| 发现 AI 基建机会 | 先用 `ai-infrastructure-sector-discovery` 扫描板块，再用 `ai-infrastructure-scarcity-radar` 深挖最强稀缺主题。 |
| 从产业链找到非共识标的 | 先用 `industry-chain-analysis` 拆产业链和瓶颈，再用 `non-consensus-company-discovery` 分析最有潜力的环节或模块。 |
| 每日市场复盘 | 美股收盘后使用 `daily-us-market-scan`。 |
| 跟踪叙事和反身性风险 | 定期用 `reflexivity-quick-scan` 判断阶段；当阶段变化或仓位较重时升级到 `reflexivity-deep-analysis`。 |
| 快速研究单只股票 | 用 `multi-agent-stock-analysis` 先生成 `company-profile` 公司画像，再交叉验证基本面、资金流、GIE、反身性、Reportify 和非共识视角。 |
| 解读财报 | 公司发布财报后用 `earnings-report-analysis` 判断预期差，再更新个股投资判断。 |
| 判断股票能不能买 | 用 `company-buyability-score` 量化 AI 受益、产业链位置、增长、回撤、情绪错位和风险负面因素。 |
| 生成正式个股报告 | 用 `professional-investment-analyst` 生成买方研究风格报告，或用 `reportify-stock-analysis` 生成标准化结构报告。 |
| 获取市场数据 | 当其他研究流程需要行情、期权或缓存数据时，使用 `market-data-router`。 |

## 技能列表

| 技能 | 用途 | 适用场景 |
|---|---|---|
| `ai-infrastructure-sector-discovery` | 扫描并评分 AI 基建板块。 | 想找下一步最值得研究的 AI 基建方向。 |
| `ai-infrastructure-scarcity-radar` | 深挖 AI 基建稀缺环节和瓶颈。 | 已经锁定主题，需要判断稀缺是否真实且可投资。 |
| `company-profile` | 生成投资分析前置公司画像。 | 用户第一次听说某家公司时，用于快速理解公司简介、核心业务、技术壁垒、产业链位置、AI 相关性、竞争对手和行业地位。 |
| `company-buyability-score` | 对美股或 ADR 生成买入可行性量化评分。 | 需要判断一家公司能不能买，并同时检查 AI 受益、产业链位置、增长、回撤、情绪错位和负面因素。 |
| `daily-us-market-scan` | 生成中文美股收盘复盘和次日计划。 | 想每日跟踪指数、板块、主题、市场宽度、财报和观察名单。 |
| `earnings-report-analysis` | 从机构视角分析财报、指引、电话会和预期差。 | 公司刚发布财报，需要判断投资逻辑是否改变。 |
| `fundamental-analysis` | 做单股基本面、估值和技术面分析。 | 需要快速形成一家公司是否值得继续研究的结构化判断。 |
| `gie-investment-framework` | 用 GIE 框架寻找 1-3 年“金铲子”机会。 | 想验证公司或行业是否受益于长期瓶颈和供需错配。 |
| `gold-trend-analysis` | 分析黄金趋势、泡沫风险和宏观驱动。 | 研究黄金价格、宏观风险或黄金交易框架。 |
| `industry-chain-analysis` | 做两层产业链和瓶颈拆解。 | 需要看清上游、中游、下游和模块级约束。 |
| `institutional-accumulation-analysis` | 分析机构吸筹、派发和资金行为。 | 想判断主力资金是在买入、出货还是对冲。 |
| `market-data-router` | 路由行情数据并提供降级兜底。 | 研究流程需要 K 线、报价、期权背景或缓存市场数据。 |
| `multi-agent-stock-analysis` | 在 Codex 会话中编排多个个股分析技能。 | 想从多个独立视角交叉验证一只股票。 |
| `non-consensus-company-discovery` | 从主题到公司，发现高潜力非共识机会。 | 想寻找市场仍用旧框架定价的公司。 |
| `professional-investment-analyst` | 生成买方研究风格的个股报告。 | 需要可跟踪、可复盘、有证据链的正式报告。 |
| `reflexivity-deep-analysis` | 做完整反身性周期分析。 | 需要拆解叙事、价格、现实验证、边际变化和反转风险。 |
| `reflexivity-quick-scan` | 快速判断反身性阶段。 | 想快速判断叙事处于启动、强化、透支还是反转。 |
| `reportify-stock-analysis` | 生成标准化结构化个股报告。 | 需要稳定的事实、解释、决策和风险输出格式。 |

## 在智能体内使用技能

在 Codex 智能体中用自然语言调用 InvestFlow。需要指定流程时，建议直接写出技能名称：

```text
使用 invest-flow:multi-agent-stock-analysis 分析 TSLA
使用 invest-flow:daily-us-market-scan 扫描今天的美股收盘
使用 invest-flow:industry-chain-analysis 拆解 HBM 产业链
使用 invest-flow:non-consensus-company-discovery 发现 AI 数据中心电力里的非共识机会
使用 invest-flow:reflexivity-quick-scan 判断 NVIDIA 当前叙事阶段
使用 invest-flow:company-buyability-score 判断 NVIDIA 能不能买
使用 invest-flow:earnings-report-analysis 解读 NVIDIA 最新财报
```

如果需要接入外部市场数据源，可从 `.env_example` 创建本地 `.env`，再填写相关密钥。

## 输出路径

报告和缓存文件会写入 `output/`：

| 流程 | 输出路径 |
|---|---|
| 公司画像 | `output/company-profile/` |
| 买入可行性评分 | `output/company-buyability-score/` |
| 基本面分析 | `output/fundamental-analysis/` |
| 财报分析 | `output/earnings-report-analysis/` |
| AI 基建板块扫描 | `output/ai-infrastructure-sector-discovery/` |
| AI 基建稀缺分析 | `output/ai-infrastructure-scarcity-radar/` |
| 产业链分析 | `output/industry-chain-analysis/` |
| 机构资金分析 | `output/institutional-accumulation-analysis/` |
| GIE 框架分析 | `output/gie-investment-framework/` |
| 非共识公司发现 | `output/non-consensus-company-discovery/` |
| 黄金分析 | `output/gold-analysis/` |
| 反身性快速扫描 | `output/reflexivity-quick-scan/` |
| 反身性深度分析 | `output/reflexivity-deep-analysis/` |
| 专业投资分析师报告 | `output/professional-investment-analyst/` |
| Reportify 个股报告 | `output/reportify-stock-analysis/` |
| 美股日报 | `output/daily-us-market-scan/` |
| 多智能体汇总报告 | `output/summary/` |
| 市场数据缓存 | `output/cache/market-data/` |

已有文件不应被覆盖。技能会在需要时追加 `(1)`、`(2)` 等后缀。

## 维护说明

- 这是仓库内置插件，不是远程市场包。
- 投资技能只维护在 `plugins/invest-flow/skills/`。
- 插件发现元数据位于 `.agents/plugins/marketplace.json`。
- README 中的技能名称应与 `plugins/invest-flow/skills/` 下的目录保持一致。
