# 多Agent协同分析 - 详细工作流指南

> 当前实现为 Phase 1 命令驱动 Pipeline。历史文档中出现的 `delegate_task` 伪代码仅表示目标架构概念，不是当前脚本调用方式。当前真实入口是 `scripts/orchestrator.py`，核心逻辑位于 `scripts/investflow_pipeline/`。

## 完整工作流程

### 阶段1: 请求解析 (MainAgent)

**输入**：用户自然语言请求
**输出**：结构化任务参数

```python
{
  "ticker": "TSLA",
  "company_name": "Tesla", 
  "analysis_type": "full",  # full | fundamental | institutional | gie
  "task_id": "ma_20260206_001"
}
```

**解析规则**：
- 提取股票代码（大写字母2-5位）
- 识别公司名称（上下文或搜索确认）
- 判断分析维度（默认full）

### 阶段2: 任务分发 (MainAgent)

**并行启动策略**：

```python
import asyncio

tasks = []

# SubAgent 1: 基本面分析
if analysis_type in ["full", "fundamental"]:
    task_fundamental = delegate_task(
        category="deep",
        load_skills=["fundamental-analysis"],
        prompt=f"""
        对 {ticker} ({company_name}) 执行完整的基本面分析。
        
        必须完成：
        1. 公司概况与商业模式
        2. 财务数据(TTM)：营收、利润、EPS、ROE等
        3. 估值指标：P/E、P/S、市值
        4. 技术指标：均线、RSI、MACD
        5. 催化剂与风险分析
        
        输出：
        - 保存报告到 ./output/fundamental-analysis/
        - 返回报告路径和核心结论
        """,
        run_in_background=True
    )
    tasks.append(("fundamental", task_fundamental))

# SubAgent 2: 机构资金流向分析
if analysis_type in ["full", "institutional"]:
    task_institutional = delegate_task(
        category="deep",
        load_skills=["institutional-accumulation-analysis"],
        prompt=f"""
        分析 {ticker} 的机构吸筹派发情况。
        
        必须完成：
        1. 收集近3个月OHLCV数据
        2. 计算OBV、CMF、VWAP等指标
        3. VSA量价分析
        4. 技术指标背离分析
        5. 给出诊断分类和置信度
        
        输出：
        - 保存报告到 ./output/institutional-accumulation-analysis/
        - 返回：诊断分类、成本区间、关键证据
        """,
        run_in_background=True
    )
    tasks.append(("institutional", task_institutional))

# SubAgent 3: GIE框架分析
if analysis_type in ["full", "gie"]:
    task_gie = delegate_task(
        category="deep",
        load_skills=["gie-investment-framework"],
        prompt=f"""
        使用GIE框架评估 {company_name} ({ticker})。
        
        必须完成：
        1. 宏观天候分析
        2. 供需趋势分析
        3. 金铲子识别(Tier 1/2)
        4. 财务穿透验证
        5. 估值与择时建议
        6. 反FOMO检查
        
        输出：
        - 保存报告到 ./output/gie-investment-framework/
        - 返回：金铲子等级、投资评级、建议仓位
        """,
        run_in_background=True
    )
    tasks.append(("gie", task_gie))
```

### 阶段3: 执行与重试 (MainAgent)

**带重试的执行逻辑**：

