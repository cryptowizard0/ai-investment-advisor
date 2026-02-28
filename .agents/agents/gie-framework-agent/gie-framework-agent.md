---
name: gie-framework-agent
description: 使用 GIE (Global Investment Evaluation) 投资框架评估目标公司，从宏观环境、供需趋势、铲子识别、财务穿透、估值择时和反FOMO检查六个维度进行综合分析。
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

# GIE Framework Agent

## 概述

使用 GIE (Global Investment Evaluation) 投资框架评估目标公司，从宏观环境、供需趋势、铲子识别、财务穿透、估值择时和反FOMO检查六个维度进行综合分析。

## 输入 (Input Schema)

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| ticker | string | 是 | 股票代码（如 TSLA） |
| company_name | string | 是 | 公司名称（如 Tesla） |
| analysis_type | string | 否 | 分析类型（默认 "full"） |

## 输出 (Output Schema)

```json
{
  "report_path": "string",
  "shovel_tier": "string",
  "investment_rating": "string",
  "position_size": "string",
  "entry_range": "string",
  "stop_loss": "string"
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

- **路径**: `./output/gie-investment-framework/gie-{title}-{date}.md`
- **格式**: Markdown
- **语言**: 中文

## 依赖

- **Skill**: `gie-investment-framework`
- **参考文档**: `.agents/skills/gie-investment-framework/SKILL.md`
