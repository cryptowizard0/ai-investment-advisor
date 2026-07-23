---
name: monitor-ai-infrastructure
description: "Use when discovering, ranking, or weekly-scanning AI infrastructure sectors, typically as a scheduled weekly tracking task. Use for AI infrastructure sector candidate pools, quantifiable sector indicators, discovery scores, threshold-based screening, and handoff queues that feed chain-alpha (chain-alpha-mismatch or chain-alpha) for deeper research."
---

# AI 基建板块发现

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 属于**日常市场跟踪类**，适合配置为每周定时任务，用于每周扫描 AI 基建候选板块，回答“这一周最值得研究哪些板块”。它不做公司深度研究，也不直接给买卖建议；它只输出可量化板块指标、`discovery_score`、触发阈值和后续深挖命令。**达标板块交接给 chain-alpha 工作流**（轻量确认用 `chain-alpha-mismatch`，完整“拆链 -> 找垄断 -> 验证定仓”用 `chain-alpha`）。

默认输出目录：`./output/monitor-ai-infrastructure/`

## 运行频率与事件触发

- **固定频率**：每周执行一次完整 AI 基建板块扫描。
- **补充触发**：hyperscaler capex 出现重大变化、AI 架构或产品路线发生实质调整、关键订单/backlog 明显变化、关键环节产能或扩产计划发生重大变化时，提前重跑。
- 补充扫描沿用同一评分与交接门槛；达标板块仍只交接给 `chain-alpha-mismatch` 或完整 `chain-alpha`。

## Trigger

在对话中使用：
- `/monitor-ai-infrastructure`
- `/monitor-ai-infrastructure 本周 AI 基建板块扫描`
- `每周扫描 AI 基建板块`
- `找下周最值得深挖的 AI 基建方向`
- `只看液冷、电力、光互联三类，做板块发现`

## Workflow

### 1) 确定扫描范围
- 若用户没有指定范围，默认扫描 `references/sector-taxonomy.md` 的固定种子板块。
- 同时允许从最新 AI 架构、产品路线图、订单、财报、产能、价格和行业新闻中动态新增候选板块。
- 若用户指定板块范围，只扫描指定板块，但仍使用同一指标体系。

### 2) 收集可量化指标
- 涉及 capex、订单、backlog、收入、毛利率、估值、股价、lead time、ASP、产能、良率、客户认证和产品路线图时，必须查询最新公开来源。
- 优先使用公司财报、Investor Relations、earnings call transcript、交易所公告、hyperscaler capex、供应商订单、权威行业数据和可信新闻。
- 每个关键指标必须带来源和日期；无法确认时标记 `数据暂缺`，不得主观补分。

### 3) 评分与排序
读取 `references/methodology.md`，为每个板块计算 `discovery_score`，满分 100：

| 模块 | 权重 |
|------|------|
| 架构变化强度 | 15 |
| 需求动量 | 20 |
| 单位用量弹性 | 15 |
| 供给约束 | 20 |
| 财务兑现 | 15 |
| 预期差 | 15 |
| 风险扣分 | -10 |

分类规则：
- `>= 80`：优先交给 chain-alpha 深挖。
- `70-79`：进入 chain-alpha 队列，若证据置信度中高则深挖。
- `55-69`：观察池，下周复核。
- `<55`：暂不深挖，除非出现强订单、价格、交期或财报异常。

### 4) 生成 chain-alpha handoff queue
- 所有 `discovery_score >= 70` 的板块进入 handoff queue。
- 每个进入队列的板块必须给出后续命令：轻量确认错位用 `chain-alpha-mismatch`，走完整漏斗用 `chain-alpha`。例如：
  - `使用 invest-flow:chain-alpha-mismatch 分析 CPO 光互联`
  - `使用 invest-flow:chain-alpha-mismatch 分析 AI 数据中心变压器`
  - `使用 invest-flow:chain-alpha 分析 液冷 CDU`
- 每个命令旁必须列出触发阈值和核心证据。

### 5) 输出并保存周报
- 使用 `references/report-template.md` 的结构输出中文 Markdown 周报。
- 输出目录：`./output/monitor-ai-infrastructure/`
- 文件名：`monitor-ai-infrastructure-{YYYY-MM-DD}.md`
- 若文件已存在，不要覆盖；追加 `(1)`, `(2)`, `(3)`。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`。

## Quality Rules

- 使用中文；财务、技术和市场术语可保留 English。
- 不得只按热点、涨幅或社交媒体热度排序。
- 必须用指标、阈值、证据日期和来源支撑每个板块的分数。
- 必须标记 `数据暂缺`，不能用主观判断补齐缺失数据。
- 必须区分“新增动态板块”和“固定种子板块”。
- 必须输出变化方向：上升 / 持平 / 下降 / 新增。
- 必须输出证据置信度：低 / 中 / 高。
- 只做板块发现和排序；环节与公司深研交给 chain-alpha 工作流（`chain-alpha-mismatch` / `chain-alpha`）。

## Resources

### references/sector-taxonomy.md
固定种子板块池，以及每个板块默认应跟踪的量化指标。

### references/methodology.md
板块发现评分模型、动态新增规则、阈值规则和 chain-alpha handoff 规则。

### references/report-template.md
每周 AI 基建板块发现中文 Markdown 周报模板。