```python
async def execute_subagent_with_retry(
    agent_def: Dict,
    ticker: str,
    max_retries: int = 1,
    timeout: int = 240
) -> SubAgentResult:
    """
    执行SubAgent，支持失败重试
    """
    agent_name = agent_def["name"]
    
    for attempt in range(max_retries + 1):
        is_retry = attempt > 0
        
        if is_retry:
            print(f"🔄 [{agent_name}] 第{attempt}次重试...")
        
        try:
            # 执行Agent
            result = await delegate_task(
                category="deep",
                load_skills=[agent_def["skill"]],
                prompt=build_prompt(agent_def, ticker),
                run_in_background=False
            )
            
            # 验证结果
            if is_valid_result(result):
                if is_retry:
                    print(f"✅ [{agent_name}] 重试成功!")
                return SubAgentResult(
                    agent_name=agent_name,
                    status="completed",
                    retry_count=attempt,
                    data=result
                )
            
            # 结果无效，需要重试
            if attempt < max_retries:
                continue
            else:
                return SubAgentResult(
                    agent_name=agent_name,
                    status="failed",
                    retry_count=attempt,
                    error="结果验证失败"
                )
                
        except TimeoutError:
            if attempt < max_retries:
                print(f"⏱️ [{agent_name}] 超时，准备重试...")
                continue
            return SubAgentResult(
                agent_name=agent_name,
                status="timeout",
                retry_count=attempt,
                error="执行超时"
            )
            
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️ [{agent_name}] 异常: {e}，准备重试...")
                continue
            return SubAgentResult(
                agent_name=agent_name,
                status="failed",
                retry_count=attempt,
                error=str(e)
            )
```

**结果验证逻辑**：

```python
def is_valid_result(result: Dict) -> bool:
    """
    验证SubAgent结果是否有效
    """
    # 1. 检查状态
    if result.get("status") == "failed":
        return False
    
    # 2. 检查输出内容
    output = result.get("output", "")
    if not output or len(output.strip()) < 100:
        return False  # 空结果或内容过少
    
    # 3. 检查关键字段
    required_keywords = ["分析", "报告", "结论"]
    if not any(kw in output for kw in required_keywords):
        return False  # 缺少关键内容
    
    # 4. 检查报告路径
    if not result.get("report_path"):
        return False
    
    return True
```

**监控逻辑（更新版）**：

```python
def monitor_tasks(tasks, timeout=300):
    """
    监控所有SubAgent任务
    """
    results = {}
    failed = {}
    retried = {}  # 记录重试信息
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        all_completed = True
        
        for name, task in tasks:
            if name in results or name in failed:
                continue
                
            # 检查任务状态
            output = background_output(
                task_id=task.task_id,
                block=False
            )
            
            if output.status == "completed":
                results[name] = parse_result(output)
                if output.retry_count > 0:
                    retried[name] = output.retry_count
                    print(f"✅ {name} 分析完成 (重试{output.retry_count}次)")
                else:
                    print(f"✅ {name} 分析完成")
            elif output.status == "failed":
                failed[name] = output.error
                if output.retry_count > 0:
                    print(f"❌ {name} 分析失败 (已重试{output.retry_count}次): {output.error}")
                else:
                    print(f"❌ {name} 分析失败: {output.error}")
            else:
                all_completed = False
        
        if all_completed:
            break
            
        time.sleep(5)
    
    # 处理超时
    for name, task in tasks:
        if name not in results and name not in failed:
            failed[name] = "Task timeout"
    
    return results, failed, retried
```

### 阶段4: 结果聚合 (MainAgent)

**聚合逻辑**：

```python
def aggregate_results(results, failed, ticker, company):
    """
    聚合各SubAgent结果
    """
    aggregated = {
        "task_id": generate_task_id(),
        "ticker": ticker,
        "company": company,
        "analysis_date": get_current_date(),
        "status": "completed" if len(results) > 0 else "failed",
        "completed_count": len(results),
        "failed_count": len(failed),
        "fundamental": results.get("fundamental"),
        "institutional": results.get("institutional"),
        "gie": results.get("gie"),
        "errors": failed
    }
    
    return aggregated
```

### 阶段5: 综合分析 (SummaryAgent)

**SummaryAgent任务**：

