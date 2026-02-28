---
name: chief-investment-advisor
description: "首席投资顾问 Agent（两层架构）- Chief 仅做调度与汇总，直接驱动 fundamental/institutional/GIE 三个 skill；决策层输出结构化投资结论（评级、仓位、触发条件、失效条件、复核时间）。适用于单票或板块主题的日常投顾决策。触发命令：/chief-investment-advisor ticker_or_theme。"
---

# Chief Investment Advisor

## Overview

本 Skill 采用**无脚本编排模式**，Chief 不再调用旧版批处理脚本，而是直接基于三份子报告做汇总决策。

主要步骤（固定三步）：
1. **分配任务**：并行执行 `fundamental` / `institutional` / `gie`，等待三方结果。
2. **分析结果**：三方完成后，提取共识、分歧、缺失维度，形成统一快照。
3. **生成报告**：使用模板输出 `summary` 报告（Markdown）。

输出：
- `./output/summary/advisor-{target}-{YYYYMMDD}.md`（必需）
- `./output/summary/advisor-{target}-{YYYYMMDD}.json`（可选）

## Trigger

在对话中使用：

`/chief-investment-advisor <ticker_or_theme>`

示例：
- `/chief-investment-advisor TSLA`
- `/chief-investment-advisor AI电力基础设施`

## Workflow

### Step 1) 分配任务（并行）
- 并行触发以下 skills：
  - `fundamental-analysis`
  - `institutional-accumulation-analysis`
  - `gie-investment-framework`
- 每个子 skill 必须各自产出一份 Markdown 报告文件。
- 若某子 skill 无法完成，需显式记录失败原因和缺失维度（不能静默跳过）。
- 启动时先记录 `run_context`：
  - `run_id`
  - `started_at`
  - `selection_window_minutes`（建议 180）

#### 子报告定位规则（必须）
- `fundamental`：`./output/fundamental-analysis/`
- `institutional`：`./output/institutional-accumulation-analysis/`
- `gie`：`./output/gie-investment-framework/`
- 仅接受 `started_at` 之后且在时间窗内的报告（避免混入历史结果）。
- 必须做目标匹配（ticker/theme 与文件名或标题一致）。
- 若同维度多份候选，取最新 `updated_at`。
- 无候选时标记 `missing`，并写入 `error_reason=not_found_in_run_window`。

### Step 2) 分析结果（汇总快照）
- 从三份子报告提取以下内容：
  - 评分维度：`fundamental_score` / `flow_score` / `gie_score`
  - 关键催化剂：`key_catalysts`
  - 关键风险：`key_risks`
  - 缺失维度：`missing_dimensions`
  - 数据质量：`data_quality`
  - 可用报告数：`available_reports_count`
- 按 `references/contracts.md` 生成 `analysis_snapshot_v1`。
- 若某子报告缺失：
  - 将该维度加入 `missing_dimensions`
  - 该维度先用 `50` 作为中性默认分
  - 在最终报告的“数据限制”中注明原因
- 若 `available_reports_count < 2`：
  - 进入证据不足降级模式（详见 `decision-policy.md`）
  - 明确标注“证据覆盖不足”

### Step 3) 生成报告（模板）
- 使用 `assets/advisor-template.md` 填充并输出最终报告。
- 报告必须包含：
  1. 分析层执行概览（完成度、数据质量、限制项）
  2. 三大子分析完整汇总（Fundamental / Institutional / GIE）
  3. 交叉验证（共识、冲突、未覆盖维度）
  4. 决策层结论（评级、仓位、触发条件、失效条件、复核）
  5. 附录（子报告路径与关键原文片段）

## Decision Rules (V1)

- `total_score = 0.35*fundamental + 0.25*flow + 0.30*gie + 0.10*risk_overlay`
- 阈值（进取型）：
  - `BUY`: `>= 70`
  - `WATCH`: `55 ~ 69.99`
  - `AVOID`: `< 55`
- 缺失关键维度惩罚：
  - 每缺 1 项，置信度 `-10`
  - 缺失 >= 2 项时，`BUY` 降级为 `WATCH`
- 证据门槛：
  - 正常要求至少 2 份子报告直接证据
  - 若可用报告少于 2 份，按可用数量下调门槛并触发评级/置信度上限约束

## Resources

- `references/contracts.md`: 输入/输出契约定义
- `references/decision-policy.md`: 决策规则和边界条件
- `assets/advisor-template.md`: 报告模板
