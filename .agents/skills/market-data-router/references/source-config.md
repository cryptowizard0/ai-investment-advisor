# 数据源配置说明

本 skill 只定义路由与规范，具体 API Key 由调用方提供。
默认支持从项目根目录的 `.env` 自动读取。

## 环境变量建议

```
POLYGON_API_KEY=your_key
ALLTICK_API_KEY=your_key
YAHOO_ENABLED=true
```

## 配置建议

- **Polygon**：仅用于 US 期权与暗池/OTC
- **AllTick**：用于多市场 5m bars 与 L1
- **Yahoo**：仅作回退/补齐

## 时区与交易时段

- 统一输出为 UTC
- 市场时段由数据源返回为准
