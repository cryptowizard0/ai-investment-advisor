# InvestFlow

[中文文档](README.zh-CN.md)

InvestFlow is a repo-local agent plugin for investment research, compatible with both Codex and Claude Code. It bundles reusable skills for market scans, industry-chain research, non-consensus discovery, single-stock analysis, buyability scoring, earnings review, reflexivity analysis, and routed market data.

The canonical plugin package lives in `plugins/invest-flow/`. Packaged skills live in `plugins/invest-flow/skills/` and are shared by both platforms.

## Quick Start

### Codex

1. Open this repository in Codex.
2. Reload Codex so it reads `.agents/plugins/marketplace.json`.
3. Install `InvestFlow` from the local plugin marketplace.
4. Use the skills directly in Codex prompts.

### Claude Code

1. Start `claude` in this repository.
2. Add the local marketplace: `/plugin marketplace add .`
3. Install the plugin: `/plugin install invest-flow@investflow-local`
4. Use the skills directly in prompts, or invoke a specific skill with `/invest-flow:skill-name`.

Examples (both platforms):

```text
Use InvestFlow to run a multi-agent analysis for TSLA.
Use InvestFlow to scan the US market close today.
Use InvestFlow to find non-consensus companies in AI data center power.
Use InvestFlow to analyze the HBM industry chain.
```

If the plugin does not appear, confirm these files exist:

- Codex: `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`
- Claude Code: `plugins/invest-flow/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

## Recommended Workflows

| Goal | Recommended flow |
|---|---|
| Find AI infrastructure opportunities | Start with `ai-infrastructure-sector-discovery`, then use `ai-infrastructure-scarcity-radar` on the strongest scarcity theme. |
| Find investable companies from an industry chain | Use `chain-alpha-pipeline` for the full mismatch -> monopoly -> verification funnel, or run `chain-alpha-mismatch-discovery` alone first to confirm the mismatch links cheaply. |
| Track whether a 待验证 name's revenue is delivering | After the funnel leaves a name at `待验证`, use `chain-alpha-delivery-tracking` for a quarterly revenue-delivery read (5-gate ladder + growth/attribution/valuation engines) that feeds the grade back into `chain-alpha-verification`. |
| Map a sector and find non-consensus names | Start with `industry-chain-analysis`, then use `non-consensus-company-discovery` on the most interesting bottleneck or module. |
| Run daily market review | Use `daily-us-market-scan` after the US close. |
| Track narrative and reflexivity risk | Use `reflexivity-quick-scan` regularly; upgrade to `reflexivity-deep-analysis` when the stage changes or the position is material. |
| Quick single-stock research | Use `multi-agent-stock-analysis` to start with `company-profile`, then cross-check fundamentals, capital flow, GIE, reflexivity, Reportify, and non-consensus views. |
| Review earnings | Use `earnings-report-analysis` after a company reports, then update the single-stock thesis if guidance or expectations changed. |
| Score whether a stock is buyable | Use `company-buyability-score` for a quantified AI exposure, growth, drawdown, sentiment mismatch, and risk review. |
| Produce a formal stock report | Use `professional-investment-analyst` for a buy-side style report, or `reportify-stock-analysis` for a standardized structured report. |
| Pull market data | Use `market-data-router` when another workflow needs bars, quote data, options context, or cached market data. |
| Index generated reports | Use `output-report-index` when you explicitly want to generate or update `output/index.md` and `output/index.html`. |

## Skill List

| Skill | Purpose | Use when |
|---|---|---|
| `ai-infrastructure-sector-discovery` | Weekly AI infrastructure sector scan and scoring. | You want to identify the best AI infrastructure themes to research next. |
| `ai-infrastructure-scarcity-radar` | Deep scarcity and bottleneck analysis for AI infrastructure. | You already have a theme and need to judge whether scarcity is real and investable. |
| `chain-alpha-mismatch-discovery` | Full industry-chain panorama and supply-demand mismatch link discovery. | You have a big theme and need the whole chain mapped plus the links where demand outruns supply. |
| `chain-alpha-monopoly-screen` | Sub-link breakdown and monopoly screening with CR3, margin, and revenue-share gates. | You confirmed a mismatch link and need the <=10 strongest companies in it. |
| `chain-alpha-verification` | 100-point four-tier company verification with drawdown-based position sizing. | You have US-listed candidates and need a buy/watch/reject grade plus a position cap. |
| `chain-alpha-pipeline` | Orchestrates the three chain-alpha steps with in-step subagent fan-out (Claude Code parallel; Codex parallel when explicitly requested and available; otherwise serial fallback) and funnel discipline. | You want the full theme-to-company workflow in one run. |
| `chain-alpha-delivery-tracking` | Forward-looking revenue-delivery tracking for 待验证 candidates with a 5-gate ladder, growth/attribution/dynamic-valuation engines, and symmetric grade up/down. | You hold a 待验证 name (e.g. 绿的谐波) and need a quarterly read on whether revenue is actually being delivered. |
| `company-profile` | Builds a company primer before investment analysis. | Use when a user is hearing about a company for the first time and needs business, technology, value-chain, AI relevance, competitors, and industry-position context. |
| `company-buyability-score` | Quantified buyability score for a US-listed company or ADR. | You need to judge whether a company is buyable using AI exposure, value-chain position, growth, drawdown risk, sentiment mismatch, and negative factors. |
| `daily-us-market-scan` | Chinese US market close report and next-session review. | You want a daily read on indices, sectors, themes, breadth, earnings, and watchlists. |
| `earnings-report-analysis` | Institutional earnings, guidance, call, and expectation-gap analysis. | A company has reported and you need to know whether the thesis changed. |
| `fundamental-analysis` | Single-stock fundamental, valuation, and technical analysis. | You need a fast but structured view of a company. |
| `gie-investment-framework` | GIE framework for 1-3 year golden-shovel opportunities. | You want to test whether a company or industry benefits from durable bottlenecks. |
| `gold-trend-analysis` | Gold trend, bubble-risk, and macro-driver analysis. | You are researching gold prices, macro risk, or a gold trading framework. |
| `industry-chain-analysis` | Two-layer industry-chain and bottleneck mapping. | You need to understand upstream, midstream, downstream, and module-level constraints. |
| `institutional-accumulation-analysis` | Institutional accumulation and distribution analysis. | You want to judge whether major players are buying, distributing, or hedging. |
| `market-data-router` | Routed market-data fetching and fallback logic. | You need bars, quote data, options context, or cached market data for analysis. |
| `multi-agent-stock-analysis` | In-session orchestration across multiple stock-analysis skills. | You want one stock analyzed from several independent angles. |
| `non-consensus-company-discovery` | Theme-to-company discovery for high-potential non-consensus opportunities. | You want names the market may still value using the wrong framework. |
| `output-report-index` | Markdown and static HTML index pages for generated reports. | You explicitly ask to generate or update the report index under `output/`. |
| `professional-investment-analyst` | Buy-side style company research system. | You need a formal, trackable, evidence-based stock report. |
| `reflexivity-deep-analysis` | Full reflexivity-cycle analysis for a stock, sector, asset, or narrative. | You need to map narrative, price, reality, marginal change, and reversal risk. |
| `reflexivity-quick-scan` | Fast reflexivity stage check. | You need a quick read on whether a narrative is starting, strengthening, exhausted, or reversing. |
| `reportify-stock-analysis` | Standardized structured stock report. | You need a repeatable report format for facts, interpretation, decision, and risk. |

## Use Skills In Agent

Use InvestFlow through natural-language prompts in Codex or Claude Code. Prefer skill names when you want a specific workflow:

```text
Use invest-flow:multi-agent-stock-analysis to analyze TSLA.
Use invest-flow:daily-us-market-scan to scan today's US market close.
Use invest-flow:industry-chain-analysis to map the HBM industry chain.
Use invest-flow:non-consensus-company-discovery to find non-consensus opportunities in AI data center power.
Use invest-flow:chain-alpha-pipeline to find investable companies in AI data center power.
Use invest-flow:reflexivity-quick-scan to check NVIDIA's current narrative stage.
Use invest-flow:company-buyability-score to score whether NVIDIA is buyable.
Use invest-flow:earnings-report-analysis to analyze NVIDIA's latest earnings.
Use invest-flow:output-report-index to update the output report index.
```

For provider-backed market data, create a local `.env` from `.env_example` and add the relevant API keys.

## Output Paths

Generated reports and cache files are written under `output/`:

| Workflow | Output path |
|---|---|
| Company profile | `output/company-profile/` |
| Company buyability score | `output/company-buyability-score/` |
| Fundamental analysis | `output/fundamental-analysis/` |
| Earnings report analysis | `output/earnings-report-analysis/` |
| AI infrastructure sector discovery | `output/ai-infrastructure-sector-discovery/` |
| AI infrastructure scarcity radar | `output/ai-infrastructure-scarcity-radar/` |
| Chain-alpha mismatch discovery | `output/chain-alpha-mismatch-discovery/` |
| Chain-alpha monopoly screen | `output/chain-alpha-monopoly-screen/` |
| Chain-alpha verification | `output/chain-alpha-verification/` |
| Chain-alpha pipeline summary | `output/chain-alpha-pipeline/` |
| Chain-alpha delivery tracking | `output/chain-alpha-delivery-tracking/` |
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
| Report index | `output/index.md`, `output/index.html` |
| Market data cache | `output/cache/market-data/` |

Existing files should not be overwritten. Skills append suffixes such as `(1)` and `(2)` when needed.

Open the HTML report reader through the UTF-8 report server so it can fetch Markdown files on demand and direct `.md` links render Chinese correctly:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000
# then open http://127.0.0.1:8000/output/index.html
```

