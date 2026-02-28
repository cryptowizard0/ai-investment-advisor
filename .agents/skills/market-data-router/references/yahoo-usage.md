# Yahoo 数据使用边界

Yahoo 只用于**部分数据补齐**，不作为主链路。

## 允许用途

- 5m bars 的短窗口回填
- 主源缺失的局部补点

## 禁止用途

- 期权链
- 暗池/OTC
- L1 订单簿

## 质量标记

若使用 Yahoo：
- 必须在 `quality_flags` 中加入 `fallback_to_yahoo`

