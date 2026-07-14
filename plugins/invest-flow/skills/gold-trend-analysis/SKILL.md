---
name: gold-trend-analysis
description: Deep dive gold market bubble risk analysis for macro commodities traders. Use this skill when (1) User requests gold market analysis or bubble risk assessment, (2) User asks to generate gold risk reports, (3) User mentions analyzing gold prices above $5000, real interest rates, hedge fund positioning, gold-silver ratio, or gold/SPX valuation, (4) User asks for gold trading strategy with stop-loss recommendations. Generates comprehensive markdown reports with 0-100 risk scores saved to ./output/gold-analysis/ directory.
---

# Gold Trend Analysis

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

Execute deep risk scanning for 2026 gold market to assess whether current gold prices ($5,000+) are approaching bubble territory through real interest rate analysis, hedge fund positioning, and cross-asset valuation metrics.

## Overview

As a senior commodities strategist and macro analyst, this skill enables comprehensive bubble risk assessment by:
- Gathering real-time market data via web search (spot/futures prices, real interest rates, COT positioning, gold-silver ratio, gold/SPX valuation)
- Analyzing four key risk dimensions: interest rate erosion, crowded positioning, silver bubble signals, and spot-futures divergence
- Computing quantitative risk scores (0-100) with identification of the single most critical warning signal
- Analyzing pricing anchors to determine what's supporting gold prices (geopolitical risk, interest rates, or central bank buying)
- Generating actionable trading strategies with specific stop-loss levels and position adjustment recommendations

**Output**: Markdown reports saved to `./output/gold-analysis/gold-{analysis-type}-{date}.md`

## Workflow

### Step 1: Determine Analysis Date

Default to today's date unless user specifies otherwise. Format: YYYY-MM-DD (e.g., 2026-01-28).

### Step 2: Search for Real-Time Market Data

**CRITICAL**: Use WebSearch to gather ALL 5 required indicator groups before proceeding to analysis. Do not skip any indicators.

#### Indicator 1: Gold Spot & Futures Prices with Basis

**Search Keywords**:
- "spot gold price XAU/USD today"
- "COMEX gold futures price(GCmain) today"
- "gold basis contango backwardation"

**Target Data**:
- Spot gold price (USD/oz)
- COMEX front futures price (USD/oz)
- Calculate basis: Futures - Spot
- Convert basis to annualized percentage: (Basis / Spot) × (365 / Days to Expiry) × 100%

#### Indicator 2: US 10-Year Real Interest Rate (TIPS)

**Search Keywords**:
- "US 10 year TIPS yield today"
- "10 year real interest rate"
- "Treasury inflation protected securities yield"

**Target Data**:
- Current 10-year TIPS yield (%)
- Recent trend (rising/falling/stable)
- Historical context (percentile level)

**Critical Insight**: Gold is a non-yielding asset. Rising real rates increase opportunity cost of holding gold.

#### Indicator 3: Hedge Fund Net Long Positioning from COT Report

**Search Keywords**:
- "CFTC COT report gold"
- "hedge fund gold positioning"
- "managed money net long gold"
- "gold speculative positioning"

**Target Data**:
- Latest net long positioning (contracts or % of open interest)
- Comparison to historical extremes
- Recent change trend (increasing/decreasing)

**Critical Insight**: Extreme net long positioning indicates crowded trades vulnerable to liquidation.

#### Indicator 4: Gold-Silver Ratio & Silver 5-Day Volatility

**Search Keywords**:
- "gold silver ratio today"
- "silver price volatility"
- "XAG USD volatility 5 day"

**Target Data**:
- Current gold-silver ratio (e.g., 85:1)
- Silver's 5-day realized volatility or price range
- Recent silver momentum vs. gold

**Critical Insight**: Rapid ratio decline with high silver volatility suggests late-stage speculative frenzy.

#### Indicator 5: Gold/S&P500 Ratio Historical Percentile

**Search Keywords**:
- "gold SP500 ratio"
- "gold SPX valuation"
- "gold relative to stocks"

**Target Data**:
- Current gold/SPX ratio
- Historical percentile (e.g., 95th percentile = extremely elevated)
- 10-year comparison

**Critical Insight**: Elevated ratio suggests gold is expensive relative to equities, potentially due for mean reversion.

