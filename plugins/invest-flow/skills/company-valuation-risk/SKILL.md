---
name: company-valuation-risk
description: "公司估值与风险分析（估值分位带）：四步串行——类型闸门（成长/现金牛/收费站可分析；周期/脉冲/资产困境排除）→ PE/PS 选尺子（四个 PE 失真条件任一触发换 PS；警戒线 PE>100 倍或 PS>40 倍重点提示不停止、读数降置信度；历史数据不足重点提示）→ 过去 5 年 TTM PE/PS 分位带（当前分位 + 10/20/25/50/60/75/80/90/95 重要分位）→ 潜在风险取「跌回 50% 分位」与「跌回重要参考点（默认 2026-03-31 上轮熊市低点）」两跌幅之大者，当前值低于参考点时重点提示。适用于：(1) 判断一只股票相对自己 5 年历史贵不贵、估值单杀能跌多少, (2) 为 chain-alpha-verification 的估值与透支度维度和最大回撤估值压缩情景提供输入, (3) 为 chain-alpha-delivery-tracking 引擎 C 预生成该股自身历史分位带。输出保存至 ./output/company-valuation-risk/。"
---

# 公司估值与风险分析

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：估值序列优先主流估值数据源（理杏仁 / 乌龟量化 / Choice / macrotrends / GuruFocus 等），全程同源同口径。

## Overview

本 skill 回答两个问题：**这家公司现在贵不贵（相对自己的历史）？如果估值均值回归，能跌多少、能涨多少？**

方法为四步串行，前一步不通过不进入后一步：

1. **类型闸门**：只分析 成长 / 现金牛 / 收费站 三类；周期 / 脉冲 / 资产困境 三类直接排除（分位法在这三类上系统性误导）。
2. **选尺子 PE or PS**：默认 PE；四个 PE 失真条件（5 年 TTM PE 中位数 >100、当前 TTM PE 为负、5 年内连续 ≥4 季净利润为负、重要参考点 TTM PE 为负）任一满足改用 PS。选定尺子后立即做两项检查：**警戒线**（当前 TTM PE >100 倍或 TTM PS >40 倍 → 重点提示、不停止：第 3-4 步照常输出，但结论区置顶警示、全部读数降置信度并建议先降敞口）；**历史数据不足**（上市较晚、分位样本覆盖不足 5 年 → 重点提示并全程降置信度，不停止）。
3. **分位带**：基于过去 5 年 TTM PE/PS 序列，输出当前分位数 + 重要分位数（10%、20%、25%、50%、60%、75%、80%、90%、95%）对应的尺子值。
4. **潜在风险与空间**：假设 TTM 分母不变，**潜在风险 = 两跌幅取大**——① 当前值跌回 50% 分位的跌幅；② 当前值跌回重要参考点（默认 2026-03-31，上轮熊市低点）尺子值的跌幅。当前值已低于参考点时**重点提示**（极端低估或参考点失效，需人工复核）。另输出 25%/10% 分位辅助压力情景、75%/90% 分位空间与双杀提示。

分位仅相对公司自身历史，不跨公司比较。细则见 `references/methodology.md`。

默认输出目录：`./output/company-valuation-risk/`

## Trigger

- `使用 invest-flow:company-valuation-risk 分析 NVDA 的估值与风险`
- `NVDA 现在贵不贵？跌回中位数要跌多少？`
- `这家公司该看 PE 还是 PS？现在处于历史什么分位？`
- 作为 `chain-alpha-verification`（估值与透支度、估值压缩情景）或 `chain-alpha-delivery-tracking`（引擎 C 分位带）的输入被调用

## Workflow

先读 `references/methodology.md`，再按以下步骤执行。全程区分 事实 / 推断 / 假设；关键数字标来源与日期；不得编造数据。

### 1) 类型闸门
- 按 methodology 第 1 节判定公司类型（成长 / 现金牛 / 收费站 / 周期 / 脉冲 / 资产困境），写一句话判定依据。
- 排除类型 → 用脚本生成"不适用"报告（附替代框架建议）并停止，不做后续步骤。

### 2) 选尺子（低成本先行）
- 先从估值数据源页面快速取四个条件读数：5 年 TTM PE 中位数、当前 TTM PE、5 年内最长连亏季数、重要参考点 TTM PE（默认 2026-03-31，上轮熊市低点，可用 `--ref-date`/`--ref-label` 更新）。
- 任一触发 → PS；否则 PE。定了尺子再收集该尺子的完整序列，避免两条序列都抓。
- **警戒线检查**：当前 TTM PE >100 倍或 TTM PS >40 倍 → 重点提示、不停止（脚本自动在结论区置顶警示并继续第 3-4 步，读数降置信度；阈值可用 `--pe-alert`/`--ps-alert` 调整但须说明理由）。
- 同时记录参考点的尺子值（PE 尺子 `--ref-pe`；PS 尺子补 `--ref-ps`），第 4 步潜在风险的参考点腿要用。

