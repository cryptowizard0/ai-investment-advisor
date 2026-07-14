---
name: company-buyability-score
description: "Use when evaluating whether a US-listed company or ADR is buyable for a 6-24 month investment horizon, especially when AI exposure, quarterly growth, drawdown risk, sentiment mismatch, and negative factors need a quantified score."
---

# Company Buyability Score

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于判断一家公司“现在能不能买”。它不是自动交易系统，也不是深度估值报告，而是一个评分驱动的投资筛选流程：先量化 AI 受益度、产业链位置、壁垒、竞争格局、四季度增长、回撤风险和情绪错位，再用风险与负面因素做最终复核。

默认范围：US-listed equities/ADRs，默认投资周期：6-24 个月。

输出目录：`./output/company-buyability-score/`

## Trigger

在对话中使用：
- `/company-buyability-score <ticker>`
- 示例：`/company-buyability-score NVDA`
- 示例：`使用 invest-flow:company-buyability-score 判断 MRVL 能不能买`
- 示例：`给 TSM 做买入可行性评分`

## Workflow

### 1) 识别研究对象
- 提取公司、ticker、交易所、币种和分析日期。
- 若用户未给 ticker，先通过公开信息确认；无法确认时标记“不确定”。
- 默认分析 US-listed equities/ADRs 和 6-24 个月持有周期。

### 2) 收集可验证事实
- 优先使用公司 10-K、10-Q、20-F、annual report、Investor Relations、earnings release、earnings call transcript。
- 补充使用交易所/SEC 文件、主流金融数据源、行业资料、竞争对手材料和可信新闻。
- 所有关键数字必须标注时间点和来源；无法确认时写“不确定”，不得编造。

### 3) 按评分体系分析
- 使用 `references/scoring-methodology.md` 的 100 分体系。
- 每项必须给出：分数、满分、证据、推断链条、不确定性。
- 评分项包括：
  - AI 板块受益/受损
  - AI 产业链位置
  - 技术壁垒与优势
  - 垄断/竞争格局
  - 最近四个季度业绩增长
  - 最大回撤风险
  - 市场情绪错位

### 4) 风险与负面因素复核
- 最后单独分析风险与负面因素。
- 至少覆盖：估值、竞争、财务、客户集中、监管、技术替代、管理层执行、会计质量、叙事透支。
- 风险项不加分，只用于降级或否决；若触发降级，必须写明触发原因。

### 5) 套用模板并保存
- 建议先生成报告骨架：
  - `python plugins/invest-flow/skills/company-buyability-score/scripts/generate_report.py --ticker NVDA --company NVIDIA`
- 使用 `references/report-template.md` 填充全部章节。
- 文件命名：`company-buyability-score-{TICKER}-{YYYY-MM-DD}.md`
- 若重名，脚本会自动追加 `(1)`, `(2)`。
- 生成报告后补齐真实研究内容；不要保留未处理的占位符作为最终结论。

## Output Requirements

- 语言：中文；财务与技术术语可保留 English。
- 最终结论只能是：`买入候选 / 观察 / 回避`。
- 必须包含总分、分项评分表、硬性降级项、风险与负面因素、后续跟踪指标。
- 每个核心判断必须区分事实、推断、假设或不确定。
- 不能把“AI 叙事相关”直接等同于“AI 真实受益”；必须给出收入、客户、产品、capex 或战略证据。

## Resources

### scripts/
- `generate_report.py`: 生成买入可行性评分报告骨架，自动处理日期、ticker 校验和重名。

### references/
- `scoring-methodology.md`: 100 分评分体系、风险复核和硬性降级规则。
- `report-template.md`: 标准中文 Markdown 报告模板。
