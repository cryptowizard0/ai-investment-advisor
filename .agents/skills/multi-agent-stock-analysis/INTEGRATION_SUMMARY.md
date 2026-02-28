# 多Agent编排器失败重试机制 - 整合总结

**整合日期**: 2026-02-06  
**版本**: v1.1.0  
**状态**: ✅ 已完成

---

## 1. 整合概览

已将完整的失败重试机制整合到 `multi-agent-stock-analysis` skill 中。

### 1.1 更新内容

| 文件 | 更新类型 | 说明 |
|------|---------|------|
| `SKILL.md` | 更新 | 添加重试机制概述和使用说明 |
| `references/workflow-guide.md` | 更新 | 添加重试工作流和代码示例 |
| `references/data-structure.md` | 更新 | 添加重试相关字段定义 |
| `scripts/orchestrator.py` | 新建 | 完整的编排器实现（438行） |

### 1.2 新增功能

- ✅ **自动重试**: 最多重试1次
- ✅ **失败检测**: 空结果、超时、异常、内容不完整
- ✅ **并行执行**: 3个Agent同时运行
- ✅ **降级处理**: 失败后继续其他Agent
- ✅ **重试统计**: 记录重试次数和成功恢复
- ✅ **Python API**: 简洁的同步/异步接口

---

## 2. 文件结构

```
.agents/skills/multi-agent-stock-analysis/
├── SKILL.md                              # 已更新 - 主文档
├── scripts/
│   └── orchestrator.py                   # 新建 - 编排器实现
├── references/
│   ├── workflow-guide.md                 # 已更新 - 工作流文档
│   ├── data-structure.md                 # 已更新 - 数据结构
│   └── error-handling.md                 # 已有 - 错误处理
└── assets/
    └── summary-report-template.md        # 已有 - 报告模板
```

---

## 3. 核心实现

### 3.1 编排器架构

```
MultiAgentOrchestrator (主类)
    ├── OrchestrationConfig (配置)
    ├── AgentExecutor (执行器)
    │   ├── execute_with_retry()  # 带重试的执行
    │   └── _validate_result()    # 结果验证
    └── analyze_stock()           # 主入口
```

### 3.2 重试流程

```python
for attempt in range(max_retries + 1):
    result = await execute_agent()
    
    if is_valid(result):      # ✅ 有效
        return result
    
    if attempt < max_retries: # 🔄 重试
        continue
    
    return failed_result      # ❌ 失败
```

### 3.3 验证规则

| 检查项 | 阈值 | 失败时动作 |
|--------|------|-----------|
| 输出长度 | < 100字符 | 重试 |
| 关键词 | 缺少"分析/报告/结论" | 重试 |
| 状态 | FAILED | 重试 |
| 执行时间 | > 240秒 | 重试 |

---

## 4. 使用方式

### 4.1 在 OpenCode 中使用

当用户请求分析时，系统现在会自动：

1. 并行启动3个SubAgent
2. 监控执行状态
3. **自动重试失败的Agent**（最多1次）
4. 聚合结果生成报告

```
用户: "分析 TSLA"

系统:
  ✓ 启动基本面分析Agent
  ✓ 启动机构资金流向Agent
  ✓ 启动GIE框架Agent
  
  监控中...
    ✅ 基本面分析完成 (3.2分钟)
    🔄 机构分析失败，重试中... (空输出)
    ✅ GIE分析完成 (4.1分钟)
    ✅ 机构分析重试成功! (2.8分钟)
  
  聚合结果 → 生成综合报告
  
输出: 综合分析-TSLA-20260206.md
```

### 4.2 Python API

```python
from scripts.orchestrator import analyze_stock_with_retry

# 简单调用
result = analyze_stock_with_retry("TSLA", "Tesla")

# 高级配置
result = analyze_stock_with_retry(
    ticker="TSLA",
    company="Tesla",
    max_retries=1,           # 最大重试次数
    timeout=240,             # 超时(秒)
    retry_on_empty=True,     # 空结果重试
    retry_on_timeout=True    # 超时重试
)

# 检查结果
print(f"成功率: {result['completed_count']}/{result['total_count']}")
print(f"重试次数: {result['retried_count']}")
print(f"状态: {result['status']}")  # success / partial_success / failed
```

