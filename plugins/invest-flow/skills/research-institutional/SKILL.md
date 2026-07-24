---
name: research-institutional
description: "机构吸筹派发分析 (Institutional Accumulation & Distribution Analysis) - 通过量价分析、技术指标背离、盘口微观结构和期权链异动识别主力资金意图。适用于：(1) 判断股票主力是在吸筹还是派发, (2) 识别机构Whales的隐藏交易行为, (3) 预测潜在的价格转折点, (4) 制定基于资金流向的交易策略。"
---

# Institutional Accumulation & Distribution Analysis

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

This skill transforms Claude into a senior quantitative trader with 20 years of experience in identifying institutional (Whale) accumulation and distribution patterns through subtle "unnatural fluctuations" in price action and volume.

## Workflow

To perform institutional accumulation/distribution analysis, follow these steps:

### 1. Identify Target & Timeframe
- Determine the **Ticker Symbol** (e.g., TSLA, AAPL)
- Specify the **Analysis Period** (e.g., 1 month, 3 months, 6 months)

### 2. Data Gathering (Parallel Research)

Gather the following market data:

**优先数据源（推荐）**
- 若存在 `market-data-router` skill，则优先使用其输出数据：
  - Bars（支持 `5m/1h/1d/auto`）、L1、期权、暗池（美股优先）
  - 输出格式参考：`../market-data-router/references/field-schema.md`
  - 使用脚本：`../market-data-router/scripts/fetch_market_data.py`
  - **数据输出路径固定为：** `./output/cache/market-data/`
  - **文件命名规则：** `mdr-{market}-{symbol}-{interval}-{start}-{end}.json`
    - `market`：US/HK/CN/FUT
    - `symbol`：原始标的代码
    - `interval`：5m/1h/1d/auto（auto 需写最终选择的粒度）
    - `start/end`：`YYYYMMDD`（若缺省则用实际请求的时间范围）
  - **缓存读取规则：** 若上述文件已存在，则直接读取该文件作为输入，不再发起数据请求
  - 若数据缺失，按 `market-data-router` 的 `quality_flags` 进行降级或标注（含 `aggregated_from_5m`）

**回退数据源（保持原流程）**
- 若未安装 `market-data-router`，或该数据源不可用，则**保持原有 web 搜索/数据抓取流程不变**。

**Price & Volume Data:**
- Daily OHLCV (Open, High, Low, Close, Volume) for the specified period
- Key support/resistance levels
- Volume profile at different price levels

**Technical Indicators:**
- OBV (On-Balance Volume) trend
- CMF (Chaikin Money Flow) values
- VWAP (Volume Weighted Average Price) and deviation
- RSI and MACD for divergence confirmation

**Options Flow (if available):**
- Unusual options volume (calls vs puts)
- Implied volatility skew
- Large block trades / sweeps

**Market Microstructure:**
- Dark pool volume levels
- Level 2 order book depth (if intraday)
- Institutional holdings changes (13F filings)

### 3. Analysis Framework

Apply the four-dimensional analysis framework:

#### Dimension 1: Volume Spread Analysis (VSA)
- **Distribution Signals:**
  - High volume + minimal price progress (stalling)
  - Shooting star patterns at highs
  - Wide spread bars on high volume with poor close

- **Accumulation Signals:**
  - Low volume pullback + high volume breakout
  - Spring patterns (false breakdown)
  - Volatility Contraction Pattern (VCP) at support

#### Dimension 2: Technical Indicator Divergence
- **OBV Analysis:**
  - Bullish divergence: Price makes lower low, OBV makes higher low (accumulation)
  - Bearish divergence: Price makes higher high, OBV makes lower high (distribution)

- **CMF Analysis:**
  - Above 0: Buying pressure dominant
  - Below 0: Selling pressure dominant
  - Trend direction indicates flow strength

- **VWAP Analysis:**
  - Price above VWAP: Bullish institutional sentiment
  - Price below VWAP: Bearish institutional sentiment
  - Bounces off VWAP: Potential support/resistance

#### Dimension 3: Market Microstructure
- **Iceberg Orders:**
  - Small prints consistently executing without price movement
  - Large block trades reported after hours

