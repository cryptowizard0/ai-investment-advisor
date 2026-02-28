---
name: fundamental-analysis
description: "基础分析 (Fundamental Analysis) - 针对个股的深度基本面与技术面分析。涵盖行业定位、核心指标、财务估值、催化剂分析及技术面判断。适用于：(1) 个股基本面分析, (2) 生成投资研究报告, (3) 评估公司商业模式, (4) 结合技术面给出投资建议。生成综合分析报告并保存至 ./output/fundamental-analysis/ 目录。"
---

# Fundamental Analysis (基础分析)

## Overview

本 skill 提供一个标准化的基本面分析流程，按模板生成结构化研究报告。

- 输出目录：`./output/fundamental-analysis/`
- 输出格式：Markdown（`.md`）

## Quick Start

1. 确认分析目标（Ticker + 公司名）。
2. 按 Workflow 收集数据并完成分析。
3. 使用 `references/report-template.md` 输出报告并保存到 `./output/fundamental-analysis/`。

## Workflow（可执行）

### 1. 输入识别
- 判断 `target` 是 `ticker` 还是 `theme`。
- `ticker` 规则：`^[A-Za-z0-9][A-Za-z0-9.\\-=]{0,19}$`。

### 2. 数据收集
- 公司与行业：业务模式、竞争格局、行业位置。
- 财务与估值：TTM/最新季度、利润率、ROE/ROA、P/E/P/S/P/B/EV-Rev。
- 技术指标：价格位置、52周区间、MA50/MA200、RSI、MACD。
- 事件催化：财报、指引、产品、监管、宏观。

### 3. 分析与策略
- 从增长、盈利质量、估值、技术结构四个维度形成综合判断。
- 输出适合投资者类型、交易/中线策略、失效条件与复核点。

### 4. 报告落盘
- 目录不存在时自动创建。
- 命名规范：
  - 单票：`{TICKER}-{company-name}-{YYYY-MM-DD}.md`
  - 主题：`{theme}-theme-{YYYY-MM-DD}.md`
  - 降级：`{target}-fallback-{YYYY-MM-DD}.md`
- 重名自动追加 `(1)`, `(2)`。

## Manual Deep Dive（可选）

当需要比自动脚本更细粒度的研究时，使用模板扩展：
- 模板：`references/report-template.md`
- 按模板补充公司定位、催化剂、风险、交易策略等定性内容。

## Resources

### references/
- `report-template.md`: 人工深度扩写模板