### 3) 取数
- 所选尺子的过去 5 年 TTM 序列（周频优先，同源同频）；上市不足 5 年用上市以来数据，**必须**用 `--data-span-years` 传入实际覆盖年数，脚本会重点提示降置信度。
- 拿不到完整序列时退而求其次用数据源的分位锚点（min/25%/50%/75%/max 等）走锚点插值模式。
- 当前价格用 yfinance / market-data-router。

### 4) 跑脚本生成报告
序列法：

```bash
python plugins/invest-flow/skills/company-valuation-risk/scripts/generate_report.py NVDA \
  --company "NVIDIA" --company-type 成长 --type-basis "数据中心收入与利润连续高增长，无周期/一次性标签" \
  --market 美股 --pe-file pe_5y.csv --current-price 181.40 \
  --max-loss-streak 0 --ref-pe 35.4 --source "macrotrends TTM PE 周频"
```

锚点法（只有分位锚点、无完整序列时）：

```bash
python plugins/invest-flow/skills/company-valuation-risk/scripts/generate_report.py 688017 \
  --company "绿的谐波" --company-type 成长 --market A股 \
  --metric ps --ps-anchors "8.5:0,12.3:25,16.8:50,24.5:75,41.2:100" --current-ps 28.6 \
  --ref-ps 10.2 --data-span-years 4.5 \
  --current-price 98.50 --current-percentile 82.0 --source "理杏仁 PS-TTM"
```

- 文件命名：`company-valuation-risk-{TICKER}-{YYYY-MM-DD}.md`；重名自动追加 `(1)`、`(2)`。

### 5) 解读并补齐
- 填写报告"解读"区（必答三条见 methodology 第 6 节）：当前定位与形态、风险承受判断、分位带失效条件。
- 补齐数据来源表（来源 + 日期 + 口径）。

## Quality Rules

- 中文输出；金融术语可保留 English。
- 类型闸门先于一切：排除类型不得进入分位分析，叙事和评分不能救回。
- 警戒线（PE >100 倍 / PS >40 倍）触发即重点提示（不停止）：分位与风险读数照常输出但全部降置信度，不得以成长性叙事弱化警示；报告须保留"先降敞口"的处置提示。
- 历史数据不足（分位样本 <5 年）必须重点提示并全程降置信度，不得静默按满窗口解读。
- 全程单一口径（TTM、同源、同频）；换口径或换窗口必须显式说明，不得静默混用。
- 分位仅相对自身历史；不得据此做跨公司贵贱比较。
- 潜在风险必须按"50% 分位腿 vs 参考点腿取大"口径输出；当前值低于参考点时必须重点提示，不得默认解读为便宜。
- 风险测算是"TTM 分母不变"的静态单杀假设，必须显式声明，并提示双杀情景。
- 关键数字标来源与日期；未确认条件标"未提供"，不得编造。
- 报告含固定作者字段 `InvestmentFlow`。
- 输出是研究与跟踪优先级，不是交易指令；结尾注明不构成投资建议。

## 与 chain-alpha 的衔接

- `chain-alpha-verification`：本 skill 的"回到 50% 分位（中位数）跌幅"可直接作为最大回撤推断的**估值压缩情景**输入；分位带与透支读数支撑"估值与透支度（20 分）"维度评分。
- `chain-alpha-delivery-tracking`：引擎 C 要求的"该股自身历史分位带（不看绝对值）"可由本 skill 预生成，PE/PS 双轨口径一致。
- 类型闸门与 chain-alpha 世界观一致：chain-alpha 找的正是利润高增长的成长标的；周期/脉冲/困境类在两边都被挡出。

## Resources

### scripts/
- `generate_report.py`: 执行类型闸门、四条件选尺子、分位带计算（序列经验分位或锚点插值）、分位回落隐含价格与风险读数，渲染中文报告骨架，处理重名。

### references/
- `methodology.md`: 类型闸门细则与失效机理、选尺子四条件口径、数据口径、分位计算方法、风险公式与解读要求。
- `report-template.md`: 标准中文 Markdown 报告模板（结论 / 闸门 / 尺子 / 分位风险表 / 读数 / 解读 / 数据来源）。