## Report Index Reader

`output-report-index` builds two local index files from the Markdown reports already under `output/`:

- `output/index.md` - a Markdown index grouped by first-level output category.
- `output/index.html` - a static single-page report reader with metrics, search, collapsible categories, and on-demand Markdown rendering.

The skill is intentionally passive. It should only run when the user explicitly asks to generate or update the index, for example:

```text
生成索引
更新索引
Use invest-flow:output-report-index to update the output report index.
```

To regenerate the files manually:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py
```

The generated HTML page does not convert each report into a separate HTML file. Report links use hash routes inside `output/index.html`; when a report is selected, the page calls `fetch()` for the original `.md` file and renders it in the reader pane. The "原文" links still point directly to the source Markdown files.

For local preview, use the bundled UTF-8 server:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000
```

Then open:

```text
http://127.0.0.1:8000/output/index.html
```

Avoid using bare `python -m http.server` for this reader. Python's default static server can serve `.md` files without `charset=utf-8`, and Chrome may display Chinese report text as mojibake when opening direct Markdown links. The bundled `serve_reports.py` sets UTF-8 headers for `.md` and `.html` files.

## Maintenance Notes

- This is a repo-local plugin, not a remote marketplace package.
- Keep investment skills under `plugins/invest-flow/skills/`; both platforms load the same skill files.
- Keep Codex plugin discovery metadata in `.agents/plugins/marketplace.json` and Claude Code metadata in `.claude-plugin/marketplace.json`.
- When plugin packaging changes, update both manifests (`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`) and keep versions in sync.
- Keep README skill names aligned with the directories under `plugins/invest-flow/skills/`.
