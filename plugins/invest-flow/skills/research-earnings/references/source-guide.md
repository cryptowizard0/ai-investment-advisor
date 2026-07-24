# 财报解读数据源指南

## 来源优先级

| 类型 | 首选来源 | 备用来源 | 备注 |
|---|---|---|---|
| Earnings release | 公司 Investor Relations | 交易所公告、SEC EDGAR | 用于 headline 数据和 guidance |
| 法定财报 | 10-Q、10-K、20-F、年报 | 公司官网年报页面 | 用于三张表、附注和风险因素 |
| 电话会 | 官方 transcript、IR webcast | Seeking Alpha、Motley Fool、FactSet transcript | 必须区分 prepared remarks 和 Q&A |
| Consensus estimate | Bloomberg、FactSet、Visible Alpha | Yahoo Finance、MarketWatch、Analyst notes | 免费源可能滞后，标注来源 |
| 股价反应 | 交易所、Yahoo Finance、Nasdaq、NYSE | 券商行情 | 区分盘前、盘后和常规交易 |
| 估值倍数 | 公司 filings、市值/EV 数据源 | yfinance、Koyfin、TIKR | 标注计算时点 |
| 行业对比 | 同行业公司财报 | 行业报告、公司 presentation | 优先同周期财报 |

## 必须交叉验证的项目

- Revenue、EPS、gross margin、operating margin、FCF。
- 下季度和全年 guidance。
- 管理层关键原话和电话会 Q&A。
- 盘后/盘前股价反应。
- 关键 KPI，例如 ARR、RPO、backlog、bookings、GMV、same-store sales、subscriber、MAU/DAU。
- 一次性项目、重组费用、减值、税率变化和 non-GAAP 调整项。

## 处理冲突

- 公司 filings 优先于新闻报道。
- 公司原始口径优先于二次数据库，但必须说明 non-GAAP 与 GAAP 差异。
- 同一指标不同来源冲突时，写明差异，优先采用披露时间更晚且可追溯的来源。
- 无法核验的数据写 `数据暂缺` 或 `不确定`，不得用估算冒充事实。

## 常用搜索提示

- `{ticker} investor relations quarterly results`
- `{company} earnings release {period}`
- `{ticker} 10-Q {period}`
- `{company} earnings call transcript {period}`
- `{ticker} guidance revenue margin {period}`
- `{ticker} consensus revenue EPS {period}`