```python
summary_task = delegate_task(
    category="deep",
    prompt=f"""
    作为Senior Investment Advisor，基于以下多维度分析结果生成综合投资建议：
    
    ## 输入数据
    {json.dumps(aggregated_data, indent=2, ensure_ascii=False)}
    
    ## 任务要求
    
    ### 1. 一致性分析
    - 检查三个维度的结论是否一致
    - 识别共振信号（多个维度同时看好的情况）
    - 标记任何矛盾或分歧
    
    ### 2. 综合评分
    - 计算整体置信度（0-100）
    - 评估风险等级（低/中/高）
    
    ### 3. 投资建议
    - 明确给出：强烈买入/买入/持有/卖出/强烈卖出
    - 建议仓位配置（如：15-20%）
    - 入场价格区间
    - 止损位设置
    - 目标价位和时间 horizon
    
    ### 4. 关键风险提示
    - 列出最重要的3-5个风险因素
    - 监测指标和预警阈值
    
    ### 5. 生成综合报告
    - 使用中文撰写专业投资报告
    - 包含执行摘要、各维度要点、综合结论
    - 保存到：./output/summary/综合分析-{ticker}-{date}.md
    
    ## 输出格式
    返回JSON格式：
    {{
      "recommendation": "买入/持有/卖出",
      "confidence": 85,
      "position_size": "15-20%",
      "entry_range": "$230-$250",
      "stop_loss": "$210",
      "target": "$320",
      "time_horizon": "12-18个月",
      "key_risks": ["风险1", "风险2"],
      "report_path": "./output/summary/..."
    }}
    """,
    run_in_background=False
)
```

### 阶段6: 结果输出

**输出格式**：

```markdown
## 📊 综合分析结果

**股票**: {ticker} ({company})
**分析日期**: {date}
**综合评级**: {recommendation}
**置信度**: {confidence}%
**建议仓位**: {position_size}

### 各维度结论

| 维度 | 核心结论 | 置信度 |
|------|----------|--------|
| 基本面 | {fundamental_conclusion} | {confidence}% |
| 机构流向 | {institutional_conclusion} | {confidence}% |
| GIE框架 | {gie_conclusion} | {confidence}% |

### 投资建议

**操作建议**: {action}
**入场区间**: {entry_range}
**止损位**: {stop_loss}
**目标价位**: {target}
**投资周期**: {time_horizon}

### 风险提示
{key_risks}

### 报告文件
- 基本面分析: {fundamental_report_path}
- 机构流向分析: {institutional_report_path}
- GIE框架分析: {gie_report_path}
- 综合报告: {summary_report_path}
```

## 执行时序图

### 正常执行流程

```
时间 →

用户          MainAgent        SubAgent1       SubAgent2       SubAgent3       SummaryAgent
  |               |                |               |               |               |
  |── 分析TSLA ──→|                |               |               |               |
  |               |── 启动Agent1 ─→|               |               |               |
  |               |── 启动Agent2 ─────────────────→|               |               |
  |               |── 启动Agent3 ─────────────────────────────────→|               |
  |               |                |               |               |               |
  |               |←──────────────|←──────────────|←──────────────|               |
  |               | (等待完成)     | (运行中)      | (运行中)      | (运行中)      |
  |               |                |               |               |               |
  |               |── 聚合结果 ───→|               |               |               |
  |               |── 调用SummaryAgent ───────────────────────────────────────────→|
  |               |                |               |               |               | (分析中)
  |               |←──────────────────────────────────────────────────────────────|
  |               | (综合报告)     |               |               |               |
  |←──────────────|                |               |               |               |
  | (输出结果)    |                |               |               |               |
```

### 带重试的执行流程（Agent2失败重试）

```
时间 →

用户          MainAgent        SubAgent1       SubAgent2       SubAgent3
  |               |                |               |               |
  |── 分析TSLA ──→|                |               |               |
  |               |── 启动Agent1 ─→|               |               |
  |               |── 启动Agent2 ─────────────────→|               |
  |               |── 启动Agent3 ─────────────────────────────────→|
  |               |                |               |               |
  |               |←──────────────|               |               |
  |               |                |               | ❌ 失败       |
  |               |                |               |   (空结果)    |
  |               |                |               |               |
  |               |                |               | 🔄 重试 ─────→|
  |               |                |               |               |
  |               |                |               | ✅ 成功       |
  |               |←──────────────────────────────────────────────|
  |               |                |               |               |
  |               |── 聚合结果（含重试信息）                       |
  |               |                |               |               |
  |←──────────────| (输出: Agent2重试1次后成功)                   |
  | (输出结果)    |                |               |               |

注: 重试机制自动执行，对用户透明
```

