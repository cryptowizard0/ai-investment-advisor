---
name: reflexivity-deep-analysis
description: "反身性深度分析。基于索罗斯反身性框架，对个股、行业、资产类别或宏观主题做完整周期分析，围绕叙事、资金行为、价格、现实验证、边际变化、错位关系与反转风险生成固定模板的中文 Markdown 报告。适用于：(1) 用户要求做完整反身性深度研究, (2) 需要判断一个主题处于反身性周期哪个阶段, (3) 需要识别机会 / 透支 / 反转风险并输出到 ./output/reflexivity-deep-analysis/。"
---

# Reflexivity Deep Analysis

## Overview

本 skill 用于把“反身性分析框架 B - 深度分析”固化成完整研究流程。执行时必须同时使用：
- `references/framework.md` 中的深度分析方法。
- `assets/report-template.md` 中的固定报告模板。

输出目录：`./output/reflexivity-deep-analysis/`

## Trigger

在对话中使用：
- `/reflexivity-deep-analysis <主题>`
- 示例：`/reflexivity-deep-analysis 英伟达`
- 示例：`/reflexivity-deep-analysis "AI 电力基础设施"`
- 示例：`/reflexivity-deep-analysis 美债`

## Workflow

### 1) 界定研究对象与主叙事
- 明确主题是个股、行业、商品、指数还是宏观叙事。
- 先定义一个最核心、最能驱动价格的市场叙事，再进入后续分析。
- 若主题过宽，先缩小到一个可交易、可验证的主线。

### 2) 分析叙事层
- 用一句话写清“市场现在相信什么”。
- 评估：
  - 媒体热度
  - 共识程度
  - 散户参与
  - “这次不一样”感
- 识别叙事来源：企业、政策、媒体、分析师、技术突破或宏观预期。
- 明确该叙事是刚出现，还是已经成为市场共识。

### 3) 分析行为层
- 至少列出 3 条关键资金行为证据。
- 证据优先来自：
  - ETF/基金资金流
  - 机构持仓变化
  - 杠杆/融资变化
  - 一级市场融资热度
  - 企业资本开支
- 判断行为性质属于：
  - 试探性建仓
  - 趋势性追涨
  - 拥挤性交易
  - 被迫性平仓/止损
- 回答这是主动相信，还是被价格裹挟。

### 4) 分析价格层
- 重点看：
  - 趋势是否顺滑
  - 波动是否放大
  - 利好 / 利空敏感度
  - 是否出现背离
- 判断价格更接近：
  - `预期启动`
  - `正反馈强化`
  - `预期透支`
  - `反身性断裂`
- 明确价格是在验证叙事，还是已经透支叙事。

### 5) 分析现实层
- 回答“如果叙事为真，现实里必须出现什么”。
- 列出 3 个最关键、最可验证的现实指标。
- 对每个指标判断：
  - 没出现
  - 刚出现
  - 持续强化
  - 开始转弱
- 明确哪些是已验证事实，哪些是推断，哪些仍待验证。

### 6) 分析边际变化层
- 分别写：
  - 认知边际
  - 价格边际
  - 现实边际
- 不要只写趋势方向，要抓“变化的变化”，例如共识是否过强、创新高是否更难、利润增速是否放缓。

### 7) 分析错位关系
- 必须分析三组关系：
  - 认知 vs 价格
  - 价格 vs 现实
  - 认知 vs 现实
- 最终判断当前更像：
  - `类型 A：认知先行，价格未动`
  - `类型 B：价格先行，现实未到`
  - `类型 C：价格远超现实，共识极强`

### 8) 判断周期阶段与反转信号
- 从以下阶段中选择一个主阶段：
  - `阶段 1：叙事萌芽`
  - `阶段 2：价格启动`
  - `阶段 3：正反馈强化`
  - `阶段 4：透支与脆弱`
  - `阶段 5：反转与负反馈`
- 同时检查顶部信号与底部信号。
- 明确当前更接近顶部风险区，还是底部孕育区。

### 9) 提炼触发因素与结论
- 列出 3 个最可能改变当前反身性结构的触发因素。
- 最终结论必须串起链条：
  - 叙事
  - 行为
  - 价格
  - 现实
  - 边际变化
- 一句话投资判断必须同时包含：
  - 当前阶段
  - 风险 / 机会属性
  - 最关键后续观察点

### 10) 套模板并保存
- 严格按 `assets/report-template.md` 输出，不删除章节。
- 无法确认的地方，明确标注 `已验证 / 推断 / 待验证`。
- 所有输出报告必须包含固定作者字段：`InvestmentFlow`
- 生成最终 Markdown 后，用下面命令保存：

```bash
python plugins/invest-flow/skills/reflexivity-deep-analysis/scripts/save_report.py --topic "英伟达"
```

- 也可以保存一份已写好的 Markdown：

```bash
python plugins/invest-flow/skills/reflexivity-deep-analysis/scripts/save_report.py \
  --topic "AI 电力基础设施" \
  --content-file /tmp/reflexivity-deep-report.md
```

## Output Requirements

- 语言：中文，投资研究术语可保留英文。
- 格式：Markdown。
- 必须包含：
  - 作者：InvestmentFlow
  - 叙事层
  - 行为层
  - 价格层
  - 现实层
  - 边际变化层
  - 错位判断
  - 周期阶段判断
  - 反转识别模块
  - 触发因素模块
  - 最终输出
  - 信息缺口与待验证点
  - 数据来源与观察依据

## Resources

### references/
- `framework.md`: 反身性深度分析框架与判断准则。

### assets/
- `report-template.md`: 固定深度报告模板。

### scripts/
- `save_report.py`: 将最终 Markdown 保存到 `./output/reflexivity-deep-analysis/`，自动处理重名文件。