- **Dark Pool Activity:**
  - High dark pool percentage >40% suggests institutional activity
  - Premium/discount to lit markets indicates urgency

#### Dimension 4: Options Flow
- **Call Sweeps:**
  - Large call purchases above ask (bullish urgency)
  - Out-of-the-money call accumulation

- **Put/Call Ratio:**
  - Extreme readings indicate sentiment extremes
  - Unusual put buying may indicate hedging or bearish bets

- **IV Skew:**
  - Call skew: Bullish expectations
  - Put skew: Bearish expectations

### 4. Synthesis & Diagnosis (Scoring Card System)

**重要**: 使用评分卡量化系统 (详见 `references/scoring-system.md`) 确保分析结论的客观性和一致性。

#### 评分卡计算流程

**Step 1: 四维评分** (每维度满分 ±25 分)
- **VSA 量价分析**: 吸筹信号 (+) / 派发信号 (-)
- **技术指标背离**: OBV + CMF + VWAP + RSI
- **盘口微观结构**: 暗池 + 大宗 + 冰山订单
- **期权链异动**: Call + Put + P/C比 + IV Skew

**Step 2: 总分计算**
```
总分 = VSA分 + 技术分 + 盘口分 + 期权分  (范围: -100 ~ +100)
```

**Step 3: 确定性分类** (基于总分区间)

| 分类 | 总分区间 | 必要条件 | 标记 |
|------|---------|---------|------|
| **强力吸筹** | +75 ~ +100 | (VSA ≥ +10 且 技术 ≥ +5) 或 (VSA ≥ +5 且 技术 ≥ +10) | 🔴 强力吸筹 |
| **温和吸筹** | +50 ~ +74 | VSA ≥ +5 或 技术 ≥ +5 或 任一维度 ≥ +20 | 🟡 温和吸筹 |
| **观望/中性** | -49 ~ +49 | 无明显方向信号 | ⚪ 观望 |
| **派发初级** | -74 ~ -50 | VSA ≤ -5 或 技术 ≤ -5 或 任一维度 ≤ -20 | 🟠 派发初级 |
| **疯狂出货** | -100 ~ -75 | (VSA ≤ -10 且 技术 ≤ -5) 或 (VSA ≤ -5 且 技术 ≤ -10) | 🔴 疯狂出货 |

**Step 4: 置信度计算**
```
置信度 = (50% + 证据加成 + 强度加成 + 完整性加成) × 调整系数
范围: 30% - 95%
```

#### 关键判定标准 (快速参考)

**吸筹必备条件** (至少满足2项):
- [ ] 弹簧模式: 假跌破 + 放量 + 收回支撑 + 长下影
- [ ] OBV底背离: 价格新低 + OBV抬高 (>3%)
- [ ] 暗池吸筹: 占比>40% + 溢价>0.3%
- [ ] Call激增: 成交量>300% + OTM集中

**派发必备条件** (至少满足2项):
- [ ] 放量滞涨: 成交量>150% + 涨幅<1% + 上影线>实体2倍
- [ ] OBV顶背离: 价格新高 + OBV降低 (>3%)
- [ ] 暗池派发: 占比>40% + 折价>0.3%
- [ ] Put激增做空: 成交量>300% + 价格高位

#### 证据清单生成规则

报告中的**关键证据清单**必须来源于评分卡中得分 ≥5分的信号，并标注:
- 信号名称
- 具体数值 (如 "成交量 1.8倍均量")
- 得分权重
- 可信度星级 (⭐⭐⭐⭐⭐)

### 5. Output Generation

Structure the output according to the report template in `references/analysis-template.md`:

1. **Comprehensive Diagnosis** - Clear classification with confidence level
2. **Key Evidence List** - 3-4 core anomalies supporting the conclusion
3. **Institutional Cost Zone Estimate** - Price range where institutions are building/exiting positions
4. **Risk & Inflection Point Prediction** - Next key timeframe or price level to watch

