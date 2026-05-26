# 多Agent协同分析 - 数据结构定义

## Phase 1 实现模型

当前代码中的数据模型位于：

`scripts/investflow_pipeline/models.py`

核心模型：

- `TaskRequest`
- `SkillSpec`
- `StageResult`
- `Handoff`
- `PipelineResult`
- `OrchestrationConfig`

历史 TypeScript interface 示例保留为设计参考；以 Python dataclass 为当前实现准绳。

## 概述

本文档定义了多Agent股票分析系统中所有数据结构的规范，确保MainAgent、SubAgent和SummaryAgent之间的数据传递一致性。

## 数据流概览

```
用户请求 → ParseRequest → TaskConfig
               ↓
         MainAgent
               ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
SubAgent1  SubAgent2  SubAgent3
    ↓          ↓          ↓
Result1    Result2    Result3
    └──────────┼──────────┘
               ↓
         AggregatedResult
               ↓
         SummaryAgent
               ↓
         SummaryResult
               ↓
         用户输出
```

## 核心数据结构

### 1. ParseRequest (解析后的请求)

```typescript
interface ParseRequest {
  ticker: string;              // 股票代码，如 "TSLA"
  company_name: string;        // 公司名称，如 "Tesla"
  analysis_type: "full" | "fundamental" | "institutional" | "gie";
  task_id: string;             // 唯一任务ID，如 "ma_20260206_001"
  timestamp: string;           // ISO 8601格式时间戳
  metadata?: {
    source: string;            // 请求来源
    user_id?: string;          // 用户标识（可选）
    priority?: number;         // 优先级（可选）
  };
}
```

**示例：**
```json
{
  "ticker": "TSLA",
  "company_name": "Tesla",
  "analysis_type": "full",
  "task_id": "ma_20260206_001",
  "timestamp": "2026-02-06T10:30:00Z",
  "metadata": {
    "source": "user_request",
    "priority": 1
  }
}
```

### 2. TaskConfig (任务配置)

```typescript
interface TaskConfig {
  task_id: string;
  ticker: string;
  company_name: string;
  subagents: SubAgentConfig[];
  timeout: number;             // 总超时时间（秒）
  retry_policy: {
    max_retries: number;
    retry_interval: number;    // 重试间隔（秒）
  };
}

interface SubAgentConfig {
  name: "fundamental" | "institutional" | "gie";
  skill: string;
  enabled: boolean;
  timeout: number;             // 单个Agent超时
  prompt_template: string;
}
```

**示例：**
```json
{
  "task_id": "ma_20260206_001",
  "ticker": "TSLA",
  "company_name": "Tesla",
  "subagents": [
    {
      "name": "fundamental",
      "skill": "fundamental-analysis",
      "enabled": true,
      "timeout": 240,
      "prompt_template": "对{ticker}执行基本面分析..."
    },
    {
      "name": "institutional",
      "skill": "institutional-accumulation-analysis",
      "enabled": true,
      "timeout": 240,
      "prompt_template": "分析{ticker}的机构资金流向..."
    },
    {
      "name": "gie",
      "skill": "gie-investment-framework",
      "enabled": true,
      "timeout": 240,
      "prompt_template": "使用GIE框架评估{ticker}..."
    }
  ],
  "timeout": 300,
  "retry_policy": {
    "max_retries": 1,
    "retry_interval": 10
  }
}
```

### 3. SubAgentResult (SubAgent结果)

所有SubAgent返回的统一格式：

```typescript
interface SubAgentResult {
  task_id: string;
  subagent_name: string;       // fundamental | institutional | gie
  status: "completed" | "failed" | "timeout" | "retrying";
  timestamp: string;
  duration: number;            // 执行时长（秒）
  
  // 重试机制相关
  retry_count: number;         // 重试次数（0表示首次）
  original_status?: string;    // 首次执行状态（如果重试过）
  retry_reason?: string;       // 重试原因
  
  // 成功时返回
  data?: {
    report_path: string;       // 报告文件路径
    key_findings: KeyFindings; // 关键发现
    key_metrics: KeyMetrics;   // 关键指标
  };
  
  // 失败时返回
  error?: {
    code: string;              // 错误代码
    message: string;           // 错误信息
    details?: any;             // 详细错误信息
    failed_attempts?: number;  // 失败尝试次数
  };
}

// 关键发现（各维度特有）
interface KeyFindings {
  // Fundamental特有
  stock_type?: "Growth" | "Value" | "Cyclical" | "Blend";
  trading_strategy?: string;
  investment_strategy?: string;
  
  // Institutional特有
  classification?: "Strong Accumulation" | "Mild Accumulation" | "Neutral" | "Early Distribution" | "Aggressive Distribution";
  confidence?: number;         // 0-100
  cost_zone?: string;          // 如 "$415-$430"
  
  // GIE特有
  shovel_tier?: "Tier 1" | "Tier 2" | "Not a Shovel";
  investment_rating?: "Strong Buy" | "Buy" | "Hold" | "Avoid";
  position_size?: string;      // 如 "15-20%"
}

// 关键指标
interface KeyMetrics {
  // 价格指标
  current_price?: number;
  pe_ratio?: number;
  ps_ratio?: number;
  market_cap?: string;
  
  // 技术指标
  rsi_14?: number;
  ma_50?: number;
  ma_200?: number;
  
  // 机构指标
  obv_trend?: "Rising" | "Falling" | "Neutral";
  cmf?: number;
  vwap?: number;
  
  // GIE指标
  orders_to_revenue?: number;
  fcf_conversion?: number;
  net_debt_ebitda?: number;
  rd_percentage?: number;
}
```

