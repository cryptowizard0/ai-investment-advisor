---
name: industry-chain-analysis
description: Use when the user asks to analyze an industry chain, upstream/downstream structure, supply chain, value chain, bottleneck, critical component, hidden supplier, or module-level constraints in any sector. Use for two-layer industry mapping, bottleneck discovery, and evidence-backed Chinese research outputs.
---

# 产业链两层分析

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 只做产业链分析，不做完整估值、不直接给买卖建议。目标是把一个产业从“上游/中游/下游”的粗颗粒度，拆到能独立影响产能、良率、成本、交期、认证或利润分配的最小瓶颈节点。

默认输出目录：`./output/industry-chain-analysis/`

## Trigger

适用于：
- `拆解 AI 产业链`
- `分析 HBM 供应链瓶颈`
- `某个行业上下游怎么拆`
- `找某条产业链里的隐形瓶颈/金铲子`
- `把某个模块继续拆细，比如 CoWoS 封装材料`

如果用户要求公司估值、仓位或买卖建议，应先完成本 skill 的产业链结论，再转交其他投资分析 skill。

## Core Rule

产业链分析必须分两层输出：

1. **第一层：产业全景图**  
   从终端需求倒推上游、中游、下游和生态支撑，识别每个一级模块的需求来源、价值池、供给弹性、代表公司和跟踪指标。

2. **第二层：模块下钻图**  
   对关键一级模块继续拆到产品/子系统、工艺步骤、关键材料、关键设备、技术参数、良率变量、供应商格局、认证周期和财务传导。

不能只停在品类名。若某个二级节点能独立影响产能、良率、成本、交期、客户认证或利润率，就必须单独拆出来。

## Workflow

### 1) 定义边界
- 明确产业、地区、时间窗口和分析目的。
- 如果用户没指定，默认全球视角，中美重点，时间窗口 6-24 个月。
- 明确分析对象是整条产业链、某个一级模块，还是某个二级瓶颈。

### 2) 收集证据
- 涉及产能、订单、价格、财务、技术路线、客户认证、政策或新闻时，必须查最新公开来源。
- 优先使用公司财报、Investor Relations、earnings call、交易所公告、客户/供应商披露、行业协会、监管文件和权威数据。
- 区分 `事实 / 推断 / 假设`，无法确认的数据标为“不确定”。

### 3) 第一层：产业全景
读取 `references/methodology.md`，先画一级模块，不得直接跳到公司名单。

必须覆盖：
- 终端需求和预算来源。
- 上游、中游、下游和生态支撑。
- 每个一级模块的价值池、供给弹性、议价权、代表公司、关键跟踪指标。
- 需求如何从下游传导到上游。

### 4) 第二层：模块下钻
选择最关键的 3-8 个一级模块做下钻。优先选择：
- 供给扩不快的模块。
- 毛利率或 ASP 可能变化的模块。
- 客户替换成本高的模块。
- 良率、可靠性、认证周期决定交付的模块。
- 市场只看到一级品类、但没看到二级瓶颈的模块。

每个模块必须拆到：
- 产品/子系统。
- 工艺步骤。
- 关键材料。
- 关键设备。
- 技术/良率参数。
- 供应商格局。
- 客户认证/扩产周期。
- 财务传导。

### 5) 识别最小瓶颈节点
输出 3 类结论：
- **真瓶颈**：需求非线性增长，供给扩张慢，替代少，已有价格/订单/交期/良率证据。
- **高景气节点**：需求强，但供给可扩张或竞争较多。
- **待验证节点**：逻辑成立，但缺少订单、价格、产能、良率或客户验证数据。

### 6) 输出报告
- 使用 `references/report-template.md` 的结构输出中文 Markdown。
- 只给产业链研究结论、优先级、跟踪指标和反证条件。
- 若生成完整报告，保存到 `./output/industry-chain-analysis/industry-chain-analysis-{主题}-{YYYY-MM-DD}.md`。
- 若文件已存在，不要覆盖；追加 `(1)`, `(2)`, `(3)`。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`。

## Quality Rules

- 中文输出；金融、技术和制造术语可保留 English。
- 不允许只列“上游/中游/下游”而没有第二层模块下钻。
- 不允许只列公司名单；公司必须绑定到具体模块、产品、工艺或材料。
- 不允许把“大需求”直接等同于“好机会”；必须验证供给约束和利润留存。
- 对 AI、半导体、先进制造、能源设备等复杂产业，必须拆到材料、设备、工艺、良率和认证周期。
- 如果无法定位到二级瓶颈，结论必须写“仍需下钻验证”。

## Resources

### references/methodology.md
两层产业链拆解方法，包含第一层全景字段、第二层下钻字段、最小瓶颈节点标准和常见行业下钻示例。

### references/report-template.md
固定中文 Markdown 报告模板，包含产业边界、一级全景、二级下钻、最小瓶颈节点、公司映射、跟踪指标、反证条件和数据来源。
