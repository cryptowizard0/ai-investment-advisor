# Multi-Agent Stock Analysis 重构设计

日期：2026-05-25
状态：已确认设计，待实施计划
范围：`plugins/invest-flow/skills/multi-agent-stock-analysis/`

## 背景

当前 `multi-agent-stock-analysis` 的文档目标是“多 Agent 协同股票分析系统”，但实际实现更接近一个固定三路命令并发器：并行执行 `fundamental-analysis`、`institutional-accumulation-analysis` 和 `gie-investment-framework`，定位报告路径后保存 orchestration JSON。

与此同时，InvestFlow 已经具备更完整的投研能力集合，包括每日美股扫描、AI 基建板块发现、稀缺机会雷达、反身性分析、专业买方研究报告、标准化个股报告和市场数据路由。现有 multi-agent 入口没有把这些能力组织成产品化投研流水线。

本次重构的目标是把 `multi-agent-stock-analysis` 从固定三 Agent 并发器升级为 InvestFlow 的轻量投研流水线编排器。

## 当前问题

1. `orchestrator.py` 硬编码三个 agent，新增 skill 没有自然接入点。
2. `SubAgentResult.key_findings` 和 `key_metrics` 没有真实抽取，最终聚合缺少稳定字段。
3. 当前只保存 `orchestration-{ticker}-{timestamp}.json`，没有生成文档承诺的中文综合报告。
4. `SKILL.md` 描述 `delegate_task` 主从模型，但实际实现是 `opencode run` 命令驱动，文档与实现不一致。
5. `summary-report-template.md` 字段丰富，但缺少字段抽取器，无法可靠填充。
6. 新增的 `daily-us-market-scan`、`ai-infrastructure-*`、`professional-investment-analyst`、`reflexivity-*` 等 skill 还没有被主编排层产品化利用。

## 目标

1. 保持现有 CLI 入口兼容：

   ```bash
   python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --execution-mode command
   ```

2. 将内部结构拆成清晰模块，使编排、注册、计划、执行、抽取和组合各自独立。
3. 支持投研流水线阶段：市场上下文、机会发现、单资产验证、决策与报告。
4. 为每个 skill 产出统一 handoff 数据，供最终综合决策使用。
5. 同时输出 orchestration JSON 和中文 Markdown 综合报告。
6. 支持 partial success，并明确说明缺失维度对结论的影响。
7. 让 README、`SKILL.md`、workflow 文档与真实实现一致。

## 非目标

1. 不引入数据库。
2. 不做 UI。
3. 不改其它 skill 的核心方法论。
4. 不一次性重写所有 Markdown 模板。
5. 不让 orchestrator 替代单个 skill；它只负责编排、字段抽取、组合和索引。

## 推荐架构

`orchestrator.py` 保留为兼容 CLI wrapper，核心逻辑下沉到 `scripts/investflow_pipeline/`：

```text
multi-agent-stock-analysis/
├── SKILL.md
├── assets/
│   └── summary-report-template.md
├── references/
│   ├── workflow-guide.md
│   ├── data-structure.md
│   └── pipeline-design.md
└── scripts/
    ├── orchestrator.py
    └── investflow_pipeline/
        ├── __init__.py
        ├── models.py
        ├── registry.py
        ├── intent_router.py
        ├── planner.py
        ├── executor.py
        ├── extractors.py
        ├── composer.py
        └── paths.py
```

### 模块职责

- `models.py`：定义 `TaskRequest`、`SkillSpec`、`StageResult`、`PipelineResult`、`Handoff`。
- `registry.py`：定义所有 InvestFlow skill 的命令模板、输出目录、阶段、是否必需、超时和 extractor 类型。
- `intent_router.py`：识别任务类型、ticker、公司、主题、市场和期望输出。
- `planner.py`：根据 intent 生成 workflow preset 和执行阶段。
- `executor.py`：负责命令执行、并发、重试、超时、partial success 和错误聚合。
- `extractors.py`：从 Markdown 或 JSON 输出中抽取 handoff 字段。
- `composer.py`：生成中文综合投资决策摘要和子报告索引。
- `paths.py`：处理 repo root、输出目录、报告路径发现和非覆盖命名。

## Skill 分层

按投研流水线分层，而不是按目录平铺：

```text
1. Market Context 层
   daily-us-market-scan
   market-data-router

2. Opportunity Discovery 层
   ai-infrastructure-sector-discovery
   ai-infrastructure-scarcity-radar
   gold-trend-analysis

3. Single Asset Validation 层
   fundamental-analysis
   institutional-accumulation-analysis
   gie-investment-framework
   reflexivity-quick-scan
   reflexivity-deep-analysis

4. Decision & Report 层
   professional-investment-analyst
   reportify-stock-analysis
   multi-agent-stock-analysis
```

