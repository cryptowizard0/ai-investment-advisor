---
name: reportify-stock-analysis
description: "个股分析报告生成器。基于固定方法论（事实层到解释层到决策层）对股票进行结构化分析，并按八段式模板输出中文 Markdown 报告。适用于：(1) 用户要求分析单个股票, (2) 需要统一格式投研报告, (3) 需要把财务/技术/风险信息整合成可执行投资建议。支持输出到 ./output/reportify-stock-analysis/ 并自动处理重名文件。"
---

# Reportify Stock Analysis

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于产出“可比较、可复核”的个股分析报告。执行时必须同时满足：
- 使用 `references/methodology.md` 的分析方法。
- 使用 `references/report-template.md` 的章节结构与字段。

输出目录：`./output/reportify-stock-analysis/`

## Trigger

在对话中使用：
- `/reportify-stock-analysis <ticker>`
- 示例：`/reportify-stock-analysis TSLA`

## Workflow（可执行）

### 1) 识别输入
- 提取 `ticker`、公司名、分析日期。
- 若用户给了指定日期，使用用户日期；否则使用当前日期。

### 2) 收集与整理事实
- 公司信息：主营、行业、管理层、上市信息。
- 财务信息：最新季度 + 最新全年，覆盖收入/利润/现金流/资本开支。
- 市场与技术：股价区间、估值倍数、关键技术指标（至少 RSI）。
- 业务与区域：战略进展、区域市场表现。
- 风险信息：经营/竞争/转型/财务四类。

### 3) 方法论分析
- 严格按 `references/methodology.md` 的三层结构分析：
  - 事实层
  - 解释层
  - 决策层
- 决策层必须给出：
  - 一句话核心观点
  - 建议动作（持有/增持/减持/观望）
  - 触发条件
  - 失效条件
  - 复核时间

### 4) 套用模板并生成报告
- 按 `references/report-template.md` 填充全部章节。
- 不删除章节，仅允许在无法获取数据时标注“数据暂缺”。
- 核心数字必须带时间点与来源。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`

### 5) 落盘与重名处理
- 建议优先执行：
  - `python plugins/invest-flow/skills/reportify-stock-analysis/scripts/generate_report.py --ticker TSLA --company 特斯拉`
- 文件命名：`reportify-stock-analysis-{TICKER}-{YYYY-MM-DD}.md`
- 若重名，自动追加 `(1)`, `(2)`。

## Output Requirements

- 语言：中文（财务与技术术语保留英文）。
- 格式：Markdown。
- 必须包含：
  - 作者：InvestmentFlow
  - 八段式主体结构
  - `数据来源` 区块（可追溯）
  - `风险提示` 区块

## Resources

### scripts/
- `generate_report.py`: 生成模板化报告文件，自动处理日期和重名。

### references/
- `methodology.md`: 个股分析方法论（事实层 -> 解释层 -> 决策层）。
- `report-template.md`: 报告标准模板（八段式）。