## 超时和错误处理

### 超时策略

```python
# 总超时: 5分钟
TOTAL_TIMEOUT = 300  # seconds

# 单个Agent超时: 4分钟
AGENT_TIMEOUT = 240  # seconds

# 检查间隔: 5秒
CHECK_INTERVAL = 5   # seconds
```

### 错误分类处理

| 错误类型 | 检测方式 | 处理策略 | 是否重试 |
|---------|---------|---------|---------|
| 空输出 | 内容长度<100字符 | 自动重试1次 | ✅ 是 |
| 网络错误 | 连接超时 | 自动重试1次 | ✅ 是 |
| 任务超时 | 超过AGENT_TIMEOUT | 自动重试1次 | ✅ 是 |
| 执行异常 | 代码抛出异常 | 自动重试1次 | ✅ 是 |
| 内容不完整 | 缺少关键词 | 自动重试1次 | ✅ 是 |
| 数据缺失 | 外部API无数据 | 标记失败 | ❌ 否 |
| 解析错误 | 返回格式异常 | 标记失败 | ❌ 否 |

### 部分成功模式

```python
def handle_partial_success(results, failed, retried):
    """
    处理部分成功的情况
    """
    completed_count = len(results)
    total_count = completed_count + len(failed)
    retried_count = len(retried)
    
    if completed_count == 0:
        # 全部失败
        return {
            "status": "failed",
            "message": "所有分析维度均失败",
            "errors": failed
        }
    elif completed_count < total_count:
        # 部分成功
        return {
            "status": "partial_success",
            "message": f"{completed_count}/{total_count} 个分析维度成功",
            "completed": results,
            "failed": failed,
            "retried": retried,
            "note": "基于成功维度生成报告，缺失维度已在报告中标注",
            "retry_summary": {
                "total_retries": sum(retried.values()),
                "successful_retries": len([r for r in retried if r in results]),
                "failed_after_retry": len([r for r in retried if r in failed])
            }
        }
    else:
        # 全部成功（可能包含重试）
        return {
            "status": "success",
            "message": "所有分析维度均成功",
            "completed": results,
            "retried": retried,
            "retry_summary": {
                "total_retries": sum(retried.values()) if retried else 0,
                "successful_retries": len(retried) if retried else 0,
                "agents_retried": list(retried.keys()) if retried else []
            }
        }
```

## 使用 Orchestrator 脚本

### Python API

```python
from scripts.orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationConfig,
    analyze_stock_with_retry
)

# 方式1: 简单同步调用
result = analyze_stock_with_retry("TSLA", "Tesla")

# 方式2: 异步调用（推荐）
async def main():
    config = OrchestrationConfig(
        max_retries=1,
        timeout_seconds=240,
        retry_on_empty=True,
        retry_on_timeout=True,
        parallel_execution=True
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    result = await orchestrator.analyze_stock("TSLA", "Tesla")
    
    print(f"状态: {result['status']}")
    print(f"成功: {result['completed_count']}/{result['total_count']}")
    print(f"重试: {result['retried_count']} 次")

asyncio.run(main())
```

### 命令行

```bash
# 在仓库根目录运行 packaged orchestrator
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py

# 查看输出结果
ls output/summary/
```

## 性能优化建议

1. **并行度控制**：同时启动3个Agent是最佳选择，更多可能导致资源竞争
2. **超时设置**：根据网络情况调整，建议5分钟总超时
3. **缓存策略**：可以缓存最近的分析结果，避免重复分析
4. **增量更新**：对于已有报告的标的，可以只更新变化的维度
5. **重试策略**：重试次数不宜过多，1次通常足够应对临时故障

## 监控指标

- **成功率**：成功完成的Agent比例
- **平均耗时**：完整分析的平均时间
- **错误率**：各类错误的发生频率
- **用户满意度**：用户对综合报告的反馈
