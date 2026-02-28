# 统一字段规范 (Normalized Schema)

## Bars (5m / 1h / 1d)

必需字段：
- `timestamp` (ISO8601, UTC)
- `open`, `high`, `low`, `close` (float)
- `volume` (int)
- `symbol`, `market`
- `source` (string)
- `quality_flags` (list)

可选字段：
- `vwap` (float)
- `trades` (int)
- `currency` (string)

## L1 订单簿

必需字段：
- `timestamp` (ISO8601, UTC)
- `bid`, `ask` (float)
- `bid_size`, `ask_size` (int)
- `symbol`, `market`
- `source` (string)
- `quality_flags` (list)

可选字段：
- `mid` (float)
- `spread` (float)

## Options / Darkpool

### Options
- `timestamp`, `symbol`, `contract`, `strike`, `expiry`, `type` (C/P)
- `last`, `bid`, `ask`, `volume`, `open_interest`
- `source`, `quality_flags`

### Darkpool/OTC
- `timestamp`, `symbol`, `price`, `size`
- `venue` (如可用), `source`, `quality_flags`

## 质量标记 (quality_flags) 约定

- `fallback_to_yahoo`
- `missing_bars`
- `missing_l1`
- `options_unavailable`
- `darkpool_unavailable`
- `partial_data`
- `aggregated_from_5m`

## Metadata 补充字段

- `interval_mode`: `auto` / `manual`
- `auto_interval`: `{"selected": "...", "span_days": ...}`（仅 auto）