**新增要求：**
- 报告末尾需标注**分析师**字段，格式：`{工具}-{模型}`，例如 `ClaudeCode-gemini3`、`codex-GPT-5.2`
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`

#### Automatic Report Saving

After completing the analysis, save the report to the project directory:

**Save Location:** `./output/research/research-institutional-机构操作分析-{YYYYMMDD}-{TICKER}.md`

**Example:** `./output/research/research-institutional-机构操作分析-20260128-TSLA.md`

**To save the report:**
1. Generate the complete analysis report using the template structure
2. Run the save script: `python scripts/save_report.py <report-content-file> <ticker>`
3. Or manually save the markdown output to the specified path

The script will:
- Create the `./output/research/` directory if it doesn't exist
- Generate filename with format: `research-institutional-机构操作分析-{YYYYMMDD}-{TICKER}.md`
- If a file with the same name already exists, automatically append `(1)`, `(2)`, etc. to avoid overwriting
- Save the full report content to the file

## Guidelines

### 核心原则
- **Objective Analysis:** Base conclusions on data, not narratives
- **Multiple Confirmations:** Require at least 2-3 independent signals before strong classification
- **Context Matters:** Consider broader market conditions and sector trends
- **Timeframe Alignment:** Ensure signals align across multiple timeframes
- **Risk Acknowledgment:** Always acknowledge uncertainty and provide alternative scenarios

### 评分卡使用规范 (关键)

**1. 量化优先原则**
- ❌ 避免: "成交量放大" / "出现背离" / "暗池活跃"
- ✅ 必须: "成交量 1.8倍20日均量" / "OBV抬高 4.2%" / "暗池占比 42%，溢价 0.4%"

**2. 阈值明确原则**
所有判定必须引用具体阈值:
- 放量: >150% 均量
- 缩量: <50% 均量
- 背离: 差距 >3%
- 暗池: 占比 >40%
- CMF强势: >+0.25

**3. 可追溯原则**
每个得分必须对应:
- 具体日期/时间段
- 原始数值
- 判定条件检查清单

**4. 边界清晰原则**
- 49分 = 观望，50分 = 温和吸筹 (无模糊地带)
- 严格按照 `scoring-system.md` 的区间分类
- 不得使用"介于两者之间"的表述

**5. 一致性检查**
生成报告前，确认:
- [ ] 吸筹结论下无未解释的派发信号
- [ ] 派发结论下无未解释的吸筹信号
- [ ] 价格趋势与分类方向一致 (或已标注背离)
- [ ] 总分计算正确，各维度相加无误

## Key Patterns Reference

### Accumulation Patterns
- **Wyckoff Accumulation Schematic:** Spring → Test → Sign of Strength
- **Volume Climax:** High volume washout followed by low volume consolidation
- **Base Building:** Higher lows on contracting volatility

### Distribution Patterns
- **Wyckoff Distribution Schematic:** Buying Climax → Test → Sign of Weakness
- **Upthrust:** False breakout on high volume, immediate reversal
- **Distribution Range:** Lower highs, expanding volatility at resistance

## Resources

### references/
- **scoring-system.md** - ⭐ 评分卡量化系统详解 (核心参考，必看)
  - 四维评分矩阵 (VSA/技术指标/盘口/期权)
  - 确定性分类阈值
  - 置信度计算公式
  - 质量检查清单
- **scoring-quickref.md** - ⭐ 评分卡快速参考表 (分析时查阅)
  - 所有阈值速查
  - 分类区间
  - 置信度加成表
- **scoring-examples.md** - 评分卡使用示例集
  - 温和吸筹案例 (TSLA)
  - 疯狂出货案例 (AAPL)
  - 信号冲突案例 (NVDA)
  - 常见错误纠正
- **analysis-template.md** - 分析报告模板 (已集成评分卡字段)
- **vsa-patterns.md** - Volume Spread Analysis pattern catalog
- **divergence-guide.md** - Technical indicator divergence interpretation guide

### scripts/
- **save_report.py** - Save analysis report to `./output/research/research-institutional-机构操作分析-{YYYYMMDD}-{TICKER}.md`

> **注意**: 本 skill 依赖评分卡量化系统进行主观分析。技术指标（OBV、CMF、RSI 等）建议从专业数据源（Yahoo Finance、TradingView、Bloomberg）直接获取，或使用 pandas/ta-lib 等工具计算。评分卡的核心价值在于**分析框架和量化标准**，而非基础指标计算。
