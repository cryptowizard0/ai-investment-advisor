---
name: reflexivity-quick-scan
description: "反身性快速扫描分析。基于索罗斯反身性框架，对单个股票、行业主题、资产类别或市场叙事进行 5 分钟阶段判断，输出“启动 / 强化 / 透支 / 反转”导向的中文 Markdown 报告。适用于：(1) 用户要求快速判断一个市场叙事处于什么阶段, (2) 需要把认知、价格、现实验证、边际变化放在同一框架里分析, (3) 需要固定模板并保存到 ./output/reflexivity-quick-scan/。"
---

# Reflexivity Quick Scan

## Web Research Routing

- 当任务需要联网搜索、网页抓取或多页研究，且当前 agent 会话已安装对应 Firecrawl skill 时，优先使用 `firecrawl-search`（发现来源）、`firecrawl-scrape`（单页提取）、`firecrawl-crawl`（站点遍历）或 `firecrawl-deep-research`（多来源深研）。
- Firecrawl skill 不可用或调用失败时，再回退到当前会话提供的 web search / browser 工具。
- 工具优先级不得降低证据标准：仍优先公司公告、监管文件、交易所、IR 等一手来源，并按本 skill 的规则交叉验证。

## Overview

本 skill 用于把“反身性分析框架 A - 5 分钟快速扫描”固化成统一工作流。执行时必须同时使用：
- `references/framework.md` 中的判断方法。
- `assets/report-template.md` 中的固定报告模板。

输出目录：`./output/reflexivity-quick-scan/`

## Trigger

在对话中使用：
- `/reflexivity-quick-scan <主题>`
- 示例：`/reflexivity-quick-scan 英伟达`
- 示例：`/reflexivity-quick-scan "AI 电力基础设施"`
- 示例：`/reflexivity-quick-scan 黄金`

## Workflow

### 1) 识别分析对象
- 提取主题名称，允许是个股、板块、商品、指数或宏观叙事。
- 若用户给出观察窗口，优先使用用户窗口；否则默认基于“当前时点”进行快速扫描。
- 若主题过于宽泛，先聚焦到一个最主要交易叙事，再继续分析。

### 2) 提炼市场叙事
- 只写“市场当前最相信什么”，不要写分析者观点。
- 用一句话概括主叙事，并标注它是需求侧、政策侧、流动性侧还是估值侧驱动。
- 若存在多个叙事，只保留当前对价格影响最大的一个，其他作为补充。

### 3) 判断资金是否已经行动
- 必须覆盖：
  - 资金流入
  - 成交活跃度
  - 杠杆或融资扩张
  - 机构配置变化
- 若缺少直接数据，可以使用价格量能、ETF 资金、期权活跃度、融资余额、持仓变化等代理变量。
- 最终只给一个强度结论：`弱 / 中 / 强`。

### 4) 判断价格状态
- 不要只写涨跌，要写价格行为。
- 至少回答以下问题：
  - 是否持续创新高 / 新低
  - 坏消息是否还能把价格打下去
  - 好消息是否还能继续推高价格
- 最终只给一个价格状态：`启动 / 强化 / 钝化 / 反转`。

### 5) 做现实验证
- 明确回答：“如果这个叙事是真的，现实里必须发生什么？”
- 列出 2-3 个最关键、最可观察的现实指标。
- 对每个指标给出当前验证判断，并汇总成一个结论：`无 / 弱 / 中 / 强`。
- 信息不足时必须区分“已验证事实”与“待验证推断”。

### 6) 抓边际变化
- 优先找拐点，而不是复述趋势。
- 边际变化必须落在可观察变量上，例如：
  - 盈利仍增长，但增速放缓
  - 资金仍流入，但斜率放缓
  - 利空很多，但价格不再创新低
  - 叙事仍强，但共识已明显拥挤
- 最后用一句话写出最关键边际变化。

### 7) 形成阶段判断
- 结合认知、价格、现实三者关系，判断整体更接近：
  - `启动`
  - `强化`
  - `透支`
  - `反转`
- `价格状态` 与 `当前阶段` 可以不同：
  - 例如价格仍在强化，但整体阶段已经更接近透支。
- 一句话投资判断必须包含：
  - 当前阶段
  - 核心风险或机会
  - 下一步最值得盯住的验证点

### 8) 套模板并保存
- 严格按 `assets/report-template.md` 输出，不删除章节。
- 信息不足时写“数据暂缺”或“需进一步验证”，不要留空。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`
- 生成最终 Markdown 后，用下面命令保存：

```bash
python plugins/invest-flow/skills/reflexivity-quick-scan/scripts/save_report.py --topic "英伟达"
```

- 也可以把已生成内容写入临时文件后保存：

```bash
python plugins/invest-flow/skills/reflexivity-quick-scan/scripts/save_report.py \
  --topic "AI 电力基础设施" \
  --content-file /tmp/reflexivity-report.md
```

## Output Requirements

- 语言：中文，金融术语可保留英文。
- 格式：Markdown。
- 必须包含：
  - 作者：InvestmentFlow
  - 市场叙事
  - 资金是否已经行动
  - 价格状态
  - 现实验证
  - 边际变化
  - 最终结论
  - 信息缺口与待验证点
  - 数据来源与观察依据

## Resources

### references/
- `framework.md`: 反身性快速扫描框架原型与执行准则。

### assets/
- `report-template.md`: 固定报告模板。

### scripts/
- `save_report.py`: 将最终 Markdown 保存到 `./output/reflexivity-quick-scan/`，自动处理重名文件。
