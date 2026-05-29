# InvestFlow

`InvestFlow` is a repo-local Codex plugin for investment research workflows. The repository now treats the plugin package under `plugins/invest-flow/` as the canonical source for all investment skills.

## Included Skills

| Skill | 做什么 | 什么时候用 |
|---|---|---|
| `ai-infrastructure-sector-discovery` | 做 AI 基建板块周扫描、排序、打 `discovery_score` | 先找本周最值得深挖的 AI 基建方向时 |
| `ai-infrastructure-scarcity-radar` | 深挖 AI 基建稀缺环节，判断是真短缺还是高景气 | 已经锁定某个 AI 基建板块，准备做 6-24 个月深挖时 |
| `fundamental-analysis` | 做单个股票的基本面 + 技术面综合分析 | 想快速看一家公司值不值得继续研究时 |
| `earnings-report-analysis` | 从机构视角解读财报、电话会、guidance 和预期差 | 想判断一份财报是否改变盈利预期、估值中枢和投资动作时 |
| `institutional-accumulation-analysis` | 分析机构吸筹、派发和主力资金行为 | 想判断主力是在买入还是出货时 |
| `gie-investment-framework` | 用 GIE 框架找 1-3 年有爆发潜力的“金铲子”资产 | 想找中期高弹性机会或分析产业链受益者时 |
| `non-consensus-company-discovery` | 从主题或产业链中发现高潜力非共识公司，按 100 分模型筛出 Top 1-3 跟踪标的 | 想寻找市场仍按旧逻辑定价、但可能在 6-24 个月重估的公司时 |
| `gold-trend-analysis` | 分析黄金趋势、泡沫风险和宏观驱动 | 研究黄金价格、泡沫风险或交易框架时 |
| `reflexivity-quick-scan` | 快速判断一个股票/主题所处的反身性阶段 | 想先用 5 分钟判断叙事是启动、强化还是透支时 |
| `reflexivity-deep-analysis` | 对股票、行业或主题做完整反身性深度研究 | 需要完整拆解叙事、资金、价格与现实验证时 |
| `professional-investment-analyst` | 生成买方视角的专业个股研究报告 | 需要正式、可跟踪、可复盘的单公司深度报告时 |
| `reportify-stock-analysis` | 按统一模板生成结构化个股报告 | 想稳定输出标准化投研报告时 |
| `daily-us-market-scan` | 生成中文《美股收盘日报》与日常复盘 | 每日复盘昨夜美股、板块、异动和次日计划时 |
| `multi-agent-stock-analysis` | 在 Codex 当前会话中编排基本面、机构资金、GIE、反身性、Reportify、非共识等分析并汇总结论 | 想一次拿到多维度交叉验证结果时 |
| `market-data-router` | 路由和兜底金融数据源，获取行情/订单簿/期权数据 | 需要稳定抓取市场数据给其他分析流程使用时 |

## Current Structure

```text
.
├── AGENTS.md
├── README.md
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── invest-flow/
│       ├── .codex-plugin/plugin.json
│       ├── assets/
│       └── skills/
│           ├── ai-infrastructure-scarcity-radar/
│           ├── ai-infrastructure-sector-discovery/
│           ├── fundamental-analysis/
│           ├── earnings-report-analysis/
│           ├── institutional-accumulation-analysis/
│           ├── gie-investment-framework/
│           ├── non-consensus-company-discovery/
│           ├── gold-trend-analysis/
│           ├── reflexivity-quick-scan/
│           ├── reflexivity-deep-analysis/
│           ├── professional-investment-analyst/
│           ├── reportify-stock-analysis/
│           ├── daily-us-market-scan/
│           ├── multi-agent-stock-analysis/
│           └── market-data-router/
└── output/
```

## Plugin Location

- Plugin root: `plugins/invest-flow`
- Plugin manifest: `plugins/invest-flow/.codex-plugin/plugin.json`
- Repo marketplace: `.agents/plugins/marketplace.json`

## Install In Codex

1. Open this repository in Codex.
2. Reload Codex so it reads `.agents/plugins/marketplace.json`.
3. Open the plugin marketplace and install `InvestFlow`.

If `InvestFlow` does not appear, verify that `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` both exist and contain valid JSON.

## Use In Codex

After installation, call the packaged skills directly through normal prompts.

Examples:

- `Use InvestFlow to run a multi-agent analysis for TSLA.`
- `使用 invest-flow:multi-agent-stock-analysis 分析 MRVL`
- `Use InvestFlow to analyze institutional accumulation in AAPL over the last 3 months.`
- `使用 invest-flow:earnings-report-analysis 解读 NVDA 最新财报`
- `Use InvestFlow to assess gold bubble risk this week.`
- `Use InvestFlow to perform a reflexivity quick scan on NVIDIA.`
- `Use InvestFlow to run a deep reflexivity analysis on AI power infrastructure.`
- `Use InvestFlow to build a professional investment analyst report for TSLA.`
- `Use InvestFlow to generate a structured stock report for TSLA.`
- `Use InvestFlow to generate a daily US market close report.`
- `Use InvestFlow to fetch 5m market data for TSLA with market-data-router.`
- `Use InvestFlow to evaluate whether NVIDIA is a GIE-style golden shovel asset.`
- `使用 invest-flow:non-consensus-company-discovery 发现 AI 数据中心电力里的非共识公司`

## Environment Variables

If you want `market-data-router` to use external market data providers, create a local `.env` from `.env_example`:

```bash
cp .env_example .env
```

Current template variables:

- `POLYGON_API_KEY` - Polygon API key for US options and dark-pool related data
- `ALLTICK_API_KEY` - AllTick API key for routed quote/bar data
- `YAHOO_ENABLED` - enable Yahoo fallback when routed sources are unavailable
- `ALLTICK_BASE_URL` - AllTick API base URL
- `POLYGON_BASE_URL` - Polygon API base URL

The packaged scripts search for `.env` automatically from the current working directory upward, so placing `.env` in the repo root is sufficient.

## Direct Script Usage

You can also run the packaged scripts directly from the repo root:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company "Tesla"
python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --market US --symbol TSLA --interval 5m --types bars --out -
python plugins/invest-flow/skills/earnings-report-analysis/scripts/generate_report.py --ticker NVDA --company "NVIDIA" --period "FY2026 Q1"
python plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py --theme "AI 数据中心电力"
```

The multi-agent script is a prompt-plan helper only. Recommended analysis usage is still the Codex prompt form: `使用 invest-flow:multi-agent-stock-analysis 分析 MRVL`.

## Output Paths

Generated analysis files are written under `output/`:

- `output/fundamental-analysis/`
- `output/earnings-report-analysis/`
- `output/ai-infrastructure-sector-discovery/`
- `output/ai-infrastructure-scarcity-radar/`
- `output/institutional-accumulation-analysis/`
- `output/gie-investment-framework/`
- `output/non-consensus-company-discovery/`
- `output/gold-analysis/`
- `output/reflexivity-quick-scan/`
- `output/reflexivity-deep-analysis/`
- `output/professional-investment-analyst/`
- `output/reportify-stock-analysis/`
- `output/daily-us-market-scan/`
- `output/summary/`
- `output/cache/market-data/`

## Notes

- This is a repo-local plugin, not a published remote marketplace plugin.
- Investment skills are maintained only inside `plugins/invest-flow/skills/`.
- `.agents/plugins/marketplace.json` is the only remaining repo-local `.agents` asset needed for plugin discovery.