**Data Quality Check**:
- Verify data is from the analysis date (not outdated)
- Cross-reference 2-3 sources for critical metrics
- Note data publication lags (COT reports typically delayed by ~3 days)
- Distinguish between real-time quotes vs. closing prices

### Step 3: Perform Deep Risk Assessment

Read the methodology reference file for detailed analysis frameworks:

```
references/analysis_methodology.md
```

Apply the four core risk assessment dimensions:

#### 1. Interest Rate Erosion (利率侵蚀)

**Analysis Logic**:
- Rising real interest rates increase opportunity cost of holding non-yielding gold
- Monitor 10-year TIPS yield direction and magnitude
- Historical relationship: Gold typically struggles when real rates >2%

**Risk Signals**:
- Real rates rising rapidly (e.g., +50bps in a month) → HIGH RISK
- Real rates turning positive after prolonged negativity → WARNING
- Real rates declining → SUPPORTIVE for gold

#### 2. Crowded Positioning (多头拥挤)

**Analysis Logic**:
- Extreme net long positioning by hedge funds indicates crowded trade
- Compare current positioning to 5-year historical range
- When positioning is at 90th+ percentile, liquidation risk is high

**Risk Signals**:
- Net long at extreme historical levels → HIGH RISK
- Positioning increasing while price stalls → VERY HIGH RISK
- Positioning declining with price rising → HEALTHY

#### 3. Silver Bubble Signals (白银泡沫)

**Analysis Logic**:
- Silver typically leads in late-stage bull markets due to its speculative appeal
- Gold-silver ratio declining rapidly suggests risk appetite and speculation
- High silver volatility confirms speculative activity

**Risk Signals**:
- Gold-silver ratio <70 with rapid decline → WARNING
- Silver outperforming gold by >10% in 5 days → HIGH RISK
- Silver volatility >3% daily average → EXTREME SPECULATION

#### 4. Spot-Futures Divergence (期现背离)

**Analysis Logic**:
- Expanding contango (futures premium over spot) while spot stalls suggests speculative excess
- Healthy markets show consistent spot-futures relationship
- Divergence indicates forward expectations exceeding current fundamentals

**Risk Signals**:
- Futures premium expanding while spot flat/declining → HIGH RISK
- Annualized contango >2% → EXCESSIVE SPECULATION
- Contango steepening into deferred contracts → BUBBLE TERRITORY

### Step 4: Calculate Comprehensive Risk Score (0-100)

Use the scoring model from `analysis_methodology.md`:

| Dimension | Weight | Scoring Criteria |
|-----------|--------|------------------|
| Interest Rate Erosion | 30 points | 0-10: declining or <0%, 11-20: stable 0-1.5%, 21-30: rising or >1.5% |
| Crowded Positioning | 30 points | 0-10: <50th percentile, 11-20: 50-80th percentile, 21-30: >80th percentile |
| Silver Bubble Signals | 20 points | 0-10: ratio >80, 11-15: ratio 70-80, 16-20: ratio <70 with high volatility |
| Spot-Futures Divergence | 20 points | 0-10: <1% contango, 11-15: 1-2% contango, 16-20: >2% contango with spot weakness |

**Risk Levels**:
- 0-30: Low Risk - Fundamentally supported, healthy market structure
- 31-60: Medium Risk - Mixed signals, cautious positioning warranted
- 61-80: High Risk - Multiple warning signals, reduce exposure recommended
- 81-100: Extreme Risk - Bubble territory, immediate protective action required

### Step 5: Identify Top Warning Signal

Identify THE SINGLE MOST CRITICAL indicator causing greatest concern right now.

**Selection Criteria**:
- Which indicator shows the most extreme reading vs. historical norms?
- Which indicator is deteriorating most rapidly?
- Which indicator historically preceded major corrections?

**Example Top Warning Signals**:
- "实际利率在 30 天内上升 80 个基点至 2.3%，为 2019 年以来最快速度，无息资产黄金面临严重压力"
- "对冲基金净多头持仓达到历史 98 分位，上一次此水平出现在 2011 年金价顶部前夕"
- "金银比暴跌至 65，白银 5 日波动率达 4.2%，典型的投机性泡沫末期特征"

### Step 6: Analyze Pricing Anchors (定价锚点分析)

Determine what fundamental factors are currently supporting gold prices:

**Three Primary Anchors**:

1. **Geopolitical Risk Premium (地缘风险溢价)**
   - Is there active conflict or heightened geopolitical tension?
   - How much of current price is fear premium?
   - Risk: Premium can evaporate quickly if tensions ease

