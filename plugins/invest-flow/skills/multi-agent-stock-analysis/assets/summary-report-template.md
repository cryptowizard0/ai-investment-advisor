# 多Agent协同股票分析 - 综合报告模板

## 报告头

```markdown
# {ticker} - {company_name} 多维度投资分析报告

**分析日期：** {analysis_date}  
**作者：** InvestmentFlow  
**当前股价：** {current_price}  
**综合评级：** {recommendation} ({confidence}% 置信度)  
**建议仓位：** {position_size}

---

## 公司画像摘要

| 项目 | 内容 |
|---|---|
| 公司一句话定义 | {company_one_liner} |
| 核心业务 | {company_business_summary} |
| 收入来源 | {company_revenue_model} |
| 核心技术 / 壁垒 | {company_technical_advantages} |
| 产业链位置 | {company_industry_chain_position} |
| AI 相关性 | {company_ai_relevance} |
| 主要竞争对手 | {company_competitors} |
| 行业地位 | {company_industry_position} |
| 关键不确定性 | {company_key_uncertainties} |

---

## 执行摘要

### 投资建议
- **操作评级：** {recommendation}
- **建议仓位：** {position_size}
- **入场区间：** {entry_range}
- **止损位：** {stop_loss}
- **目标价位：** {target_price}
- **投资周期：** {time_horizon}
- **风险等级：** {risk_level}

### 核心逻辑
{summary_text}

---

## 各维度分析汇总

### 一、基本面分析

**分析师：** Fundamental Analysis Agent  
**报告路径：** {fundamental_report_path}

#### 关键指标
| 指标 | 数值 | 评估 |
|------|------|------|
| 股票类型 | {stock_type} | - |
| 当前股价 | {current_price} | - |
| P/E (TTM) | {pe_ratio} | {pe_assessment} |
| 市值 | {market_cap} | - |
| RSI(14) | {rsi_14} | {rsi_assessment} |

#### 核心结论
{fundamental_conclusion}

#### 投资策略
- **短线策略：** {trading_strategy}
- **长线策略：** {investment_strategy}

---

### 二、机构资金流向分析

**分析师：** Institutional Accumulation Agent  
**报告路径：** {institutional_report_path}

#### 诊断结果
- **分类：** {institutional_classification}
- **置信度：** {institutional_confidence}%
- **趋势方向：** {trend_direction}

#### 关键指标
| 指标 | 数值 | 信号 |
|------|------|------|
| OBV趋势 | {obv_trend} | {obv_signal} |
| CMF | {cmf} | {cmf_signal} |
| VWAP | {vwap} | {vwap_signal} |

#### 机构成本区间
- **建仓成本区：** {cost_zone}
- **当前位置：** {current_position}

#### 核心证据
{key_evidence}

#### 风险提示
- **关键支撑位：** {support_levels}
- **关键阻力位：** {resistance_levels}
- **风险拐点：** {risk_inflection_point}

---

## 一致性分析

### 整体一致性评级：{consistency_rating}

### 共振信号（多维度一致）
{aligned_signals}

### 冲突与分歧
{conflicts}

### 关键置信点
{confluence_points}

---

## 综合投资建议

### 投资策略矩阵

| 投资周期 | 建议 | 逻辑 | 风险等级 |
|----------|------|------|----------|
| 短线(1-4周) | {short_term_recommendation} | {short_term_logic} | {short_term_risk} |
| 中线(1-6月) | {medium_term_recommendation} | {medium_term_logic} | {medium_term_risk} |
| 长线(1-3年) | {long_term_recommendation} | {long_term_logic} | {long_term_risk} |

### 操作策略

#### 建仓策略
- **首次建仓：** {initial_entry}
- **加仓时机：** {add_position_trigger}
- **仓位管理：** {position_management}

#### 止损策略
- **止损位：** {stop_loss_level}
- **减仓信号：** {reduce_position_signals}
- **清仓条件：** {exit_conditions}

#### 获利了结
- **目标位1：** {target_1} ({target_1_logic})
- **目标位2：** {target_2} ({target_2_logic})
- **目标位3：** {target_3} ({target_3_logic})

---

## 风险提示

### 高风险因素
{risk_warnings}

### 监控指标

| 指标 | 当前值 | 预警阈值 | 状态 |
|------|--------|----------|------|
{monitoring_table}

### 情景分析

**乐观情景** ({optimistic_probability}%概率)
- 触发条件：{optimistic_trigger}
- 目标价位：{optimistic_target}
- 预期收益：{optimistic_return}

**基准情景** ({base_probability}%概率)
- 触发条件：{base_trigger}
- 目标价位：{base_target}
- 预期收益：{base_return}

**悲观情景** ({pessimistic_probability}%概率)
- 触发条件：{pessimistic_trigger}
- 目标价位：{pessimistic_target}
- 预期损失：{pessimistic_loss}

---

## 附录

### 报告文件清单
- **本报告：** {summary_report_path}
- **company-profile：** [{company_profile_report_path}]({company_profile_report_link})
- **基本面分析：** {fundamental_report_path}
- **机构流向分析：** {institutional_report_path}
- **反身性深度分析：** {reflexivity_deep_report_path}
- **Reportify标准报告：** {reportify_report_path}
- **非共识重估分析：** {non_consensus_report_path}

### 免责声明
本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。请根据自身风险承受能力做出投资决策。

### 版本信息
- **报告版本：** 1.0.0
- **生成时间：** {generation_time}
- **分析系统：** Multi-Agent Stock Analysis System
- **数据截止：** {data_cutoff_time}

---

**分析师：** AI Multi-Agent Analysis System  
**复核：** Summary Agent  
**数据来源：** Yahoo Finance, Investing.com, 各Agent独立分析
```

