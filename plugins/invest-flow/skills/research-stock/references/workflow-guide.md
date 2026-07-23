# 多Agent协同分析 - Prompt-Native 工作流指南

> 当前实现以 agent 会话（Codex / Claude Code）内 prompt 编排为准。`scripts/orchestrator.py` 只生成 prompt plan 和 orchestration JSON，方便检查或 handoff，不负责执行子 skill。

## 当前执行路径

```text
用户请求
  -> agent 解析 ticker/company
  -> agent 执行五段默认子 skill prompt
  -> 每个子 skill 保存 Markdown 子报告并返回 report_path
  -> agent 校验每个维度 report_path 和 handoff
  -> Composer 汇总已有 report_path + handoff
  -> 中文综合报告
```

## 阶段说明

### 阶段1: Request -> Planner

- 输入：ticker/company
- 输出：`stock_decision_basic` 计划
- 默认包含五个分析维度：
  - `research-profile`
  - `research-fundamentals`
  - `research-institutional`
  - `research-reflexivity`
  - `research-reportify`

### 阶段2: Planner -> Prompt Plan

Registry 为五个默认维度生成 prompt template：

```text
使用 invest-flow:research-profile 分析 {ticker} / {company}，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
使用 invest-flow:research-fundamentals 分析 {ticker}
使用 invest-flow:research-institutional 分析 {ticker}
使用 invest-flow:research-reflexivity 对 {ticker} 做深度反身性分析
使用 invest-flow:research-reportify 分析 {ticker}
```

这些 prompt 由当前 agent 会话依次执行。Python 层不会启动外部 agent 进程。

用户明确指定报告期或出现相关新财报事件时，可额外调用 `research-earnings`。它不属于默认五阶段。默认流程不得调用 `chain-alpha-entry-plan`。

实际执行时，每个 prompt 都必须附加落盘要求：保存 Markdown 子报告到对应 `output/<skill-name>/` 目录，并在回复末尾明确写出 `report_path`。只返回对话内容或 handoff 不能算该维度完成。

### 阶段3: 子 Skill -> Handoff

每个子 skill 完成后，先校验并保留：

- 子报告路径 `report_path`
- 核心结论
- 操作建议
- 置信度
- 关键证据
- 风险信号
- 分歧点
- 监控指标
- 数据缺口

`report_path` 必须指向该子 skill 生成的 Markdown 文件。若缺失，MainAgent 应先补跑该子 skill；只有补跑失败或用户明确允许部分结果时，才可进入 Composer，并在综合报告中标注缺失原因。

`research-profile` 的 handoff 额外包含 `company_profile` 结构化字段。Composer 使用该字段生成 `## 公司画像摘要`；如果 `company_profile` 缺失，则渲染公司画像状态行，而不是用其他 handoff 字段回填。若 `research-profile` 阶段失败，Composer 会明确警告缺少公司画像会降低整体判断可信度。

### 阶段4: Handoff -> Composer

Composer 根据成功或部分成功的 handoff 生成：

- `output/research-stock/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`
- `output/research-stock/research-stock-{TICKER}-{YYYY-MM-DD}.md`

如果只是生成 prompt plan，则输出：

- `output/research-stock/prompt-plan-{TICKER}-{YYYYMMDD-HHMMSS}.md`
- `output/research-stock/orchestration-{TICKER}-{YYYYMMDD-HHMMSS}.json`

综合报告固定作者字段：`InvestmentFlow`。

## 推荐入口

在 Codex 或 Claude Code 中说：

```text
使用 invest-flow:research-stock 分析 MRVL
```

然后 agent 应执行：

```text
使用 invest-flow:research-profile 分析 MRVL / MRVL，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
使用 invest-flow:research-fundamentals 分析 MRVL
使用 invest-flow:research-institutional 分析 MRVL
使用 invest-flow:research-reflexivity 对 MRVL 做深度反身性分析
使用 invest-flow:research-reportify 分析 MRVL
```

执行时必须要求每个子 skill 保存子报告并返回 `report_path`；不得把 subagent 对话摘要直接当作子报告。

如果用户提供公司名：

```text
使用 invest-flow:research-profile 分析 MRVL / Marvell Technology，输出公司画像、核心业务、技术壁垒、产业链位置、AI 相关性、竞争格局和行业地位
```

## Python Helper

从仓库根目录运行：

```bash
python plugins/invest-flow/skills/research-stock/scripts/orchestrator.py MRVL --company "Marvell Technology"
```

该命令只生成 prompt plan。适用场景：

- 调试 registry 是否生成了正确 prompt
- 在外部文档中交接待执行计划
- 将已有 handoff 交给 Composer 汇总前检查结构

## 部分结果处理

- 五个默认维度都完成：输出完整综合报告。
- 只有部分维度完成：先补跑缺失子报告；补跑失败或用户允许部分结果时，输出报告并标注缺失维度、缺失子报告路径和数据缺口。
- 五个默认维度都缺失：只输出 orchestration JSON 或 prompt plan，不输出投资结论。

## 综合报告原则

1. 不把单一维度结论当成最终结论。
2. 公司画像、基本面、资金流、反身性和 Reportify 结论一致时才提高置信度。
3. 结论冲突时优先写清冲突来源，而不是强行平均。
5. 所有高置信度建议必须附带触发重新评估的监控信号。
6. 子维度 handoff 不能替代子报告；综合报告必须有子报告索引。