2. **Interest Rate Environment (利率环境)**
   - Are real rates negative or very low?
   - Is the Fed pausing or cutting rates?
   - Risk: Any hawkish shift undermines this support

3. **Central Bank Buying (央行购金)**
   - Are central banks (especially China, Russia, India) actively accumulating?
   - What percentage of global gold demand is official sector?
   - Risk: If official sector buying slows, retail demand may not compensate

**Analysis Output**: Rank these three anchors by strength and assess fragility. Identify which anchor is most vulnerable to change.

### Step 7: Formulate Actionable Trading Strategy

Provide specific, implementable recommendations with exact levels:

**Components Required**:

1. **Directional View**: HOLD / REDUCE / EXIT / SHORT
2. **Stop-Loss Level**: Specific price (e.g., "严格止损位设定在 $2,850/oz")
3. **Position Adjustment**: Percentage reduction (e.g., "建议减持 40% 现货仓位")
4. **Time Horizon**: Short-term tactical vs. long-term strategic view
5. **Upside/Downside Scenarios**: Define what would invalidate the bearish case

**Example Strategy**:
```
风险评分 72/100 - 建议减仓 50%
止损位: $2,820/oz (较当前价位 $2,900 下跌 2.8%)
调仓建议:
- 现货投资者: 减持至 30% 仓位,保留核心配置
- 期货多头: 立即平仓 70% 多单,剩余设定 $2,820 止损
- 期权策略: 考虑购买 3 月到期 $2,750 看跌期权作为保险

观望信号 (什么情况下重新加仓):
- 实际利率重新转负
- 金银比回升至 80+ 且银价稳定
- COT 净多头持仓降至 50 分位以下
```

### Step 8: Generate Report

Read the template at `assets/report_template.md` to structure the output. Replace all placeholders with actual analysis content.
Every generated report must include `作者：InvestmentFlow`.

**Key Placeholders**:
- {DATE}, {ANALYSIS_TYPE}, {TIMESTAMP}
- {SPOT_PRICE}, {FUTURES_PRICE}, {BASIS}, {BASIS_PCT}
- {REAL_RATE}, {RATE_TREND}
- {NET_LONG_POSITION}, {POSITION_PERCENTILE}
- {GOLD_SILVER_RATIO}, {SILVER_VOLATILITY}
- {GOLD_SPX_RATIO}, {GOLD_SPX_PERCENTILE}
- {RATE_EROSION_ANALYSIS}, {POSITIONING_ANALYSIS}, {SILVER_BUBBLE_ANALYSIS}, {DIVERGENCE_ANALYSIS}
- {RISK_SCORE}, {RISK_LEVEL}, {RISK_REASONING}
- {TOP_WARNING_SIGNAL}
- {ANCHOR_1_ANALYSIS}, {ANCHOR_2_ANALYSIS}, {ANCHOR_3_ANALYSIS}, {ANCHOR_SUMMARY}
- {DIRECTIONAL_VIEW}, {STOP_LOSS}, {POSITION_ADJUSTMENT}, {REENTRY_SIGNALS}

### Step 9: Save Report

**IMPORTANT**: Always check for existing files and avoid overwriting. Use numbered suffixes for duplicate filenames.

#### Save Process

1. **Ensure directory exists**: `./output/gold-analysis/` (create if needed)

2. **Generate base filename**: `gold-{analysis-type}-{date}`
   - Default: `gold-bubble-risk-2026-01-28`
   - Alternative: `gold-deep-scan-2026-01-28`

3. **Handle filename conflicts** (CRITICAL):
   - Check if `gold-{analysis-type}-{date}.md` already exists
   - If exists, append numbered suffix: `gold-{analysis-type}-{date}(1).md`
   - If that exists, increment: `gold-{analysis-type}-{date}(2).md`
   - Continue incrementing until finding an available filename

4. **Write the complete report** to the determined filename

5. **Confirm to user** with actual saved path:
   - First save: "深度风险扫描报告已生成: ./output/gold-analysis/gold-bubble-risk-2026-01-28.md"
   - Duplicate: "深度风险扫描报告已生成: ./output/gold-analysis/gold-bubble-risk-2026-01-28(1).md"

#### Implementation Methods

