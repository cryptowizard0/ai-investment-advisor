---
name: monitor-nhnl-bottom
description: "Elder-style NH-NL breadth state machine for major-bottom detection and top-exhaustion warning on an index or sector universe: 250-day new-high/new-low counts, capitulation spikes, valid bullish divergences, bull-confirmation thresholds rescaled by universe size, plus index-level Impulse/value-zone/false-breakout reads. Use for 探底状态机, 新高新低指标, NH-NL 宽度分析, 判断大底/投降/牛市确认, 判断当前处于熊市开端还是牛市回调, or monitoring SOX/纳指/行业指数 breadth."
---

# NH-NL Breadth Bottom State Machine

基于埃尔德《以交易为生 II：卖出的艺术》第 10 章"探索底部"（Groping for a Bottom）的宽度状态机：对一个指数/行业样本自算 250 日新高−新低（NH-NL），把书中面向全美股的绝对阈值等比换算到任意样本规模，输出"当前处于探底状态机哪个阶段"的可复核判定。既判大底（S1-S4），也报顶部预警（新高衰竭）。

输出目录：`./output/monitor/`，命名：`monitor-nhnl-bottom-{LABEL}-{YYYY-MM-DD}.md`（LABEL 如 SOX；文件已存在则加 `(1)` 后缀，不覆盖）。

## 核心口径（不可混用）

- NH/NL：复权收盘价 > / < 此前 252 个交易日极值；上市不足 252 日的成员当日不计入分母。
- 周线 NH-NL = 日值 **5 日滚动求和**（不是"周线图上的周末值"）。
- 比率化：`weekly_ratio = Σ5日(日净值/当日可判家数)`，取值 [-5, +5]，用于跨样本移植阈值。
- 阈值（比率 | 折算到 N 家样本的家次 = 比率 × N）：投降线 −0.571（书中 −4000）、历史极限 −0.857（书中 −6000）、牛市确认 +0.357（书中 +2500）。换算是操作化取值，非书中原文。

## 状态机（P0-P6 + 判定期）

| 状态 | 判据 | 动作含义 |
|---|---|---|
| P1 投降 | 周比率 ≤ −0.571 | 平空、列购物清单，不接飞刀 |
| P2 生还 | 投降后回正（上穿 0） | 停新空，等背离 |
| P3 大底背离 | 价格新低 + 比率低点浅 ≥40% + 两底间回正 | 战略转多，允许试仓 |
| P4 战术确认 | P3 后日线 NH-NL 二次上穿新低线（双螺旋） | 买入窗口 |
| P5 牛市确认 | 近 4 周比率 ≥ +0.357 | 波段做多为主 |
| P6 牛市回调 | 26 周内有确认、当前回落未枯竭 | 回调至价值区买回 |
| P0 熊市初段 | 连续 ≥3 周零新高 且 新低已出现 | 持空/防守 |
| PX 判定期 | 零新高但也零新低 | 挂两侧触发器，等裁决 |

双螺旋交叉只在 P3 成立后才有信号意义，平时的例行交叉是噪音。

## Workflow

### 1. 确定样本与基准

- 内置 `--preset sox`（30 成分，2026-07-17 Invesco SOXQ 持仓口径；调仓后需更新脚本内清单）。
- 其他指数/行业：整理成分清单为一行一个 ticker 的文本文件，用 `--tickers-file` + `--index-symbol`。样本 <20 时先警告用户颗粒过粗。

### 2. 运行脚本

先完整阅读 `references/methodology.md`，再运行：

```bash
python plugins/invest-flow/skills/monitor-nhnl-bottom/scripts/build_nhnl.py \
  --preset sox \
  --cache-dir output/cache/market-data/nhnl-sox-$(date +%Y%m%d) \
  --format markdown
```

- 需要至少 lookback+250 个交易日历史（默认 `--start 2021-01-01`）。
- 离线复现/回测用 `--prices-file`（宽表收盘 CSV）+ `--index-file`。
- `--as-of` 可截断到历史日期做事后验证。

### 3. 人工复核（脚本不替你判断的部分）

- **S3 背离结构**：对照周线图确认两底形态与期间回正；样本小时机械判定可能漏报/误报。
- **S4 末跌缩量**：对比最后一次探底与前几次探底的成交额。
- **加权失真**：对比指数跌幅与成员中位跌幅，市值加权指数可能被一两只权重股撑住表面。
- 距离感：报告成员距各自 52 周低点的中位距离，说明投降信号结构上有多远。

### 4. 写报告

- 从 `assets/report-template.md` 复制骨架，融合脚本输出与人工复核结论。
- 必须包含：状态判定与理由、两侧触发器（恶化路径/修复路径的具体阈值与前哨个股）、历史命中回顾、口径与阈值换算说明。

### 5. 验证

- 抽查 2-3 个历史投降周：用 `--as-of` 重跑确认状态机在当时给出 P1。
- 核对最新收盘价与数据源一致；周线表末行若为进行中一周需标注。

## Output Requirements

- 中文输出；NH-NL、Impulse、EMA 等术语保留英文。
- 报告开头必须有**"一分钟白话速读"**：3-5 条大白话结论（数人头/红绿灯等比喻，不出现术语），读者只看这节就能明白状态与该做什么；技术细节放后面各节。
- 必须包含：分析日期、数据截止日、样本与口径、阈值表（比率+折算家次）、状态判定、近 8 周宽度表、历史事件、指数层读数、人工复核结论、两侧触发器。
- 免责声明：`本报告为公开数据的宽度统计与状态判读，不构成投资建议。`

## Resources

- `scripts/build_nhnl.py`：宽度计算、阈值换算、状态机、指数层读数（支持离线数据）。
- `references/methodology.md`：书中方法逐条量化、阈值换算推导、SOX 历史命中验证、边界条件。
- `assets/report-template.md`：监控报告骨架。
