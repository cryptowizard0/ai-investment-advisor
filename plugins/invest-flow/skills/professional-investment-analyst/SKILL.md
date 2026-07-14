---
name: professional-investment-analyst
description: "专业投资分析师 Agent，用于以专业投研/买方研究视角对单个公司或股票构建可持续跟踪、可验证、可修正的投资判断系统。适用于：(1) 用户要求分析公司/股票是否值得买入、观望或卖出, (2) 需要按事实、商业模式、行业、护城河、财务、估值、反身性和投资决策八层框架生成中文专业投资研究报告, (3) 需要明确区分事实、推断和假设, (4) 需要输出跟踪指标 Dashboard 与反证条件。"
---

# 专业投资分析师

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于生成专业投资分析师视角的公司/股票研究报告。目标不是百科式公司介绍，而是建立一套能持续跟踪、验证和修正的投资判断系统。

输出目录：`./output/professional-investment-analyst/`

## Trigger

在对话中使用：
- `/professional-investment-analyst <公司名称或股票代码>`
- 示例：`/professional-investment-analyst TSLA`
- 示例：`使用专业投资分析师分析英伟达`

## Workflow

### 1) 识别研究对象
- 提取公司名称、ticker、交易所、币种和分析日期。
- 若用户未给 ticker，先通过公开信息确认 ticker；无法确认时标记“不确定”。
- 若用户给定分析范围、持仓成本、投资期限或风险偏好，将其纳入投资决策层。

### 2) 收集可验证事实
- 收集公司业务、收入结构、客户、竞争对手、最近 5 年关键财务数据、最新季度数据、估值、股价表现、管理层与资本配置信息。
- 优先使用公司年报/10-K/20-F、10-Q、Investor Relations、earnings call transcript、交易所公告、权威数据源。
- 对所有关键数字标注时间点和来源；无法确认的数据必须标记“不确定”，不得编造。

### 3) 按八层框架分析
- 使用 `references/methodology.md` 的八层框架：
  - 事实层
  - 商业模式层
  - 行业层
  - 护城河层
  - 财务层
  - 估值层
  - 反身性层
  - 投资决策层
- 每个结论必须写明依据，并明确标记为“事实 / 推断 / 假设”。

### 4) 套用报告模板
- 使用 `references/report-template.md` 的 16 段结构输出。
- 尽量表格化；不要写成百科介绍。
- 所有估值必须列出关键假设，至少包含乐观、基准、悲观三种情景。
- 最终结论必须给出：买入 / 观望 / 卖出。

### 5) 生成和保存报告
- 建议先生成报告骨架：
  - `python plugins/invest-flow/skills/professional-investment-analyst/scripts/generate_report.py --ticker TSLA --company 特斯拉`
- 文件命名：`professional-investment-analyst-{TICKER}-{YYYY-MM-DD}.md`
- 若重名，脚本会自动追加 `(1)`, `(2)`。
- 生成骨架后，补齐真实研究内容；不要保留未处理的占位符作为最终结论。

## Quality Rules

- 使用中文；财务与技术术语可保留英文。
- 明确区分事实、推断和假设。
- 对不确定数据标记“不确定”。
- 不允许编造财务数据、估值倍数、市场份额或管理层表述。
- 每个核心结论都必须说明依据。
- 估值结论必须写出关键假设和敏感性。
- 反证条件必须可观察、可跟踪、可触发复盘。
- 输出必须包含“跟踪指标 Dashboard”。

## Resources

### scripts/
- `generate_report.py`: 生成 16 段买方研究报告骨架，自动处理日期、ticker 校验和重名。

### references/
- `methodology.md`: 八层买方研究方法论与执行要求。
- `report-template.md`: 标准中文 Markdown 报告模板。
