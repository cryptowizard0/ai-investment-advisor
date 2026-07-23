---
name: monitor-index-valuation
description: "Use when you need an index valuation price-sensitivity table — how a ±X% index move maps the TTM P/E (整体法 aggregate caliber) onto its N-year percentile — with single-caliber (口径) consistency guardrails and cyclical-earnings distortion checks. Triggers: 指数估值敏感性分析, 分位数敏感性表, 纳指/科创50/沪深300 PE 分位, '指数再涨跌 X% 估值到历史什么位置', index PE percentile sensitivity."
---

# Index PE Sensitivity

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：估值口径优先交易所/指数公司官方与主流估值数据源，并全程保持单一口径。

## Overview

本 skill 生成一张「指数价格敏感性 × N 年估值分位」表，回答：**"如果指数再涨/跌 X%，估值会到历史什么位置？"**

方法：以指数 **TTM P/E（整体法 = Σ总市值 ÷ Σ滚动净利润）** 为基准，按价格档位（默认 ±5% / ±10%）线性传导到 P/E（盈利视为不变），再把每个 P/E 映射到 N 年历史经验分位；最后解读分位定位、上下不对称性、曲线陡峭/钝化，并做口径一致性与盈利周期失真检查。

默认口径：指数整体法；默认窗口：5 年。详见 `references/methodology.md`。

输出目录：`./output/monitor-index-valuation/`

## 运行频率与事件触发

- **固定频率**：每月执行一次完整指数估值敏感性更新。
- **补充触发**：指数自上次完整报告以来上涨或下跌至少 5%、指数成分发生调整、或成分股盈利口径/盈利周期出现足以改变 aggregate earnings caliber 的重大变化时，提前重跑。
- 补充更新必须沿用同一估值口径和历史窗口；若口径变化，必须明确标注并避免与旧分位直接比较。

## Trigger

在对话中使用：
- `/monitor-index-valuation <指数>`
- 示例：`使用 invest-flow:monitor-index-valuation 分析 科创50`
- 示例：`给纳斯达克100做一张估值敏感性/分位表`
- 示例：`沪深300 再跌 10% PE 到历史什么分位`

## Workflow

### 1) 锁定标的与口径
- 确认指数、代码、分析日期、分位窗口（默认 5 年）。
- **先锁口径**：基准 = 整体法 TTM P/E。A 股优先 Choice，取不到用同族整体法源（中证指数官方 / 理杏仁「市值加权」/ 乐咕乐股）并标注。
- 严禁使用 ETF 资料页口径或算术平均值口径（会失真且不可与整体法混比）。细则见 `references/methodology.md` 第 1 节。

### 2) 取当前值与历史分布
- 取截止日 **P/E₀（整体法）** 与其 **N 年经验分位**。
- 尽量取 **N 年历史序列**（逐日/逐周 P/E）以算真实经验分位；否则取分位锚点（min / 20% / 50% / 80% / max + 当前分位）做插值，并标注插值较粗略。
- 当前值、历史序列、分位必须同源同口径。

### 3) 生成敏感性表
- `新 P/E = P/E₀ × (1 + 价格档位)`；对每档映射到 N 年分位。
- 用脚本计算并生成报告骨架：
  - 序列法：`python plugins/invest-flow/skills/monitor-index-valuation/scripts/generate_report.py --index 科创50 --code 000688 --base 232.5 --series-file series.txt --source "理杏仁·整体法"`
  - 锚点法：`... --base 232.5 --anchors "36.31:0,43.26:20,83.91:50,159.29:80,232.51:98.07,263.72:100" --current-percentile 98.07`
- 文件命名：`monitor-index-valuation-{代码或指数}-{YYYY-MM-DD}.md`；重名自动追加 `(1)`、`(2)`。

### 4) 解读（必答三条）
- 当前分位定位（>90 极端偏高 / 70–90 偏高 / 30–70 中性 / <30 偏低）。
- 上下不对称性（上方是否很快触顶、下方是否快速释放）。
- 敏感度 / 曲线形态（价格每 ±5% 分位摆动几个点；陡峭 vs 钝化）。

### 5) 口径与失真检查
- 口径一致性复核（是否混源）。
- 盈利周期检查：成分盈利是否在周期底？若是，整体法 P/E 会被动抬高、分位钝化，需说明"高分位 ≠ 单纯贵"，并建议用等权 PE / PB / PS / forward PE 复核（同框架可换倍数复跑）。

## Output Requirements

- 语言：中文；财务与技术术语可保留 English。
- 必须包含：数据源与口径标注、分析日期、当前值与当前分位、敏感性表（含"较现在"分位变化）、三条解读、口径与失真检查、免责声明。
- 每个关键数字标注时间点与来源；无法确认时写"不确定"，不得编造。
- 全程单一口径；若不得不换口径或换窗口，必须显式说明，不得静默混用。
- 结尾注明：本报告为公开数据的客观呈现与统计定位，不构成投资建议。

## Resources

### scripts/
- `generate_report.py`: 计算敏感性表（价格扰动 → P/E → 分位，支持历史序列经验分位或锚点插值），渲染中文报告骨架，处理日期与重名。

### references/
- `methodology.md`: 口径铁律、计算步骤、解读要点、整体法失真检查、数据源速查。
- `report-template.md`: 标准中文 Markdown 报告模板。
