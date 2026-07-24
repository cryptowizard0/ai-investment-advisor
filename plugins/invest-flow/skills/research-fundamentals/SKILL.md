---
name: research-fundamentals
description: "基础分析 (Fundamental Analysis) - 针对个股的深度基本面与技术面分析。涵盖行业定位、核心指标、财务估值、催化剂分析及技术面判断。适用于：(1) 个股基本面分析, (2) 生成投资研究报告, (3) 评估公司商业模式, (4) 结合技术面给出投资建议。生成综合分析报告并保存至 ./output/research/ 目录。"
---

# Fundamental Analysis (基础分析)

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

This skill enables Claude to act as a senior investment analyst, providing deep-dive reports on stocks and companies. It follows a structured workflow that integrates fundamental analysis, technical analysis, and strategic investment guidance.

**Output**: Markdown reports saved to `./output/research/`

## Workflow

To perform a high-quality investment analysis, follow these steps:

### 1. Identify the Target
- Determine the **Ticker Symbol** and **Company Name**.
- Identify the primary exchange and currency.

### 2. Data Gathering (Parallel Research)
Use search tools to gather the following context:
- **Company Profile**: Industry, business model, core products, and market positioning.
- **Financials (TTM & Latest Quarter)**: Revenue, Net Income, EPS, Profit Margins (Gross, Operating, Net), ROE/ROA.
- **Operational Metrics**: User growth, GMV, production capacity, or other sector-specific KPIs.
- **Valuation**: Current Market Cap, P/E, P/S, P/B, EV/Revenue.
- **Technical Data**: Current price, 52-week range, 50-day and 200-day Moving Averages, RSI(14), MACD.
- **News & Catalysts**: Recent earnings calls, product launches, regulatory changes, or macroeconomic impacts.

### 3. Analysis & Drafting
Use the provided template to structure the findings.
- **Template Location**: `references/report-template.md`
- Replace placeholders like `{{股票代码}}`, `{{公司名称}}`, `{{date}}`.
- Every generated report must include `作者：InvestmentFlow`.

### 4. Evaluation & Strategy
Synthesize the data into actionable insights:
- Define the **Stock Type** (Growth, Value, Cyclical, etc.).
- Provide specific **Trading** and **Investment Strategies** based on the combined fundamental/technical view.

### 5. Save Report
- **Output Directory**: `./output/research/`
- **Filename Format**: `research-fundamentals-{ticker}-{company-name}-{date}.md` (e.g., `research-fundamentals-AAPL-Apple-2026-01-28.md`)
- **Conflict Handling**: If a file with the same name exists, append a numbered suffix: `{ticker}-{company-name}-{date}(1).md`
- Ensure the output directory exists before saving (create if needed)
- Confirm to user with the actual saved path

## Guidelines

- **Objectivity**: Maintain a neutral, analytical tone. Highlight both risks and opportunities.
- **Data Freshness**: Always check for the latest available data (TTM and latest quarterly report).
- **Sector Context**: Adjust "Core Operating Metrics" based on the industry (e.g., IFP for Fintech, GMV for E-commerce, Delivery numbers for Auto).
- **Risk Assessment**: Don't just list metrics; interpret what they mean for the company's future.

## Resources

### references/
- **report-template.md**: The primary Markdown template for generating investment reports.
