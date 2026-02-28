---
name: fundamental-analysis-agent
description: 执行全面的基本面分析，包括公司概况、财务指标、估值分析、技术面指标以及催化剂和风险评估。
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

# Fundamental Analysis Agent

## 概述

执行全面的基本面分析，包括公司概况、财务指标、估值分析、技术面指标以及催化剂和风险评估。

## 输入 (Input Schema)

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| ticker | string | 是 | 股票代码（如 TSLA） |
| company_name | string | 是 | 公司名称（如 Tesla） |
| analysis_date | string | 否 | 分析日期（ISO 8601 格式） |

## 输出 (Output Schema)

```json
{
  "report_path": "string",
  "stock_type": "string",
  "key_metrics": {
    "current_price": "number",
    "pe_ratio": "number",
    "market_cap": "string"
  },
  "key_findings": {
    "trading_strategy": "string",
    "investment_strategy": "string"
  }
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

- **路径**: `./output/fundamental-analysis/{ticker}-{company_name}-{date}.md`
- **格式**: Markdown
- **语言**: 中文

## 依赖

- **Skill**: `fundamental-analysis`
- **参考文档**: `.agents/skills/fundamental-analysis/SKILL.md`
