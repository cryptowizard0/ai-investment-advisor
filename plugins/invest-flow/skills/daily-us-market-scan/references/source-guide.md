# 数据源与核验指南

## 来源优先级

优先级从高到低：

1. 官方和一手来源：公司 IR、SEC filings、Federal Reserve、CME FedWatch、FRED、U.S. Treasury、EIA、交易所和指数官网。
2. 权威新闻和市场数据：Reuters、Bloomberg、CNBC、WSJ、MarketWatch、FactSet、Nasdaq、CME、Barchart。
3. 行情和图表工具：Yahoo Finance、Investing、TradingView、Koyfin、Finviz。
4. 二手评论和社交媒体只能作为线索，不能作为关键事实的唯一依据。

## 核验规则

- 指数、ETF、股票涨跌幅优先使用交易所、Nasdaq、Yahoo Finance、Barchart 或 Investing，并记录数据时间。
- 宏观数据优先使用官方发布机构；新闻稿或财经媒体可用于解释市场反应。
- Fed 降息概率优先使用 CME FedWatch，并标注对应 FOMC 会议。
- 美债收益率优先使用 U.S. Treasury、FRED、CNBC 或 MarketWatch。
- 财报数据优先使用公司 earnings release、10-Q/10-K、IR presentation 和 earnings call transcript。
- 机构观点必须写明机构、分析师或来源媒体，以及发布日期。
- 如果同一数据存在差异，写出来源差异，并解释采用哪一个数值。
- 无法核验时写 `暂无可靠数据`。

## 必查资产

大盘和波动率：
- Dow Jones、S&P 500、Nasdaq Composite、Nasdaq 100 / QQQ、Russell 2000 / IWM、SOX、VIX。

宏观：
- 2Y、10Y、30Y Treasury yield、2Y-10Y spread、10Y-30Y spread、DXY、Gold、WTI、Brent、Bitcoin、Ethereum、FedWatch。

S&P 500 板块 ETF：
- XLK、XLC、XLY、XLF、XLI、XLV、XLP、XLE、XLU、XLB、XLRE。

主题和风格 ETF：
- SMH、SOXX、IGV、CIBR、HACK、CLOU、WCLD、BOTZ、AIQ、IWO、IWN、RSP、QQQ、SCHG、VTV。

大型科技：
- NVDA、MSFT、AAPL、GOOGL、AMZN、META、TSLA。

AI 硬件和半导体：
- NVDA、AMD、AVGO、MRVL、MU、TSM、ASML、ARM、INTC、QCOM、SMCI、DELL、HPE、ANET、CLS、VRT、COHR、LITE、AAOI、TSEM、SIVE。

软件 / SaaS / AI 应用：
- CRM、NOW、SNOW、ORCL、ADBE、PANW、CRWD、DDOG、NET、MDB、PLTR、APP、TEAM、WDAY、INTU、SHOP。

AI 电力 / 数据中心基础设施：
- CEG、VST、NRG、ETN、PWR、GEV、VRT、FLNC、OKLO、SMR、BE、NEE、SO、DUK、APLD、IREN、CORZ。

用户重点关注股票池：
- 核心科技 / AI：NVDA、AMD、AVGO、MRVL、GOOGL、MSFT、META、AMZN、ORCL。
- 软件：CRM、NOW、SNOW、ADBE、PANW、CRWD、PLTR、DDOG、NET。
- 光通信 / AI 互连：LITE、COHR、AAOI、TSEM、SIVE、MRVL、AVGO、ANET。
- AI 电力 / 数据中心基础设施：FLNC、OKLO、VST、CEG、ETN、VRT、PWR、GEV、APLD、IREN。