**Method 1: Manual Logic (Preferred for immediate use)**
```python
import os

def get_unique_filename(directory, base_name, extension=".md"):
    """Generate unique filename avoiding conflicts"""
    os.makedirs(directory, exist_ok=True)

    file_path = os.path.join(directory, f"{base_name}{extension}")
    if not os.path.exists(file_path):
        return file_path

    counter = 1
    while True:
        new_path = os.path.join(directory, f"{base_name}({counter}){extension}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

# Usage
directory = "./output/gold-analysis"
base_name = "gold-bubble-risk-2026-01-28"
file_path = get_unique_filename(directory, base_name)
# Write report content to file_path
```

**Method 2: Use Helper Script**
```bash
# The helper script at scripts/save_report.py provides the same functionality
# However, prefer Method 1 for direct integration
```

#### Examples

**First analysis of the day**:
- Input: `gold-bubble-risk-2026-01-28`
- No conflicts → Output: `gold-bubble-risk-2026-01-28.md`

**Second analysis of the same day**:
- Input: `gold-bubble-risk-2026-01-28`
- Conflict detected → Output: `gold-bubble-risk-2026-01-28(1).md`

**Third analysis**:
- Input: `gold-bubble-risk-2026-01-28`
- Conflicts: base and (1) exist → Output: `gold-bubble-risk-2026-01-28(2).md`

## Analysis Standards

### Professional Requirements

- **Data-Driven**: Every conclusion must cite specific data points
- **Quantitative**: Use precise numbers, not vague descriptors ("实际利率 2.3%" not "实际利率较高")
- **Actionable**: Provide specific prices for stop-losses and exact percentages for position adjustments
- **Historical Context**: Compare current readings to historical percentiles and extremes
- **Balanced**: Present both bullish and bearish scenarios, but take a clear stance

### Critical Thinking

- **Question the Narrative**: Don't just follow consensus. If everyone expects gold to rise, why might they be wrong?
- **Identify Fragility**: Which seemingly strong support could break quickly?
- **Tail Risk**: What low-probability, high-impact event could trigger rapid unwinding?

### Language and Tone

- Professional, data-heavy, and decisive
- Use Chinese for narrative, English for technical terms
- Avoid hedging language like "可能" or "也许" - make clear calls
- Support bold claims with hard data

### Common Errors to Avoid

- Don't ignore rising real rates just because gold is rising (correlation can break)
- Don't dismiss crowded positioning because "this time is different"
- Don't confuse silver strength for market health (often signals late-stage excess)
- Don't provide strategy without specific stop-loss levels

## Resources

### Report Template
- `assets/report_template.md` - Comprehensive markdown template for bubble risk reports

### Analysis Framework
- `references/analysis_methodology.md` - Complete methodology including:
  - Four risk dimensions with detailed scoring rubrics
  - Historical examples of each risk signal
  - Pricing anchor framework
  - Strategy formulation guidelines
  - Data source recommendations and search keywords

**When to read**: Before Step 3 (risk assessment) to ensure rigorous application of all frameworks.

### Helper Scripts
- `scripts/save_report.py` - File conflict handler (optional)
  - Automatically generates numbered filenames to avoid overwrites
  - Usage: `python scripts/save_report.py <directory> <base_name> <content_file>`
  - Note: The inline Python logic in Step 9 is preferred for direct integration

## Example Usage

**User**: "执行 2026 年黄金市场深度风险扫描"

**Execution**:
1. Determine date: 2026-01-28
2. Search for all 5 indicator groups (spot/futures+basis, TIPS, COT, gold-silver+volatility, gold/SPX)
3. Read `references/analysis_methodology.md` for scoring model
4. Analyze four risk dimensions (interest rate, positioning, silver, divergence)
5. Calculate comprehensive 0-100 risk score
6. Identify the single top warning signal
7. Analyze pricing anchors (geopolitics, rates, central banks)
8. Formulate strategy with specific stop-loss and position adjustments
9. Read `assets/report_template.md` and populate all fields
10. Check for existing file `./output/gold-analysis/gold-bubble-risk-2026-01-28.md`
    - If not exists: Save to `gold-bubble-risk-2026-01-28.md`
    - If exists: Save to `gold-bubble-risk-2026-01-28(1).md` (or next available number)
11. Confirm with actual saved filename: "深度风险扫描报告已生成: ./output/gold-analysis/gold-bubble-risk-2026-01-28(1).md"
