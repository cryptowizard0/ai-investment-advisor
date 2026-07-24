---
name: research-profile
description: "公司画像 (Company Profile) - 为单个公司生成投资分析前置画像，覆盖公司简介、核心业务、收入来源、核心技术优势、产业链位置、AI 相关性、竞争格局和行业地位。适用于：(1) 用户第一次了解某家公司, (2) research-stock 的默认前置公司认知, (3) 投资判断前的业务与行业定位梳理。生成报告并保存至 ./output/research/ 目录。"
---

# Company Profile (公司画像)

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

This skill builds a company primer before investment analysis. It explains what the company does, how it makes money, where it sits in the industry chain, why it may have durable advantages, and who it competes with.

It does not issue buy, sell, or hold recommendations. Downstream skills handle valuation, trading, reflexivity, capital flow, and final decision synthesis.

**Output**: Markdown reports saved to `./output/research/`

## Workflow

### 1. Identify The Target

- Determine the ticker symbol.
- Determine the company name.
- Identify the main exchange, reporting currency, and primary sector when available.

### 2. Gather Current Company Context

Use current reliable sources where available:

- company investor relations pages
- latest annual report or 10-K
- latest quarterly report or 10-Q
- earnings presentation
- official product pages
- credible industry sources
- competitor investor materials

Separate facts, reasoned inference, and uncertainty. Do not treat market narrative as proven business exposure.

### 3. Build The Company Profile

Use `references/report-template.md` and cover:

- company overview
- core business and revenue structure
- customers and downstream demand
- core technology advantages and barriers
- industry-chain position
- AI value-chain relevance when evidence supports it
- competitors and industry position
- business model quality
- pre-analysis questions for downstream investment work
- data sources and uncertainty

### 4. AI Relevance Rules

Classify AI relevance as one of:

- `直接受益`
- `间接受益`
- `弱相关`
- `无明显相关`
- `不确定`

Only call a company AI-relevant when there is evidence from revenue exposure, customers, products, capex linkage, or disclosed strategy. If AI relevance is mainly market narrative, say so explicitly.

### 5. Save Report

- **Output Directory**: `./output/research/`
- **Filename Format**: `research-profile-{TICKER}-{YYYY-MM-DD}.md`
- **Conflict Handling**: If a file with the same name exists, append a numbered suffix: `research-profile-{TICKER}-{YYYY-MM-DD}(1).md`
- Ensure the output directory exists before saving.
- Every generated report must include `作者：InvestmentFlow`.
- Confirm to the user with the actual saved path.

## Handoff Fields

When this skill is used inside `research-stock`, preserve these fields for summary composition:

- `one_liner`
- `business_summary`
- `core_products`
- `revenue_model`
- `customers_and_end_markets`
- `technical_advantages`
- `moat_assessment`
- `industry_chain_position`
- `ai_relevance`
- `ai_value_chain_position`
- `competitors`
- `industry_position`
- `key_uncertainties`
- `pre_analysis_questions`
- `data_sources`

## Resources

### references/

- `report-template.md` - Company profile report template.
