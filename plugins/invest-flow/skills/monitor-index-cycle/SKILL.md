---
name: monitor-index-cycle
description: "Create, verify, and update stock-index bull/bear market cycle tables using close-to-close reversal thresholds, turning-point dates, duration, amplitude, P/E at extrema, evidence-backed causes, and explicit data-cutoff dates. Use for requests such as 指数牛熊周期表, 更新牛市/熊市历史, 判断指数是否进入牛市或熊市, 跟踪 SOX/纳指/科创板等指数周期, or maintaining existing market-cycle Markdown reports."
---

# Index Bull/Bear Cycle Tracking

建立或原地更新指数牛熊周期表。价格周期统一用收盘价确认；P/E 只记录峰谷估值，不参与牛熊判定。

输出目录：`./output/monitor-index-cycle/`

- 牛市：`monitor-index-cycle-bull-{CODE}.md`
- 熊市：`monitor-index-cycle-bear-{CODE}.md`

文件名保持稳定，分析日期与行情截止日写在正文中，后续直接更新同一文件。

## 运行频率与报告触发

- **固定频率**：每个交易日收盘后执行一次轻量状态检查，使用最新完整交易日的收盘价核对 close-to-close 反转阈值。
- **完整报告触发**：仅当牛熊状态发生变化，或预先安排的定期复核需要刷新证据、估值和成因时，才更新完整周期报告。
- 状态未变化且不在定期复核点时，只记录轻量检查结果，不生成重复的完整报告。

## Web Research Routing

- 需要联网时优先使用当前会话可用的 Firecrawl search/scrape skill；不可用或失败时回退到 web search/browser。
- 价格优先指数公司或交易所官方 EOD 历史数据；P/E 使用同一供应商、同一算法的指数级序列。
- 新闻只用于解释原因，不得用二手报道替代价格与估值原始数据。

## Workflow

### 1. 锁定标的和现有状态

- 确认指数名称、代码、时区、分析日期、最新完整交易日和阈值（默认 20%）。
- 若已有报告，先读取牛市和熊市两个文件，确认最后一个已完成极值和当前周期方向。
- 若是新指数，从 `assets/` 复制两个模板，替换占位符后再填表。

### 2. 获取单一价格序列

- 下载未经混源的日频 EOD 收盘序列；更新现有表时至少覆盖最后一个已确认峰/谷至截止日。
- 对拆分、指数重定基或异常零值做检查。不得把 ETF 价格与指数价格拼接。
- 将数据整理为至少含 `date,close` 的 CSV。

### 3. 计算峰谷和当前周期

先完整阅读 `references/methodology.md`，再运行：

```bash
python plugins/invest-flow/skills/monitor-index-cycle/scripts/calculate_cycles.py \
  --prices-file prices.csv \
  --seed-kind bull \
  --as-of 2026-07-20 \
  --format markdown
```

- `--seed-kind bull`：CSV 首行是已知谷底；`bear`：首行是已知峰值；完整长历史可用 `auto`。
- 脚本只计算价格周期，不计算 P/E、原因或均值。
- 复核原始极值价格和公式，不要只复制脚本输出。

### 4. 补充 P/E 与原因

- 记录峰谷当日的指数级 TTM P/E；起始值、结束值和历史比较必须同源同口径。
- 无日频观测时可在极短区间内按价格比例估算，但必须标记 `≈`、写明公式与“盈利不变”假设。
- **P/E 回撤不能判定熊市，P/E 上涨也不能判定牛市。** 牛熊确认只看指数收盘价。
- 用当期公开资料解释主要驱动，并区分已证实事实、媒体归因和自己的推断。

### 5. 原地更新两个报告

- 已完成周期：终止日写真实峰/谷日；持续天数按自然日差；幅度按峰谷收盘价计算。
- 当前周期：终止日列写“截至截止日的最高/最低收盘日”，并在脚注明尚未确认最终极值。
- 历史均值只包含已完成周期；当前未完成周期不得纳入。
- 正文顶部同时标注“分析日期”和“行情数据截至日期”。
- 若 20% 反转已确认，关闭上一周期，并在另一张表新增从该峰/谷回溯开始的当前周期。

### 6. 验证

- 独立复算：幅度、持续天数、20% 阈值和最新回撤。
- 检查牛市终点是否与熊市起点一致、熊市终点是否与下一轮牛市起点一致。
- 检查当前行没有误纳入历史均值，文件名没有日期，且报告中的截止日为最新完整交易日。
- 每个关键数字和原因都应有来源；无法确认时写“不确定”。

## Output Requirements

- 中文输出；保留 P/E、EOD 等常用英文术语。
- 必须包含：统计日期、数据截止日、完整周期表、当前状态、计算依据、P/E 口径、原因与来源、免责声明。
- 免责声明：`本表为公开数据的客观整理与周期统计，不构成投资建议。`

## Resources

- `scripts/calculate_cycles.py`：用日频收盘价和反转阈值识别已完成及当前牛熊周期。
- `references/methodology.md`：确认规则、边界条件、P/E 与均值口径、更新检查表。
- `assets/monitor-index-cycle-bull-template.md`：新指数牛市表模板。
- `assets/monitor-index-cycle-bear-template.md`：新指数熊市表模板。
