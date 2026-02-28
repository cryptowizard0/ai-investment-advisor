# Contracts

## 1) Input Contract: `sub_reports_v1`

Chief 的输入来自三份子报告文件（而非子脚本返回值）：

```json
{
  "schema_version": "sub_reports_v1",
  "target": "TSLA",
  "as_of_date": "2026-02-28",
  "run_context": {
    "run_id": "20260228-TSLA-001",
    "started_at": "2026-02-28T09:30:00+08:00",
    "selection_window_minutes": 180
  },
  "reports": {
    "fundamental": {
      "status": "success|failed|missing",
      "report_path": "./output/fundamental-analysis/xxx.md",
      "full_text": "...",
      "updated_at": "2026-02-28T09:45:00+08:00",
      "error_reason": ""
    },
    "institutional": {
      "status": "success|failed|missing",
      "report_path": "./output/institutional-accumulation-analysis/xxx.md",
      "full_text": "...",
      "updated_at": "2026-02-28T09:42:00+08:00",
      "error_reason": ""
    },
    "gie": {
      "status": "success|failed|missing",
      "report_path": "./output/gie-investment-framework/xxx.md",
      "full_text": "...",
      "updated_at": "2026-02-28T09:48:00+08:00",
      "error_reason": ""
    }
  }
}
```

### Report Selection Rules

- 只读取 `started_at` 之后、且在 `selection_window_minutes` 时间窗内的新报告。
- 必须满足“目标匹配”（ticker/theme 关键字命中文件名或报告正文标题）。
- 若同一维度出现多份候选，取 `updated_at` 最新的文件。
- 若无可用候选，`status=missing` 且必须填写 `error_reason`（例如 `not_found_in_run_window`）。
- 若读取失败，`status=failed` 且必须填写 `error_reason`（例如 `file_unreadable`、`parse_failed`）。

## 2) Derived Contract: `analysis_snapshot_v1`

由 `sub_reports_v1` 提取得到的统一决策输入：

```json
{
  "schema_version": "analysis_snapshot_v1",
  "ticker_or_theme": "TSLA",
  "as_of_date": "2026-02-28",
  "market_scope": "US",
  "data_quality": {
    "level": "high|medium|low",
    "quality_flags": ["..."],
    "market_data": {
      "sources": ["alltick", "yahoo"],
      "errors": []
    }
  },
  "fundamental_score": 0,
  "flow_score": 0,
  "gie_score": 0,
  "key_catalysts": ["..."],
  "key_risks": ["..."],
  "missing_dimensions": ["..."],
  "available_reports_count": 0
}
```

### Field Rules

- `fundamental_score`: `0-100`（缺失时默认 50）
- `flow_score`: `0-100`（由原始 `-100~100` 线性映射，缺失时默认 50）
- `gie_score`: `0-100`（缺失时默认 50）
- `missing_dimensions`: 记录缺失维度和失败子分析
- `available_reports_count`: `0-3`，表示成功读取的子报告数量

## 3) Output Contract: `advisor_decision_v1`

```json
{
  "schema_version": "advisor_decision_v1",
  "rating": "BUY|WATCH|AVOID",
  "confidence": 0,
  "position_size_pct": {
    "min_pct": 0,
    "max_pct": 0
  },
  "entry_plan": "...",
  "stop_loss_rule": "...",
  "take_profit_rule": "...",
  "thesis": ["..."],
  "invalidation_conditions": ["..."],
  "review_schedule": "...",
  "risk_flags": ["..."],
  "data_limitations": ["..."],
  "evidence_coverage": {
    "required": 2,
    "actual": 0
  },
  "components": {
    "fundamental_score": 0,
    "flow_score": 0,
    "gie_score": 0,
    "risk_overlay": 0,
    "total_score": 0
  }
}
```

## 4) Output Files

- Markdown 报告（必需）：`./output/summary/advisor-{target}-{YYYYMMDD}.md`
- JSON 快照（可选）：`./output/summary/advisor-{target}-{YYYYMMDD}.json`