**示例 - Fundamental结果：**
```json
{
  "task_id": "ma_20260206_001_fundamental",
  "subagent_name": "fundamental",
  "status": "completed",
  "timestamp": "2026-02-06T10:45:00Z",
  "duration": 180,
  "data": {
    "report_path": "./output/fundamental-analysis/TSLA-Tesla-2026-02-06.md",
    "key_findings": {
      "stock_type": "Growth",
      "trading_strategy": "短期回调至$235可建仓",
      "investment_strategy": "长期持有，目标价$320"
    },
    "key_metrics": {
      "current_price": 406.01,
      "pe_ratio": 290,
      "market_cap": "1.4T",
      "rsi_14": 42.6
    }
  }
}
```

**示例 - Institutional结果：**
```json
{
  "task_id": "ma_20260206_001_institutional",
  "subagent_name": "institutional",
  "status": "completed",
  "timestamp": "2026-02-06T10:43:00Z",
  "duration": 165,
  "data": {
    "report_path": "./output/institutional-accumulation-analysis/机构操作分析-20260206-TSLA.md",
    "key_findings": {
      "classification": "Early Distribution",
      "confidence": 65,
      "cost_zone": "$415-$430"
    },
    "key_metrics": {
      "obv_trend": "Falling",
      "cmf": -0.05,
      "vwap": 418.5
    }
  }
}
```

**示例 - GIE结果：**
```json
{
  "task_id": "ma_20260206_001_gie",
  "subagent_name": "gie",
  "status": "completed",
  "timestamp": "2026-02-06T10:44:30Z",
  "duration": 175,
  "data": {
    "report_path": "./output/gie-investment-framework/gie-特斯拉-2026-02-06.md",
    "key_findings": {
      "shovel_tier": "Tier 1",
      "investment_rating": "Hold",
      "position_size": "5-10%"
    },
    "key_metrics": {
      "orders_to_revenue": 1.2,
      "fcf_conversion": 85,
      "net_debt_ebitda": 0.8,
      "rd_percentage": 4.5
    }
  }
}
```

### 4. AggregatedResult (聚合结果)

```typescript
interface AggregatedResult {
  task_id: string;
  ticker: string;
  company_name: string;
  analysis_date: string;
  
  status: "success" | "partial_success" | "failed";
  completed_count: number;     // 成功的Agent数量
  failed_count: number;        // 失败的Agent数量
  total_count: number;         // 总Agent数量
  retried_count: number;       // 触发重试的Agent数量（新增）
  
  // 各维度结果
  fundamental?: SubAgentResult;
  institutional?: SubAgentResult;
  gie?: SubAgentResult;
  
  // 错误信息
  errors?: {
    [agent_name: string]: {
      code: string;
      message: string;
      retry_count?: number;    // 该Agent的重试次数
    }
  };
  
  // 重试统计（新增）
  retry_summary?: {
    total_retries: number;           // 总重试次数
    successful_retries: number;      // 成功恢复次数
    failed_after_retry: number;      // 重试后仍失败次数
    agents_retried: string[];        // 重试过的Agent列表
  };
  
  // 元数据
  metadata: {
    start_time: string;
    end_time: string;
    total_duration: number;    // 总耗时（秒）
    config?: {                 // 执行配置（新增）
      max_retries: number;
      timeout_seconds: number;
      parallel_execution: boolean;
    }
  };
}
```

**示例：**
```json
{
  "task_id": "ma_20260206_001",
  "ticker": "TSLA",
  "company_name": "Tesla",
  "analysis_date": "2026-02-06",
  "status": "partial_success",
  "completed_count": 2,
  "failed_count": 1,
  "total_count": 3,
  "fundamental": { /* SubAgentResult */ },
  "institutional": { /* SubAgentResult */ },
  "errors": {
    "gie": {
      "code": "TIMEOUT",
      "message": "Task timeout after 240 seconds"
    }
  },
  "metadata": {
    "start_time": "2026-02-06T10:30:00Z",
    "end_time": "2026-02-06T10:45:00Z",
    "total_duration": 900
  }
}
```

### 5. SummaryResult (SummaryAgent结果)

