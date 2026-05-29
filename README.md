# InvestFlow

[Chinese version](README.zh-CN.md)

InvestFlow is a repo-local Codex plugin for investment research. It bundles reusable skills for market scans, industry-chain research, non-consensus discovery, single-stock analysis, earnings review, reflexivity analysis, and routed market data.

The canonical plugin package lives in `plugins/invest-flow/`. Packaged skills live in `plugins/invest-flow/skills/`.

## Quick Start

1. Open this repository in Codex.
2. Reload Codex so it reads `.agents/plugins/marketplace.json`.
3. Install `InvestFlow` from the local plugin marketplace.
4. Use the skills directly in Codex prompts.

Examples:

```text
Use InvestFlow to run a multi-agent analysis for TSLA.
Use InvestFlow to scan the US market close today.
Use InvestFlow to find non-consensus companies in AI data center power.
Use InvestFlow to analyze the HBM industry chain.
```

If the plugin does not appear, confirm these files exist:

- `plugins/invest-flow/.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

## Recommended Workflows

| Goal | Recommended flow |
|---|---|
| Find AI infrastructure opportunities | Start with `ai-infrastructure-sector-discovery`, then use `ai-infrastructure-scarcity-radar` on the strongest scarcity theme. |
| Map a sector and find non-consensus names | Start with `industry-chain-analysis`, then use `non-consensus-company-discovery` on the most interesting bottleneck or module. |
| Run daily market review | Use `daily-us-market-scan` after the US close. |
| Track narrative and reflexivity risk | Use `reflexivity-quick-scan` regularly; upgrade to `reflexivity-deep-analysis` when the stage changes or the position is material. |
| Research one stock quickly | Use `multi-agent-stock-analysis` for cross-checking across fundamentals, flows, GIE, reflexivity, Reportify, and non-consensus views. |
| Review earnings | Use `earnings-report-analysis` after a company reports, then update the single-stock thesis if guidance or expectations changed. |
| Produce a formal stock report | Use `professional-investment-analyst` for a buy-side style report, or `reportify-stock-analysis` for a standardized structured report. |
| Pull market data | Use `market-data-router` when another workflow needs bars, quote data, options context, or cached market data. |

## Skill List

| Skill | Purpose | Use when |
|---|---|---|
| `ai-infrastructure-sector-discovery` | Weekly AI infrastructure sector scan and scoring. | You want to identify the best AI infrastructure themes to research next. |
| `ai-infrastructure-scarcity-radar` | Deep scarcity and bottleneck analysis for AI infrastructure. | You already have a theme and need to judge whether scarcity is real and investable. |
| `daily-us-market-scan` | Chinese US market close report and next-session review. | You want a daily read on indices, sectors, themes, breadth, earnings, and watchlists. |
| `earnings-report-analysis` | Institutional earnings, guidance, call, and expectation-gap analysis. | A company has reported and you need to know whether the thesis changed. |
| `fundamental-analysis` | Single-stock fundamental, valuation, and technical analysis. | You need a fast but structured view of a company. |
| `gie-investment-framework` | GIE framework for 1-3 year golden-shovel opportunities. | You want to test whether a company or industry benefits from durable bottlenecks. |
| `gold-trend-analysis` | Gold trend, bubble-risk, and macro-driver analysis. | You are researching gold prices, macro risk, or a gold trading framework. |
| `industry-chain-analysis` | Two-layer industry-chain and bottleneck mapping. | You need to understand upstream, midstream, downstream, and module-level constraints. |
| `institutional-accumulation-analysis` | Institutional accumulation and distribution analysis. | You want to judge whether major players are buying, distributing, or hedging. |
| `market-data-router` | Routed market-data fetching and fallback logic. | You need bars, quote data, options context, or cached market data for analysis. |
| `multi-agent-stock-analysis` | Codex-native orchestration across multiple stock-analysis skills. | You want one stock analyzed from several independent angles. |
| `non-consensus-company-discovery` | Theme-to-company discovery for high-potential non-consensus opportunities. | You want names the market may still value using the wrong framework. |
| `professional-investment-analyst` | Buy-side style company research system. | You need a formal, trackable, evidence-based stock report. |
| `reflexivity-deep-analysis` | Full reflexivity-cycle analysis for a stock, sector, asset, or narrative. | You need to map narrative, price, reality, marginal change, and reversal risk. |
| `reflexivity-quick-scan` | Fast reflexivity stage check. | You need a quick read on whether a narrative is starting, strengthening, exhausted, or reversing. |
| `reportify-stock-analysis` | Standardized structured stock report. | You need a repeatable report format for facts, interpretation, decision, and risk. |

## Use Skills In Agent

Use InvestFlow through natural-language prompts in the Codex agent. Prefer skill names when you want a specific workflow:

```text
Use invest-flow:multi-agent-stock-analysis to analyze TSLA.
Use invest-flow:daily-us-market-scan to scan today's US market close.
Use invest-flow:industry-chain-analysis to map the HBM industry chain.
Use invest-flow:non-consensus-company-discovery to find non-consensus opportunities in AI data center power.
Use invest-flow:reflexivity-quick-scan to check NVIDIA's current narrative stage.
Use invest-flow:earnings-report-analysis to analyze NVIDIA's latest earnings.
```

For provider-backed market data, create a local `.env` from `.env_example` and add the relevant API keys.

## Output Paths

Generated reports and cache files are written under `output/`:

| Workflow | Output path |
|---|---|
| Fundamental analysis | `output/fundamental-analysis/` |
| Earnings report analysis | `output/earnings-report-analysis/` |
| AI infrastructure sector discovery | `output/ai-infrastructure-sector-discovery/` |
| AI infrastructure scarcity radar | `output/ai-infrastructure-scarcity-radar/` |
| Industry-chain analysis | `output/industry-chain-analysis/` |
| Institutional analysis | `output/institutional-accumulation-analysis/` |
| GIE framework | `output/gie-investment-framework/` |
| Non-consensus company discovery | `output/non-consensus-company-discovery/` |
| Gold analysis | `output/gold-analysis/` |
| Reflexivity quick scan | `output/reflexivity-quick-scan/` |
| Reflexivity deep analysis | `output/reflexivity-deep-analysis/` |
| Professional investment analyst | `output/professional-investment-analyst/` |
| Reportify stock analysis | `output/reportify-stock-analysis/` |
| Daily US market scan | `output/daily-us-market-scan/` |
| Multi-agent summaries | `output/summary/` |
| Market data cache | `output/cache/market-data/` |

Existing files should not be overwritten. Skills append suffixes such as `(1)` and `(2)` when needed.

## Maintenance Notes

- This is a repo-local plugin, not a remote marketplace package.
- Keep investment skills under `plugins/invest-flow/skills/`.
- Keep plugin discovery metadata in `.agents/plugins/marketplace.json`.
- Keep README skill names aligned with the directories under `plugins/invest-flow/skills/`.