### Skill 定位

- `market-data-router`：公共数据前置层，为单股流程提供统一行情与缓存。
- `daily-us-market-scan`：市场上下文入口，为 watchlist 和主题机会提供来源。
- `ai-infrastructure-sector-discovery`：AI 基建赛道发现与排序，不直接给买卖建议。
- `ai-infrastructure-scarcity-radar`：验证真短缺、高景气或纯概念，输出研究优先级。
- `gold-trend-analysis`：宏观商品专题路径，不进入默认单股流程。
- `fundamental-analysis`：财务、商业模式、估值和基础技术面。
- `institutional-accumulation-analysis`：短中期资金行为和交易风险。
- `gie-investment-framework`：1-3 年产业链与金铲子逻辑。
- `reflexivity-quick-scan`：默认轻量叙事、价格、现实错位判断。
- `reflexivity-deep-analysis`：在用户要求深研，或 quick scan 显示透支、反转、高错位时触发。
- `professional-investment-analyst`：正式单股研究报告主报告。
- `reportify-stock-analysis`：标准化输出，不承担深度判断主逻辑。
- `multi-agent-stock-analysis`：编排层和最终决策摘要生成器。

## Workflow Preset

第一版支持以下 preset：

| Preset | 用途 | 默认阶段 |
|---|---|---|
| `stock_decision` | 判断单股买入、观望、减仓或回避 | market-data-router -> fundamental -> institutional -> gie -> reflexivity-quick -> professional-investment-analyst -> decision-composer |
| `theme_discovery` | 从市场或主题中发现机会 | daily-us-market-scan -> ai-infrastructure-sector-discovery -> ai-infrastructure-scarcity-radar -> gie |
| `ai_infra_research` | 深挖 AI 基建稀缺机会 | ai-infrastructure-scarcity-radar -> gie -> reflexivity-quick -> professional-investment-analyst |
| `formal_report` | 生成正式个股研究报告 | professional-investment-analyst -> reportify-stock-analysis -> decision-composer |
| `market_scan` | 每日美股复盘和观察清单 | daily-us-market-scan -> decision-composer |

为了降低重构风险，Phase 1 默认仍以旧三件套兼容路径为基础；Phase 2 再将完整 `stock_decision` preset 设为默认。

## 数据结构

### TaskRequest

```text
task_id
intent: stock_decision / theme_discovery / ai_infra_research / formal_report / market_scan
target: ticker / company / theme / sector
market: US / HK / CN / FUT / unknown
horizon: short / medium / long / mixed
requested_outputs: summary / formal_report / handoff_json
```

### SkillSpec

```text
skill_name
stage
command_template
output_dir
required
timeout_seconds
retry_policy
extractor_type
```

### StageResult

```text
skill_name
status
report_path
handoff
errors
duration
retry_count
```

### Handoff

```text
conclusion
recommendation
confidence
key_evidence[]
risk_flags[]
contradiction_points[]
monitoring_signals[]
data_gaps[]
```

### PipelineResult

```text
task_id
status
intent
target
started_at
ended_at
stage_results[]
summary_report_path
orchestration_json_path
failed_required[]
warnings[]
```

## 默认单股执行流

`stock_decision` 流程：

```text
1. Intent Router
   用户输入 -> ticker/company/任务类型

2. Planner
   生成阶段计划：
   market-data-router
   fundamental-analysis
   institutional-accumulation-analysis
   gie-investment-framework
   reflexivity-quick-scan
   professional-investment-analyst
   decision-composer

3. Executor
   market-data-router 先跑
   fundamental / institutional / gie 可并发
   reflexivity 依赖市场与报告摘要
   professional report 最后生成
   可选 agent 失败时进入 partial_success

4. Extractor
   每个报告抽取 handoff JSON
   第一版使用规则抽取和 fallback 摘要

5. Composer
   生成 output/summary/综合分析-{TICKER}-{YYYY-MM-DD}.md
   生成 output/summary/orchestration-{TICKER}-{timestamp}.json
```

## 降级规则

1. `market-data-router` 失败：继续跑研究类 skill，但所有量价与资金结论标记“数据源未统一”，整体置信度下调。
2. `institutional-accumulation-analysis` 失败：不阻断长期结论，短线交易建议降级为“需等待资金流确认”。
3. `gie-investment-framework` 失败：不阻断短线判断，中长期 thesis 降低置信度。
4. `reflexivity-quick-scan` 失败：保留基本面、资金流和 GIE 结论，但 summary 明确缺少叙事/价格/现实错位验证。
5. `professional-investment-analyst` 失败：只输出 multi-agent 摘要，不生成正式深研报告。
6. 所有核心分析失败：只输出错误 JSON，不生成投资建议。