```typescript
interface SummaryResult {
  task_id: string;
  ticker: string;
  company_name: string;
  analysis_date: string;
  
  // 综合分析
  recommendation: "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell";
  confidence: number;          // 0-100
  position_size: string;       // 如 "15-20%"
  
  // 价格建议
  entry_range: string;         // 如 "$380-$400"
  stop_loss: string;           // 如 "$370"
  target_price: string;        // 如 "$450-$480"
  time_horizon: string;        // 如 "6-12个月"
  
  // 一致性分析
  consistency_analysis: {
    overall: "High" | "Medium" | "Low";
    aligned_aspects: string[];    // 一致的观点
    conflicts: string[];          // 冲突点
    confluence_points: string[];  // 共振信号
  };
  
  // 风险提示
  risk_warnings: string[];
  risk_level: "Low" | "Medium" | "High";
  
  // 监控指标
  monitoring_metrics: {
    indicator: string;
    current_value: string;
    threshold: string;
    status: "Normal" | "Warning" | "Critical";
  }[];
  
  // 报告路径
  report_path: string;
  
  // 子报告路径
  sub_reports: {
    fundamental?: string;
    institutional?: string;
    gie?: string;
  };
}
```

**示例：**
```json
{
  "task_id": "ma_20260206_001_summary",
  "ticker": "TSLA",
  "company_name": "Tesla",
  "analysis_date": "2026-02-06",
  "recommendation": "Hold",
  "confidence": 70,
  "position_size": "5-10%",
  "entry_range": "$380-$400",
  "stop_loss": "$370",
  "target_price": "$450-$480",
  "time_horizon": "6-12个月",
  "consistency_analysis": {
    "overall": "Medium",
    "aligned_aspects": [
      "长期AI/机器人叙事空间被认可",
      "高估值是共同担忧"
    ],
    "conflicts": [
      "基本面看好长期 vs 机构分析短期派发"
    ],
    "confluence_points": [
      "短期调整但长期价值仍在"
    ]
  },
  "risk_warnings": [
    "P/E 290倍，估值极度透支",
    "汽车业务连续2年下滑",
    "机构短期派发信号"
  ],
  "risk_level": "High",
  "monitoring_metrics": [
    {
      "indicator": "股价",
      "current_value": "$406",
      "threshold": "$370止损",
      "status": "Normal"
    },
    {
      "indicator": "RSI",
      "current_value": "42.6",
      "threshold": "<30超卖",
      "status": "Normal"
    }
  ],
  "report_path": "./output/summary/综合分析-TSLA-2026-02-06.md",
  "sub_reports": {
    "fundamental": "./output/fundamental-analysis/TSLA-Tesla-2026-02-06.md",
    "institutional": "./output/institutional-accumulation-analysis/机构操作分析-20260206-TSLA.md"
  }
}
```

## 错误代码规范

```typescript
enum ErrorCode {
  // 系统错误
  SYSTEM_ERROR = "SYSTEM_ERROR",
  TIMEOUT = "TIMEOUT",
  
  // 网络错误
  NETWORK_ERROR = "NETWORK_ERROR",
  RATE_LIMIT = "RATE_LIMIT",
  
  // 数据错误
  DATA_NOT_FOUND = "DATA_NOT_FOUND",
  DATA_PARSE_ERROR = "DATA_PARSE_ERROR",
  
  // Agent错误
  AGENT_CRASH = "AGENT_CRASH",
  SKILL_NOT_FOUND = "SKILL_NOT_FOUND",
  INVALID_PROMPT = "INVALID_PROMPT",
  
  // 文件错误
  FILE_SAVE_ERROR = "FILE_SAVE_ERROR",
  FILE_NOT_FOUND = "FILE_NOT_FOUND"
}
```

## 数据验证规则

### 必填字段验证

```python
def validate_parse_request(data: dict) -> bool:
    """验证ParseRequest"""
    required_fields = ["ticker", "company_name", "analysis_type", "task_id"]
    return all(field in data for field in required_fields)

def validate_subagent_result(data: dict) -> bool:
    """验证SubAgentResult"""
    required_fields = ["task_id", "subagent_name", "status", "timestamp"]
    if not all(field in data for field in required_fields):
        return False
    
    if data["status"] == "completed":
        return "data" in data and "report_path" in data["data"]
    elif data["status"] in ["failed", "timeout"]:
        return "error" in data
    
    return True
```

### 数据类型验证

```python
def validate_types(data: dict, schema: dict) -> list:
    """
    验证数据类型
    
    schema示例：
    {
        "ticker": str,
        "confidence": int,
        "pe_ratio": float
    }
    """
    errors = []
    for field, expected_type in schema.items():
        if field in data and not isinstance(data[field], expected_type):
            errors.append(f"Field '{field}' should be {expected_type.__name__}")
    return errors
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-02-06 | 初始版本 |
