# 严重问题修复记录

**修复日期**: 2026-02-10  
**修复版本**: v1.1  
**修复内容**: P0级别严重问题

---

## 修复清单

### ✅ 1. 评分卡与 VSA/Divergence 文档不一致 (P0)

**问题描述:**
- `scoring-system.md` 中有具体量化阈值，但 `vsa-patterns.md` 和 `divergence-guide.md` 中缺失
- 导致模型在不同文档间看到不一致的标准

**修复内容:**

#### vsa-patterns.md
- [x] 添加评分卡量化标准速查表
- [x] 更新所有模式，添加具体阈值:
  - 弹簧模式: 跌破>2%, 成交量>120%, 下影>实体2倍
  - 强势突破: 突破>3%, 成交量>150%, 收高位80%以上
  - 量缩整理: 振幅<2%, 成交量<50%, 整理3日+
  - 放量滞涨: 成交量>150%, 涨幅<1%, 上影>实体2倍
  - 上抛失败: 假突破>2%, 回落, 次日低开
  - 量增下跌: 成交量>130%, 跌>2%, 收低位
- [x] 每个模式添加评分卡权重和计分规则

#### divergence-guide.md
- [x] 添加评分卡量化标准速查表
- [x] 更新 OBV 背离，添加量化阈值:
  - 强底背离: 价格20日新低(跌>5%) + OBV高>3% + 3个低点
  - 弱底背离: 价格10日新低 + OBV未新低(<3%) + 2个低点
  - 强顶背离: 价格20日新高(涨>5%) + OBV低>3% + 3个高点
  - 弱顶背离: 价格10日新高 + OBV未新高(<3%) + 2个高点
- [x] 更新 RSI 背离，添加阈值: 抬高/降低>5点

**影响:** 所有文档现在使用一致的量化标准

---

### ✅ 2. "必要条件"设计缺陷 (P0)

**问题描述:**
- 原设计: 强力吸筹要求 VSA≥+10 **且** 技术≥+10
- 问题: 排除了"量价极强+技术中等"的合理场景
- 示例: VSA +20, 技术 +8, 总分 +58 → 按原规则只能是温和吸筹，但明显应该更强

**修复内容:**

#### scoring-system.md
修改分类必要条件:

```diff
强力吸筹:
- 必要条件: VSA ≥ +10 且 技术 ≥ +10
+ 必要条件: (VSA ≥ +10 且 技术 ≥ +5) 或 (VSA ≥ +5 且 技术 ≥ +10)

温和吸筹:
- 必要条件: VSA ≥ +5 或 技术 ≥ +5
+ 必要条件: VSA ≥ +5 或 技术 ≥ +5 或 任一维度 ≥ +20

派发初级:
- 必要条件: VSA ≤ -5 或 技术 ≤ -5
+ 必要条件: VSA ≤ -5 或 技术 ≤ -5 或 任一维度 ≤ -20

疯狂出货:
- 必要条件: VSA ≤ -10 且 技术 ≤ -10
+ 必要条件: (VSA ≤ -10 且 技术 ≤ -5) 或 (VSA ≤ -5 且 技术 ≤ -10)
```

添加单一维度极端例外条款:
```
if VSA ≥ +20 且 总分 < +50:
    分类 = "温和吸筹"
    置信度 = 计算置信度 × 0.7
    
if 技术 ≥ +20 且 总分 < +50:
    分类 = "温和吸筹"
    置信度 = 计算置信度 × 0.7
```

**影响:** 更合理地处理"单一维度极强"的场景

---

### ✅ 3. 置信度计算的"证据加成"表有歧义 (P0)

**问题描述:**
- 原定义: "强证据: 权重 ≥ 8分"
- 歧义: 权重=8分的信号是强证据还是弱证据？
- 风险: 不同模型理解不同，导致置信度计算不一致

**修复内容:**

#### scoring-system.md
采用严格大于定义，消除歧义:

```diff
证据级别定义:
- 强证据: 权重 ≥ 8分
- 弱证据: 权重 < 8分

+ 强证据: 权重 > 8分 (即9分及以上)
+ 中证据: 权重 = 8分
+ 弱证据: 权重 < 8分 (即7分及以下)
```

更新加成表，增加"中证据"列:
```
| 强(>8) | 中(=8) | 弱(<8) | 加成 |
|--------|--------|--------|------|
| ≥5     | 任何   | 任何   | +25% |
| 4      | ≥1     | 任何   | +22% |
| 4      | 0      | ≥2     | +20% |
... (共15档，精确覆盖所有组合)
```

添加使用示例:
```
3个强证据(>8) + 2个中证据(=8) → 查表第6行 → +17%
2个强证据(>8) + 1个中证据(=8) + 3个弱证据(<8) → 查表第10行 → +10%
```

**影响:** 证据级别定义清晰，无边界歧义

---

### ✅ 4. 输出目录不一致 (P0)

**问题描述:**
```
SKILL.md:      ./output/institutional-accumulation-analysis/
save_report.py: ./institutional-accumulation-analysis/
```

**修复内容:**

#### save_report.py
```diff
def get_output_directory():
    """Get the output directory path."""
-   return Path.cwd() / "institutional-accumulation-analysis"
+   # Standard output path: ./output/institutional-accumulation-analysis/
+   output_dir = Path.cwd() / "output" / "institutional-accumulation-analysis"
+   
+   # Handle running from scripts directory
+   if "scripts" in Path.cwd().name or ".agents" in str(Path.cwd()):
+       # Navigate to project root
+       ...
+   
+   return output_dir
```

**影响:** 脚本输出路径与文档一致

---

### ✅ 5. 引用的 Python 脚本不存在 (P1)

**问题描述:**
```
SKILL.md 引用但不存在的脚本:
- calculate_obv.py
- detect_divergence.py
- volume_profile.py

实际只有:
- save_report.py
```

**评估结论:** 这些脚本不必要

**理由:**
1. **核心价值在评分卡**: 本 skill 的核心是分析框架和量化标准，不是基础指标计算
2. **数据可获取**: OBV/CMF/RSI 等指标可从 Yahoo Finance、TradingView 等直接获取
3. **维护成本**: 开发这些脚本需要处理大量边界情况，维护成本高
4. **AI 能力**: AI 分析时可以直接从数据源获取已计算的指标

**修复内容:**

#### SKILL.md
```diff
### scripts/
- **save_report.py** - Save analysis report
- **calculate_obv.py** - OBV calculation
- **detect_divergence.py** - Divergence detection
- **volume_profile.py** - Volume profile

+ ### scripts/
+ **save_report.py** - Save analysis report to `./output/institutional-accumulation-analysis/`
+ 
+ > **注意**: 本 skill 依赖评分卡量化系统进行主观分析。技术指标建议从专业数据源
+ > 直接获取，或使用 pandas/ta-lib 计算。评分卡的核心价值在于**分析框架和量化标准**。
```

**影响:** 移除不存在的引用，明确 skill 的核心价值

---

## 修复验证清单

- [x] 所有文档阈值一致
- [x] 分类必要条件合理
- [x] 证据级别定义清晰
- [x] 输出路径统一
- [x] 脚本引用清理

---

## 版本变更

### v1.0 → v1.1

**重大变更:**
1. 文档阈值统一化
2. 分类条件优化
3. 证据定义精确化

**兼容性:**
- 向后兼容: 总分计算方式不变
- 向前兼容: 新条件更宽松，不会将原"强力吸筹"降级

**建议:**
- 重新阅读 `scoring-quickref.md` 了解最新阈值
- 使用示例见 `scoring-examples.md`
