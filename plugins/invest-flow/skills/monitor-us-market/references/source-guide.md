# 数据源与核验指南

## 来源优先级

优先级从高到低：

1. 官方和一手来源：公司 IR、SEC filings、Federal Reserve、CME FedWatch、FRED、U.S. Treasury、EIA、交易所和指数官网。
2. 权威新闻和市场数据：Reuters、Bloomberg、CNBC、WSJ、MarketWatch、FactSet、Nasdaq、CME、Barchart。
3. 行情和图表工具：Yahoo Finance、Investing、TradingView、Koyfin、Finviz。
4. 二手评论和社交媒体只能作为线索，不能作为关键事实的唯一依据。

一页式扫描来源（提高板块/主题扫描效率，避免逐个查询）：

- Finviz Groups（`finviz.com/groups.ashx`）：全部板块与细分行业的当日/近5日表现排名，是发现池外行业异动的首选。
- Barchart ETF performance / stockanalysis.com ETF screener：主题 ETF 宇宙一次性排序。
- Finviz Screener（52-week high/low、量比筛选）：捕捉群体性新高/新低和放量异动。

## 核验规则

- 指数、ETF、股票涨跌幅优先使用交易所、Nasdaq、Yahoo Finance、Barchart 或 Investing，并记录数据时间。
- 宏观数据优先使用官方发布机构；新闻稿或财经媒体可用于解释市场反应。
- Fed 降息概率优先使用 CME FedWatch，并标注对应 FOMC 会议。
- 美债收益率优先使用 U.S. Treasury、FRED、CNBC 或 MarketWatch。
- 财报数据优先使用公司 earnings release、10-Q/10-K、IR presentation 和 earnings call transcript。
- 机构观点必须写明机构、分析师或来源媒体，以及发布日期。
- 如果同一数据存在差异，写出来源差异，并解释采用哪一个数值。
- 无法核验时写 `暂无可靠数据`；整块指标拿不到时在报告「数据缺口」节说明，不留空表格。

## 必查核心（每日必须覆盖）

大盘和波动率：

- S&P 500、Nasdaq Composite、Dow Jones、Russell 2000、SOX、VIX。

宏观：

- 10Y / 2Y Treasury yield、DXY、Gold、WTI、Bitcoin、FedWatch 下次会议定价。
- 30Y、利差、Brent、Ethereum 等仅在当日有显著异动时补充。

个股：

- 七巨头：NVDA、MSFT、AAPL、GOOGL、AMZN、META、TSLA（逐一确认涨跌与新闻，每只一行）。
- 用户重点池（见下），按异动阈值报告。

## 板块与主题扫描宇宙

用途：这是「排序扫描」的宇宙，不是逐项填表清单。对宇宙按当日涨跌幅排序，板块取 Top3/Bottom3、主题取 Top5/Bottom5 入表；未上榜且无异动的不写。

GICS 板块 ETF（11 个全排序）：

- XLK、XLC、XLY、XLF、XLI、XLV、XLP、XLE、XLU、XLB、XLRE。

主题与风格 ETF 宇宙（覆盖 AI 内外，用于发现轮动和新主线）：

- AI / 科技：SMH、SOXX、IGV、CIBR、CLOU、BOTZ、AIQ、QTUM。
- 风格 / 宽度：QQQ、RSP、IWO、IWN、SCHG、VTV。
- 医疗 / 生物科技：XBI、IBB、IHI。
- 能源与电力：TAN、URA、NLR、ICLN、OIH、XOP。
- 金属与材料：GDX、COPX、XME、LIT。
- 金融 / 地产 / 消费：KRE、XHB、ITB、XRT、JETS。
- 国防 / 中概 / 高 beta：ITA、PPA、KWEB、FXI、ARKK。
- 加密相关用代表股观察：COIN、MSTR、MARA、RIOT。

扫描规则：

- 主题 ETF 单日 |涨跌幅| ≥3%，或近 5 日累计 ≥7%，入表时必须给一句驱动解读。
- 宇宙之外的行业异动靠 Finviz Groups 行业排名捕捉，发现后按新动态雷达标准处理。

## 新动态雷达触发标准

满足其一即可写入报告第 3 节（主题性/群体性；单一个股事件归第 5 节）：

- 同一主题 ≥3 只个股或对应 ETF 单日涨跌 ≥3%，且有共同催化。
- 量比 ≥3 或 52 周新高/新低的群体性现象。
- 盘后重大事件可能催生新主题：政策、并购潮、技术突破、突发供需冲击。

确无池外新动态时，如实写「今日扫描未发现池外显著新动态」并注明扫描范围（如：Finviz Groups 全行业 + 主题 ETF 宇宙）。

## 用户重点池（按异动阈值报告）

入表阈值：当日 |涨跌幅| ≥2%，或有实质新闻、财报、评级、订单事件；其余一行带过。

- 核心科技 / AI：NVDA、AMD、AVGO、MRVL、GOOGL、MSFT、META、AMZN、ORCL。
- 软件：CRM、NOW、SNOW、ADBE、PANW、CRWD、PLTR、DDOG、NET。
- 光通信 / AI 互连：LITE、COHR、AAOI、TSEM、SIVE、MRVL、AVGO、ANET。
- AI 电力 / 数据中心基础设施：FLNC、OKLO、VST、CEG、ETN、VRT、PWR、GEV、APLD、IREN。
- 半导体与硬件外延（异动时纳入）：MU、TSM、ASML、ARM、INTC、QCOM、SMCI、DELL、HPE、CLS。
- 电力外延（异动时纳入）：NRG、SMR、BE、NEE、SO、DUK、CORZ。
