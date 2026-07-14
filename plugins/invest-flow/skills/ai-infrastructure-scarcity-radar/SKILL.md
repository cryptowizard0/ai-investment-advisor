---
name: ai-infrastructure-scarcity-radar
description: "Use when researching early AI infrastructure scarcity opportunities across optical modules, HBM, CoWoS, liquid cooling, power equipment, AI storage, advanced packaging, networking, semiconductor materials, equipment, or testing. Use for opportunity discovery, supply-demand bottleneck analysis, candidate company screening, and research-priority scoring."
---

# AI 基建稀缺机会雷达

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于发现 6-24 个月窗口内的早期 AI 基建稀缺投资机会。核心目标不是追逐 AI 热点，而是判断某个 AI 系统架构变化是否正在放大单位用量、制造供需缺口，并最终让特定公司在收入、利润或订单上真实受益。

默认输出目录：`./output/ai-infrastructure-scarcity-radar/`

## Trigger

在对话中使用：
- `/ai-infrastructure-scarcity-radar <主题或环节>`
- 示例：`/ai-infrastructure-scarcity-radar CPO 光互联`
- 示例：`使用 AI 基建稀缺机会雷达分析液冷 CDU`
- 示例：`HBM 供应链还有没有早期机会`
- 示例：`某公司是否真实受益于 CoWoS 扩产`

适用范围包括：
- GPU / AI ASIC / rack-scale 系统
- HBM / DDR / NAND / SSD / HDD
- CoWoS / SoIC / ABF / 先进封装 / 测试
- 光模块 / 光芯片 / 激光器 / 硅光 / CPO / 光纤 / 连接器
- 交换芯片 / NIC / DPU / Retimer / SerDes
- 数据中心电力 / 变压器 / UPS / PDU / 储能
- 液冷 / CDU / 冷板 / 快接头 / 泵阀
- 半导体材料、设备、测试设备

## Workflow

### 1) 识别研究对象
- 提取用户要研究的主题、产业链环节、公司或股票代码。
- 若用户没有指定市场，默认覆盖全球市场，中美重点，纳入美股、港股、A股及关键日韩台欧供应商。
- 若用户没有指定时间窗口，默认使用 6-24 个月观察窗口。

### 2) 收集证据
- 涉及财务、价格、订单、产能、估值、新闻和公司指引时，必须查询最新公开来源。
- 优先使用公司财报、Investor Relations、earnings call transcript、交易所公告、客户或供应商公开披露、权威行业数据和可信新闻。
- 关键事实必须标注来源和日期；无法确认的数据标记为“不确定”，不得编造。
- 明确区分“事实 / 推断 / 假设”。

### 3) 使用方法论分析
读取 `references/methodology.md`，按以下链路分析：

`AI 架构变化 -> 单位用量变化 -> 供需缺口 -> 公司真实受益 -> 财务兑现 -> 市场定价 -> 风险与跟踪信号`

每次分析必须回答：
1. 这个机会来自什么 AI 架构变化？
2. 需求为什么会放大？
3. 单位用量是否非线性增长？
4. 供给为什么扩不快？
5. 哪些环节最可能短缺？
6. 哪些公司真实受益？
7. 财务是否开始兑现？
8. 当前市场是否已经充分定价？
9. 最大风险是什么？
10. 下一步应该跟踪什么数据？

### 4) 评分
按 0-5 或负分区间逐项打分：

| 维度 | 分数 |
|------|------|
| 需求确定性 | 0-5 |
| 单位用量弹性 | 0-5 |
| 供给约束 | 0-5 |
| 技术壁垒 | 0-5 |
| 客户绑定 | 0-5 |
| 财务兑现 | 0-5 |
| 预期差 | 0-5 |
| 周期风险 | -5-0 |

另给出证据置信度：低 / 中 / 高。证据置信度不进入总分，但必须影响最终判断。

总分判断：
- 28 分以上：高优先级，值得深度研究
- 22-28 分：进入重点观察池
- 16-22 分：继续验证
- 10-16 分：普通景气机会
- 10 分以下：暂不值得研究

### 5) 套用报告模板
- 使用 `references/report-template.md` 的章节结构输出中文 Markdown 报告。
- 不给确定性买卖建议，只给研究优先级、观察池判断、风险和下一步验证数据。
- 如果只有需求增长，没有单位用量弹性、供给约束或财务兑现，不得判定为稀缺机会，只能归类为普通景气或概念主题。

### 6) 保存报告
- 输出目录：`./output/ai-infrastructure-scarcity-radar/`
- 文件名：`ai-infrastructure-scarcity-radar-{主题}-{YYYY-MM-DD}.md`
- 若文件已存在，不要覆盖；追加 `(1)`, `(2)`, `(3)`。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`。

## Quality Rules

- 使用中文；财务与技术术语可保留 English。
- 不追热点，不用空话。
- 必须区分真短缺、高景气、纯概念。
- 必须区分收入弹性和利润弹性。
- 必须警惕扩产过剩、价格下行、客户砍单和技术替代。
- 必须关注客户集中、认证周期和供应链迁移风险。
- 公司受益判断必须落到产品、客户、订单、产能、毛利率或管理层指引。
- 市场定价判断必须同时考虑估值、股价反应、预期上修和叙事拥挤度。

## Resources

### references/methodology.md
系统方法论，包含架构变化分类、产业链覆盖、供需缺口判断、财务兑现指标和市场定价检查。

### references/report-template.md
固定中文 Markdown 报告模板，包含一句话结论、机会来源、产业链地图、供需缺口、公司筛选、评分、跟踪信号、最终判断、数据来源与证据等级。
