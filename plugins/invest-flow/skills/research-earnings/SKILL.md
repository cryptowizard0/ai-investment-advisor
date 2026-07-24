---
name: research-earnings
description: "机构视角财报解读 Skill。适用于用户要求解读公司财报、10-K/10-Q/年报/季报、earnings release、shareholder letter 或财报电话会，判断预期差、beat/miss 质量、guidance、现金流、估值重定价、反证条件和跟踪动作，并输出中文 Markdown 报告。"
---

# 财报解读

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于从机构投资者角度解读单家公司财报。目标不是复述财报数字，而是判断财报是否改变未来 6-24 个月盈利预期、估值中枢、市场叙事和投资动作。

默认输出目录：`./output/research/`

## Trigger

在对话中使用：
- `invest-flow:research-earnings`
- `使用 invest-flow:research-earnings 解读 NVDA 最新财报`
- `帮我从机构角度分析 Tesla Q1 earnings`
- `解读这份 10-Q / 10-K / 年报 / 季报 / earnings call`
- `这家公司财报 beat 但为什么股价跌？`

## Workflow

### 1) 识别分析对象和周期
- 提取 ticker、公司名、交易所、币种、财报周期、发布日期和分析日期。
- 若用户没有给财报周期，默认寻找最新已发布财报；无法确认时标记 `不确定`。
- 若用户给了持仓成本、投资期限、关注指标或原始财报链接，将其纳入结论和反证条件。

### 2) 收集可验证资料
- 优先使用公司 IR、earnings release、10-Q/10-K/20-F、shareholder letter、earnings call transcript、investor presentation 和交易所公告。
- 涉及最新财报、盘后股价、consensus estimate、guidance、管理层表述和市场反应时必须联网核验。
- 读取 `references/source-guide.md` 选择来源；无法核验的数据写 `数据暂缺` 或 `不确定`，不得编造。

### 3) 生成报告骨架
- 建议先运行：
  - `python plugins/invest-flow/skills/research-earnings/scripts/generate_report.py --ticker NVDA --company "NVIDIA" --period "FY2026 Q1"`
- 脚本会读取 `references/report-template.md`，生成不覆盖旧文件的 Markdown 骨架。
- 生成后必须补齐真实数据和来源，不要把占位符作为最终报告交付。

### 4) 按机构框架分析
- 使用 `references/methodology.md` 的框架，至少覆盖：
  - 预期差：actual vs consensus vs guidance vs buy-side whisper。
  - 三张表：利润表、资产负债表、现金流量表。
  - 质量：beat/miss 的来源、一次性因素、non-GAAP 调整、working capital。
  - guidance：下季度/全年收入、margin、capex、FCF 和关键 KPI。
  - 电话会：管理层语气、Q&A 压力点、口径变化和未回答问题。
  - 估值：未来 estimate revision、multiple 重定价和 bull/base/bear 情景。

### 5) 输出结论和跟踪计划
- 使用 `references/report-template.md` 的章节结构输出中文 Markdown 报告。
- 最终结论必须给出：正面 / 中性 / 负面，以及买入 / 观望 / 减持 / 卖出之一。
- 必须写清楚核心依据、可观察反证条件、下一次复盘触发点和跟踪 Dashboard。

## Quality Rules

- 使用中文；财务术语可保留 English，例如 EPS、FCF、RPO、ARR、gross margin、guidance。
- 明确区分事实、推断和假设。
- 不得把 headline beat 直接等同于高质量财报。
- 不得只看 EPS；必须同时看收入、margin、现金流、资产负债表和 guidance。
- 对每个关键数字标注时间点和来源；无法确认时标记 `不确定`。
- 对股价反应必须区分：盘前/盘后/次日、绝对涨跌和相对大盘/行业表现。
- 最终输出是研究判断，不是自动交易指令。

## Resources

### scripts/
- `generate_report.py`: 生成中文财报解读 Markdown 骨架，自动处理日期和重名文件。

### references/
- `methodology.md`: 机构视角财报解读框架、评分规则、常见陷阱和反证机制。
- `report-template.md`: 中文报告模板，覆盖结论、预期差、三张表、guidance、电话会、估值和 Dashboard。
- `source-guide.md`: 财报、电话会、共识预期、行情反应和估值数据的来源优先级。
