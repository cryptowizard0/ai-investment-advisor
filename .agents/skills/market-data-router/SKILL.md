---
name: market-data-router
description: "稳定金融数据源路由与降级策略。美股优先，分钟级(5m)行情，L1订单簿，期权/暗池用Polygon，Yahoo用于部分回填/兜底，港股/A股/期货降级处理。"
---

# Market Data Router (稳定数据源路由)

本 skill 用于**稳定获取分钟级/小时级/日级金融数据**并做**多数据源路由与降级**，满足：
- 美股优先（5m/1h/1d K 线 + L1 订单簿 + 期权 + 暗池）
- 港股/A股/期货降级（只保证 5m/1h/1d K 线）
- Yahoo 作为“部分数据补齐/兜底”

> 数据源选择与降级规则见 `references/provider-matrix.md`

## 输入

- `market`: `US` / `HK` / `CN` / `FUT`
- `symbol`: 交易标的（如 `TSLA` / `0700.HK` / `000001.SZ` / `ES`）
- `interval`: `5m` / `1h` / `1d` / `auto` (根据时间跨度自动选择)
- `data_types`: `bars` / `l1` / `options` / `darkpool`
- `time_range`: 起止时间（UTC 或市场本地时区）

## 核心策略（摘要）

- **美股期权 + 暗池**：只用 `Polygon`（主源）
- **美股 5m bars + L1**：优先 `AllTick`，失败则用 `Yahoo`（部分数据兜底）
- **港股 / A股 5m bars**：优先 `AllTick`，缺失则标记不可用（不伪造）
- **期货 5m bars**：优先 `AllTick`，如不可用再用 `Yahoo`（仅限其可覆盖品种）

## 执行流程

1. **加载配置**
   - 读取 `references/source-config.md` 中说明的环境变量或配置文件
   - 若关键 key 缺失：进入降级路径（不报错但标记 `quality_flags`)

2. **根据市场/数据类型选源**
   - 使用 `references/provider-matrix.md` 的路由表

3. **获取数据并标准化**
   - 统一输出字段格式（见 `references/field-schema.md`）
   - 支持 `5m` / `1h` / `1d`：若数据源仅提供 5m，则按请求粒度聚合

## 自动间隔选择 (auto)

- 规则：
  - 时间跨度 ≤ 10 天 → `5m`
  - 时间跨度 ≤ 60 天 → `1h`
  - 时间跨度 > 60 天 → `1d`
- 使用方式：`--interval auto`
- 可选参数：`--explain` 输出自动选择理由到 stderr

## 输出补充字段

`metadata` 中新增：
- `interval_mode`: `auto` / `manual`
- `auto_interval`: `{"selected": "...", "span_days": ...}`（仅 auto 模式）

4. **质量检查**
   - 缺失 bar 比例 > 5%：触发降级
   - 关键字段缺失：标记 `quality_flags`

5. **降级与回退**
   - 按 `references/fallback-policy.md` 执行
   - Yahoo 仅用于**部分数据补齐/兜底**

6. **缓存**
   - 建议缓存到 `./output/cache/market-data/`（如不存在可创建）
   - 缓存命中优先级 > 远端请求

## 输出

输出为统一结构（JSON/CSV/DF 皆可），包含：
- `source`（实际使用的数据源）
- `quality_flags`（缺失/降级/回退记录）
- 标准字段（见 `references/field-schema.md`）

## 资源

- `scripts/fetch_market_data.py`：主脚本，输出统一 JSON 格式
- `references/provider-matrix.md`：路由矩阵与降级策略
- `references/field-schema.md`：统一字段规范
- `references/fallback-policy.md`：缓存、重试、降级细则
- `references/source-config.md`：API key 与配置说明
- `references/yahoo-usage.md`：Yahoo 作为部分数据源的使用边界