## 输出

每次执行至少输出：

```text
output/summary/orchestration-{TARGET}-{YYYYMMDD-HHMMSS}.json
```

当存在至少一个成功研究阶段时，额外输出：

```text
output/summary/综合分析-{TARGET}-{YYYY-MM-DD}.md
```

Markdown summary 必须包含：

1. 作者：`InvestmentFlow`
2. 任务类型和目标
3. 综合结论
4. 置信度和原因
5. 多维共振信号
6. 冲突与分歧
7. 操作建议或研究优先级
8. 反证条件
9. 跟踪指标 Dashboard
10. 数据缺口
11. 子报告路径索引
12. 免责声明

## 环境变量

保留旧变量以兼容：

```text
ORCH_FUNDAMENTAL_CMD
ORCH_INSTITUTIONAL_CMD
ORCH_GIE_CMD
ORCH_EXECUTION_MODE
```

新增统一命名规则：

```text
INVESTFLOW_CMD_<SKILL_NAME_UPPER_WITH_UNDERSCORES>
```

示例：

```text
INVESTFLOW_CMD_FUNDAMENTAL_ANALYSIS
INVESTFLOW_CMD_PROFESSIONAL_INVESTMENT_ANALYST
INVESTFLOW_CMD_REFLEXIVITY_QUICK_SCAN
```

旧变量优先级高于 registry 默认值；新变量优先级高于旧变量。发生冲突时记录到 orchestration metadata。

## 实施阶段

### Phase 1：架构拆分与兼容

- 将 `orchestrator.py` 拆成 CLI wrapper 和 `investflow_pipeline/` 模块。
- 建立 `models.py`、`registry.py`、`planner.py`、`executor.py`、`composer.py`、`paths.py`。
- 默认流程兼容现有 `fundamental + institutional + gie`。
- `mock` 模式完整生成 orchestration JSON 和 summary Markdown。
- 更新 `SKILL.md`，移除与实现不一致的 `delegate_task` 描述。

### Phase 2：投研流水线接入

- 将所有 skill 写入 registry。
- 新增 workflow preset：`stock_decision`、`theme_discovery`、`ai_infra_research`、`formal_report`、`market_scan`。
- 接入 `market-data-router` 作为单股流程的数据前置层。
- 接入 `reflexivity-quick-scan` 和 `professional-investment-analyst` 到默认 `stock_decision` 流程。
- 建立第一版规则抽取器，填充 `handoff`。

### Phase 3：质量与产品化

- 强化字段抽取与 summary 生成质量。
- 为 partial success、无 ticker、无报告路径、命令失败、报告空文件等场景补测试。
- 让 summary 明确区分事实、推断、假设、数据缺口和反证条件。
- README、AGENTS、workflow-guide、data-structure 与真实实现对齐。
- 后续可选：将 `daily-us-market-scan -> discovery -> watchlist` 做成每日或每周 automation。

## 验收标准

1. `python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py --help` 正常。
2. `--execution-mode mock` 可跑完整 `stock_decision` 或兼容基础流程。
3. 旧三件套路径仍可用，不破坏现有使用方式。
4. 输出同时包含 orchestration JSON 和中文 summary Markdown。
5. registry 中能看到所有现有 skill 的定义，即使部分 workflow 暂不默认启用。
6. partial success 报告明确列出缺失维度和影响。
7. `SKILL.md` 与真实实现一致，不再描述不存在的 `delegate_task` 调用模式。
8. 不覆盖已有输出文件，重复文件使用 `(1)`、`(2)` 后缀。
9. 命令失败、超时、报告路径缺失和空报告均有清晰错误信息。
10. 不引入数据库、UI 或其它 skill 方法论变更。

## 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 字段抽取不稳定 | summary 结论质量波动 | Phase 1 使用保守规则抽取，无法确认则标记数据缺口 |
| workflow preset 过早复杂化 | 重构面过大 | Phase 1 只保证兼容路径，Phase 2 再扩展 preset |
| 外部命令运行时间长 | 开发验证慢 | mock 模式作为默认测试路径，command 模式用于真实验收 |
| 文档与实现再次漂移 | 使用者困惑 | 将 registry 和 workflow-guide 同步更新列入验收 |
| 数据源不统一 | 多 agent 结论冲突 | 将 `market-data-router` 作为公共前置层，并在 summary 中记录数据源状态 |

## 后续计划

本设计经用户确认后，下一步使用 implementation planning 流程产出详细实施计划。实施计划应按 Phase 1 优先，先完成模块拆分、兼容 CLI、mock 验证和 summary 输出，再逐步接入完整投研流水线。