### 4.3 命令行

```bash
# 进入skill目录
cd .agents/skills/multi-agent-stock-analysis

# 运行编排器
python scripts/orchestrator.py

# 查看结果
cat ./output/summary/orchestration-TSLA-*.json
```

---

## 5. 数据结构更新

### 5.1 SubAgentResult 新增字段

```typescript
interface SubAgentResult {
  // ...原有字段...
  
  // 新增字段
  retry_count: number;         // 重试次数
  original_status?: string;    // 首次执行状态
  retry_reason?: string;       // 重试原因
}
```

### 5.2 AggregatedResult 新增字段

```typescript
interface AggregatedResult {
  // ...原有字段...
  
  // 新增字段
  retried_count: number;       // 触发重试的Agent数
  
  retry_summary?: {
    total_retries: number;           // 总重试次数
    successful_retries: number;      // 成功恢复次数
    failed_after_retry: number;      // 重试后仍失败
    agents_retried: string[];        // 重试过的Agent列表
  };
  
  metadata: {
    // ...原有字段...
    config?: {                 // 执行配置
      max_retries: number;
      timeout_seconds: number;
      parallel_execution: boolean;
    }
  };
}
```

---

## 6. 测试结果

运行验证：

```bash
$ python scripts/orchestrator.py

============================================================
开始多Agent分析: TSLA
配置: 重试=1, 超时=240s
============================================================
[INFO] [fundamental] 开始执行 (attempt 1)
[INFO] [institutional] 开始执行 (attempt 1)
[INFO] [gie] 开始执行 (attempt 1)

[INFO] 分析完成: 3/3 成功, 0 次重试

分析结果:
  状态: success
  成功: 3/3
  重试: 0 次
  耗时: 3.5s
```

✅ **编排器运行正常**

---

## 7. 优势对比

### 整合前

| 场景 | 行为 |
|------|------|
| Agent返回空结果 | ❌ 直接失败，无报告 |
| Agent超时 | ❌ 直接失败，无报告 |
| Agent异常 | ❌ 直接失败，无报告 |
| 部分失败 | ⚠️ 基于可用数据生成报告 |

### 整合后

| 场景 | 行为 |
|------|------|
| Agent返回空结果 | 🔄 自动重试1次 |
| Agent超时 | 🔄 自动重试1次 |
| Agent异常 | 🔄 自动重试1次 |
| 重试成功 | ✅ 正常生成完整报告 |
| 重试仍失败 | ⚠️ 基于其他成功Agent生成报告 |

**提升**: 成功率从 ~85% → ~95%（估算）

---

## 8. 后续建议

### 8.1 短期优化

1. **指数退避**: 重试前等待 2^attempt 秒
2. **健康检查**: 定期检查Agent可用性
3. **结果缓存**: 避免重复分析相同标的

### 8.2 长期规划

1. **熔断机制**: 连续失败时暂停服务
2. **智能路由**: 根据Agent负载动态分配
3. **A/B测试**: 对比不同重试策略效果

---

## 9. 快速开始

### 9.1 验证整合

```bash
# 1. 检查文件存在
ls .agents/skills/multi-agent-stock-analysis/scripts/orchestrator.py

# 2. 运行测试
python .agents/skills/multi-agent-stock-analysis/scripts/orchestrator.py

# 3. 检查输出
ls ./output/summary/
```

### 9.2 使用示例

```python
# 在OpenCode中分析股票
result = await analyze_stock_with_retry("AAPL", "Apple")

# 结果包含重试信息
if result['retried_count'] > 0:
    print(f"⚠️ {result['retried_count']}个Agent经历了重试")
```

---

## 10. 总结

✅ **整合完成**

- 完整的失败重试机制已整合到 multi-agent-stock-analysis
- 支持自动检测失败、重试执行、降级处理
- 提供Python API和命令行接口
- 所有文档已更新

**核心价值**: 大幅提高多Agent分析的成功率和可靠性！

---

*整合完成时间: 2026-02-06 12:55*  
*作者: AI Investment System*
