# Decision Policy (V1)

适用前提：
- 已拿到 `fundamental` / `institutional` / `gie` 三份报告（允许个别缺失，但要记录 `missing_dimensions`）。
- 本策略只定义**汇总决策**，不定义子 skill 的分析方法。

## 1) Score Formula

```text
total_score =
  0.35 * fundamental_score +
  0.25 * flow_score +
  0.30 * gie_score +
  0.10 * risk_overlay
```

其中：
- `fundamental_score`: 0~100
- `flow_score`: 0~100（由原始 -100~100 映射）
- `gie_score`: 0~100
- `risk_overlay`: 0~100（风险惩罚后）

### 缺失数据默认值

- 任一维度缺失时默认 `50` 分（中性）
- 每缺失一个关键维度，`confidence` 额外 `-10`
- `available_reports_count` 记录成功读取的子报告数量（0~3）

## 2) Rating Thresholds (Aggressive)

- `BUY`: `total_score >= 70`
- `WATCH`: `55 <= total_score < 70`
- `AVOID`: `total_score < 55`

## 3) Confidence

```text
confidence = 60
           + consistency_bonus
           + data_quality_adjustment
           - 10 * missing_dimensions_count
```

- `consistency_bonus`：跨维度分差 <= 20 时 +15，否则 0
- `data_quality_adjustment`：
  - high: +10
  - medium: 0
  - low: -15
- 最终限幅：`30~95`
- 若 `missing_dimensions_count >= 2` 且评级为 `BUY`，降级为 `WATCH`

## 4) Position Size (Aggressive)

- 高置信度（>=80）：`8%~12%`
- 中置信度（60~79）：`4%~8%`
- 低置信度（<60）：`0%~3%`
- 若 `risk_flags` 包含 `event_risk_high`，上限减 `2%`
- 若评级为 `AVOID`，上限进一步约束到 `1%`

## 5) Mandatory Invalidation Conditions

1. 基本面失效：核心增长指标连续两个观察窗恶化  
2. 资金面失效：flow 评分跌破阈值并持续  
3. 价格面失效：跌破策略止损线  
4. 事件失效：监管/政策/供需逻辑逆转  

## 6) Evidence Rules

- 正常场景下，决策结论至少要引用 2 份子报告直接证据。
- 若三份报告中存在明显冲突（例如一份强烈看多、一份强烈看空），必须在最终报告显式列为“冲突项”并下调置信度。
- 所有默认值、缺失维度、降级判断必须写入 `data_limitations`。

### 证据不足降级（强制）

- `required_evidence_count = min(2, available_reports_count)`
- 若 `available_reports_count = 0`：
  - `rating = AVOID`
  - `confidence <= 35`
- 若 `available_reports_count = 1`：
  - `rating` 最高只能为 `WATCH`
  - `confidence <= 55`
- 若 `available_reports_count >= 2`：
  - 按常规阈值执行评级与仓位规则
