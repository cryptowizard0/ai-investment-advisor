---
name: non-consensus-company-discovery
description: "发现和评估高潜力非共识公司。适用于从一个大趋势、主题或产业链出发，筛选 US-listed equities/ADRs 或用户指定市场中的 20-50 家候选公司，用 100 分模型识别市场误解、产业链瓶颈、利润弹性、财务拐点和 6-24 个月催化剂，并输出中文深度研究报告、Top 1-3 跟踪标的、反证条件和跟踪 Dashboard。"
---

# 非共识公司发现

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于从大趋势或产业链主题中发现高潜力非共识公司。目标不是寻找没人知道的公司，而是寻找市场已经看到表面事实、但低估该事实未来会演化成利润、现金流或战略地位的公司。

默认股票池：`US-listed equities/ADRs`。若用户指定市场、地区、行业、排除清单或候选公司，优先使用用户范围。

默认输出目录：`./output/non-consensus-company-discovery/`

## Trigger

在对话中使用：
- `invest-flow:non-consensus-company-discovery`
- `使用 invest-flow:non-consensus-company-discovery 发现 AI 数据中心电力里的非共识公司`
- `帮我找机器人产业链里有潜力的非共识公司`
- `Use InvestFlow to find non-consensus companies in robotics infrastructure.`
- `从先进封装主题里筛 1-3 个非共识机会`

## Workflow

### 1) 明确主题和默认范围
- 提取主题、市场范围、投资期限、排除行业、候选公司和用户偏好。
- 用户未指定市场时，默认使用 `US-listed equities/ADRs`。
- 用户未指定 Top N 时，默认最终保留 `1-3` 家重点跟踪公司。

### 2) 构建主题与产业链地图
- 先判断 3-5 年大趋势是否足够大，再拆分产业链：上游材料/设备、核心零部件、系统集成、平台/软件、终端客户、服务/运维。
- 逐层寻找最稀缺、扩产最慢、客户迁移成本最高、技术壁垒最高、毛利率最可能上升的环节。
- 初始候选池目标为 20-50 家公司；若数据不足，明确说明候选池不足的原因。

### 3) 识别共识盲区
- 对每家公司写清楚：
  - 市场认为它是什么。
  - 市场担心什么。
  - 市场为什么给低估值或旧估值体系。
  - 市场忽略的变量是什么。
  - 未来 1-3 年最可能改变市场看法的变量是什么。
- 优先识别错误分类、低估经营杠杆、低估供给约束、高估竞争风险、低估客户迁移成本和忽略第二增长曲线。

### 4) 收集证据并评分
- 读取 `references/methodology.md`，使用 100 分模型评分。
- 涉及财报、订单、backlog、收入、毛利率、估值、股价、招聘、专利、客户验证、技术路线和行业供需时，必须查询最新公开来源。
- 关键数字必须标注来源和日期；无法确认时标记 `数据暂缺` 或 `不确定`，不得编造。

### 5) 深挖 Top 1-3 公司
- 对最高分公司写深度卡片：非共识假设、利润转化路径、财务验证指标、未来 3 个催化剂、主要风险、反证条件、合理估值区间和仓位计划。
- 非共识必须落到财务路径：收入从哪里来、毛利率如何变化、客户是谁、竞争对手是谁、规模化后利润率是多少、何时进入财报。
- 没有明确 6-24 个月验证点的公司只能进入观察池，不能列为重点跟踪。

### 6) 生成并保存报告
- 使用 `references/report-template.md` 输出中文 Markdown 深度报告。
- 建议先生成报告骨架：
  - `python plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py --theme "AI 数据中心电力"`
- 文件命名：`non-consensus-company-discovery-{theme}-{YYYY-MM-DD}.md`
- 若文件已存在，脚本会自动追加 `(1)`, `(2)`。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`。

## Scoring

总分 100：

| 模块 | 权重 |
|---|---:|
| 趋势强度 | 15 |
| 产业链瓶颈位置 | 20 |
| 利润弹性/财务拐点 | 20 |
| 市场误解/共识盲区 | 20 |
| 6-24 个月催化剂确定性 | 15 |
| 估值拥挤度/安全边际 | 10 |

分类：
- `>=80`：重点跟踪。
- `70-79`：深度研究。
- `60-69`：观察池。
- `<60`：剔除，除非出现新的强催化剂。

## Quality Rules

- 使用中文；财务、技术和市场术语可保留 English。
- 必须区分事实、推断和假设。
- 不得把冷门、低估值或故事性强直接等同于非共识机会。
- 不得只按涨幅、媒体热度或社交媒体讨论排序。
- 每个 Top 候选必须有可观察、可复盘、可反证的假设。
- 明确说明短期问题是周期性噪音还是结构性衰退。
- 最终输出是研究和跟踪优先级，不是自动交易指令。

## Resources

### references/methodology.md
完整非共识发现框架、评分细则、漏斗流程、反证机制和常见陷阱。

### references/report-template.md
中文深度报告模板，覆盖主题地图、产业链地图、候选池、评分、Top 1-3 深挖、催化剂、反证条件、Dashboard 和数据来源。

### references/source-guide.md
数据源优先级和交叉验证规则，覆盖财报、电话会、产业链验证、招聘、专利、开发者生态、客户评价和估值数据。
