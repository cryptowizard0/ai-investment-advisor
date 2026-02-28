---
name: institutional-accumulation-agent
description: 分析机构资金的吸筹和派发模式，通过量价分析、技术指标背离、盘口微观结构和成交量分布分析识别主力资金意图。
tools:
  bash: true
  read: true
  write: true
  edit: true
  grep: true
  websearch: true
  skill: true
  todowrite: true
---

# Institutional Accumulation Agent

## 概述

分析机构资金的吸筹和派发模式，通过量价分析、技术指标背离、盘口微观结构和成交量分布分析识别主力资金意图。

## 输入 (Input Schema)

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| ticker | string | 是 | 股票代码（如 TSLA） |
| analysis_period | string | 否 | 分析周期（默认 "3m"） |

## 输出 (Output Schema)

```json
{
  "report_path": "string",
  "classification": "string",
  "confidence": "number",
  "cost_zone": "string",
  "key_evidence": ["string"]
}
```

## 错误处理 (Error Handling)

| 错误类型 | 处理方式 | 说明 |
|---------|---------|------|
| DATA_NOT_FOUND | 返回错误，不重试 | 股票代码无效或数据不可用 |
| NETWORK_ERROR | 重试一次 | 网络超时或API不可达 |
| TIMEOUT | 重试一次 | 执行超时 |
| EMPTY_OUTPUT | 重试一次 | 输出为空或无效 |

## 报告输出

- **路径**: `./output/institutional-accumulation-analysis/机构操作分析-{date}-{ticker}.md`
- **格式**: Markdown
- **语言**: 中文

## 依赖

- **Skill**: `institutional-accumulation-analysis`
- **参考文档**: `.agents/skills/institutional-accumulation-analysis/SKILL.md`