## 模板使用说明

### 变量替换规则

所有 `{variable_name}` 格式的标记都需要替换为实际值：

```python
template_variables = {
    # 基础信息
    "ticker": "TSLA",
    "company_name": "Tesla",
    "analysis_date": "2026-02-06",
    "current_price": "$406.01",

    # 公司画像
    "company_profile_report_path": "./output/company-profile/...",
    "company_profile_report_link": "./output/company-profile/...",
    "company_one_liner": "Tesla 是全球领先的电动车和能源科技公司。",
    "company_business_summary": "核心业务包括电动车、储能、能源服务和自动驾驶软件。",
    "company_revenue_model": "通过整车销售、能源产品、服务和软件订阅收费。",
    "company_technical_advantages": "电池系统、制造效率、自动驾驶数据闭环",
    "company_industry_chain_position": "电动车和能源存储产业链下游整合商。",
    "company_ai_relevance": "直接受益",
    "company_competitors": "BYD, Volkswagen, GM",
    "company_industry_position": "全球电动车头部企业。",
    "company_key_uncertainties": "自动驾驶商业化节奏、价格竞争、监管变化",
    
    # 综合结论
    "recommendation": "Hold",
    "confidence": 70,
    "position_size": "5-10%",
    "entry_range": "$380-$400",
    "stop_loss": "$370",
    "target_price": "$450-$480",
    "time_horizon": "6-12个月",
    "risk_level": "High",
    
    # 基本面
    "fundamental_report_path": "./output/fundamental-analysis/...",
    "stock_type": "Growth",
    "pe_ratio": 290,
    "pe_assessment": "⚠️ 极高",
    "market_cap": "$1.4T",
    "rsi_14": 42.6,
    "rsi_assessment": "中性偏弱",
    
    # 机构分析
    "institutional_report_path": "./output/institutional-accumulation-analysis/...",
    "institutional_classification": "派发初级",
    "institutional_confidence": 65,
    "trend_direction": "短期看跌",
    "obv_trend": "下降",
    "obv_signal": "⚠️ 资金流出",
    "cmf": -0.05,
    "cmf_signal": "⚠️ 卖盘主导",
    "vwap": "$418.5",
    "vwap_signal": "股价低于机构成本",
    "cost_zone": "$415-$430",
    "current_position": "低于成本区约3%",
    
    # 一致性分析
    "consistency_rating": "中等",
    "aligned_signals": "- 长期AI叙事空间被认可\n- 技术护城河稳固",
    "conflicts": "- 基本面看好长期 vs 机构分析短期派发",
    "confluence_points": "- 短期调整但长期价值仍在",
    
    # 其他变量...
}

# 生成报告
report = template.format(**template_variables)
```

### 输出保存

生成的报告应保存到：
```
./output/summary/综合分析-{ticker}-{YYYY-MM-DD}.md
```

如果文件已存在，使用编号后缀：
```
./output/summary/综合分析-TSLA-2026-02-06.md
./output/summary/综合分析-TSLA-2026-02-06(1).md
./output/summary/综合分析-TSLA-2026-02-06(2).md
```
