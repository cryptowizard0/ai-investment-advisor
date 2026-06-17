# chain-alpha 产业链选股汇总报告：人形机器人

- 日期：2026-06-17
- 作者：InvestmentFlow
- 执行模式：Task 7 compact proof rerun
- 目的：端到端证明 chain-alpha 新合同下非美可投市场模式可工作；本报告复用 2026-06-15 证据轨迹，不构成完整重新调研。

## 一、创建的步骤报告

- Step 1: output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-人形机器人-2026-06-17.md
- Step 2: output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-行星滚柱丝杠-2026-06-17.md
- Step 2: output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-稀土永磁-2026-06-17.md
- Step 2: output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-谐波减速器-2026-06-17.md
- Step 3: output/chain-alpha-verification/chain-alpha-verification-688017-2026-06-17.md
- Step 3: output/chain-alpha-verification/chain-alpha-verification-300748-2026-06-17.md
- Step 3: output/chain-alpha-verification/chain-alpha-verification-603667-2026-06-17.md
- Step 3: output/chain-alpha-verification/chain-alpha-verification-MP-2026-06-17.md

## 二、一句话结论

Proof rerun 成功验证：**A 股候选可以进入 Step 3 并获得真实档位/仓位结论，不能仅因非美上市地被剔除**。绿的谐波（688017.SH）进入并获得通过档；金力永磁（300748.SZ）进入但因机器人专项收入占比不足为待验证；五洲新春（603667.SH）进入但因 PRS/机器人收入占比硬门槛失败被剔除；MP 作为美股 comparator 维持待验证。

## 三、错位环节与评分

| 环节 | 错位评分 | 本次处理 |
|---|---:|---|
| 行星滚柱丝杠 PRS | 20/20 | Step 2 放行 A 股候选五洲新春进入 Step 3，最终按收入占比剔除 |
| 稀土永磁 NdFeB | 16/20 | Step 2 放行金力永磁与 MP；金力永磁因机器人专项收入占比待验证，MP 维持待验证 |
| 谐波减速器 | 14/20 | Step 2 放行绿的谐波；Step 3 给通过档和 1.0% 研究仓位上限 |

## 四、候选漏斗

| 阶段 | 数量 | 说明 |
|---|---:|---|
| 全景环节 | 约 18 | 上游材料/基础件、中游传动、电机、下游本体与生态支撑 |
| 错位环节 | 3 | PRS / 稀土永磁 / 谐波减速器 |
| 硬门槛存活候选 | 6+ | 含 GSA、新剑传动、绿的谐波、Harmonic Drive、金力永磁、MP 等 |
| **可投候选进入验证（标注市场）** | **4** | 688017.SH（A 股科创板）、300748.SZ（A 股创业板）、603667.SH（A 股主板）、MP（NYSE） |
| 通过及以上档位 | 1 | 绿的谐波 66/100，通过，研究仓位上限 1.0% |

## 五、Step 3 最终结果

| 公司 | Ticker | 上市地/市场 | 环节 | 档位 | 总分 | 仓位上限 | 结论原因 |
|---|---|---|---|---|---:|---|---|
| 绿的谐波 | 688017.SH | A 股科创板 | 谐波减速器 | 通过 | 66/100 | 1.0% | 主业纯正、毛利和认证壁垒过线；未因 A 股过滤 |
| 金力永磁 | 300748.SZ | A 股创业板 | 稀土永磁/GBD NdFeB | 待验证 | 58/100 | 不适用 | A 股允许进入，但机器人专项收入占比仍低/不清晰 |
| 五洲新春 | 603667.SH | A 股上交所主板 | PRS/轴承/丝杠链 | 剔除 | 34/100 | 不适用 | A 股允许进入；剔除原因是 PRS/机器人收入约 0.22%，低于 20% |
| MP Materials | MP | NYSE 主板 | 稀土矿山/分离/磁体一体化 | 待验证 | 50/100 | 不适用 | 美股 comparator；人形机器人直接收入弱且估值透支 |

## 六、背景/no position

| 公司 | 市场状态 | 处理 |
|---|---|---|
| 新剑传动 | 未上市/A 股 IPO 辅导 | 产业背景，不给仓位 |
| Harmonic Drive HSYDF | 仅 OTC 粉单 | 背景/no position；本次不对粉单给仓位 |
| GSA AG / Bosch Rexroth / Proterial / VAC | 私有或集团子公司 | 产业格局背景 |

## 七、证明点

| 旧行为风险 | 本次 proof 结果 |
|---|---|
| Step 2 使用 `US-listed/ADR 候选` 语义，把 A 股强标的归为背景 | 三份 2026-06-17 Step 2 报告均使用 `## 六、进入第三步的可投候选（标注市场）`，表字段为 `上市地与可投性` |
| A 股候选被市场属性提前剔除 | 688017.SH、300748.SZ、603667.SH 均进入 Step 3 |
| 非市场原因没有被清晰区分 | 603667.SH 被收入占比硬门槛剔除；300748.SZ 因机器人专项收入占比待验证；不是因 A 股剔除 |
| OTC 粉单与未上市公司被误给仓位 | HSYDF 和新剑传动均明确为 background/no position |

## 八、数据来源

| 来源 | 用途 |
|---|---|
| 2026-06-15 Step 1/2/3 本地报告 | carried-forward source trail，复用全景、错位、份额、收入占比与 MP 估值判断 |
| 主 agent 提供的 MP 公开事实标签 | DoD $400M 支持与 $110/kg NdPr price floor；Apple $500M 稀土磁体协议；10X 工厂 2028 年 10,000 吨/年目标 |
| 2026-06-17 本次 Step 报告 | 验证新合同的 handoff 字段、A 股进入 Step 3 和最终档位 |

---
*本报告仅为 chain-alpha 非美市场模式 proof rerun 和研究优先级验证，不构成投资建议。*
