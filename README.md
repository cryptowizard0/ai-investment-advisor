# InvestFlow

[中文文档](README.zh-CN.md)

InvestFlow is a repo-local agent plugin for investment research, compatible with both Codex and Claude Code. It bundles reusable skills for market scans, industry-chain research, non-consensus discovery, single-stock analysis, earnings review, reflexivity analysis, and routed market data.

Its flagship workflow is **chain-alpha** — a theme → industry-chain → investable-company funnel with ongoing revenue/profit-delivery tracking. See [Featured Workflow: chain-alpha](#featured-workflow-chain-alpha).

At a glance, the skills fall into four user-facing categories, grouped by what you bring in (plus a supporting infrastructure layer):

| Category | Input | Start with | For |
|---|---|---|---|
| **1. Find opportunities** | a theme | `chain-alpha` | Turn a big theme into investable companies |
| **2. Research a single stock** | a ticker | `multi-agent-stock-analysis` | Judge one company from several independent angles |
| **3. Daily & periodic tracking** | a calendar | `daily-us-market-scan` | Recurring reads that run well as scheduled tasks |
| **4. Cycle scanning** | an index | `index-bull-bear-cycle-tracking` | Maintain a close-to-close bull/bear cycle history |

See [Skills By Category](#skills-by-category) for the full list, including the infrastructure layer.

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
Use InvestFlow to map the HBM supply chain with chain-alpha.
```

If the plugin does not appear, confirm these files exist:

- Codex: `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`
- Claude Code: `plugins/invest-flow/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

## Featured Workflow: chain-alpha

chain-alpha is InvestFlow's flagship workflow: it turns a big theme into investable companies, defines the entry plan, then keeps tracking whether revenue and profit growth actually deliver. Six skills form a closed loop, orchestrated end-to-end by `chain-alpha`:

```text
theme ─▶ chain-alpha-mismatch ─▶ chain-alpha-monopoly ─▶ chain-alpha-verification ─▶ chain-alpha-entry-plan ⇄ chain-alpha-delivery-tracking
        industry + growth        sub-links +           4-tier grade               entry decision +         quarterly revenue/
        screen + mismatch        ≤10 candidates        (grading only)             staged buying plan       profit tracking
        └──────────────────── orchestrated by chain-alpha ────────────────────┘
```

Run the whole funnel in one command:

```text
Use invest-flow:chain-alpha to find investable companies in humanoid robots.
```

Funnel discipline: industry definition and growth gate → 2-4 mismatch links → ≤10 candidates per link → top-6 into verification → pass-and-above into step-4 position sizing → 2-3 deep dives. Industry/key-link revenue growth must be >20%, have a clear driver, and last at least 6 months before the workflow enters later steps; industry and company screens must still map back to sustainable profit growth: ≥30% is preferred, 20% is the minimum gate, and <20% is screened out. Step 3 `chain-alpha-verification` only grades; positions come exclusively from step 4 `chain-alpha-entry-plan` (position cap = drawdown budget / potential risk, with grade/elastic discounts). Names left at `pending-verification` are then tracked quarterly with `chain-alpha-delivery-tracking`, whose grade changes feed back into `chain-alpha-verification` and re-trigger step-4 sizing on upgrades. Each step can also run standalone — start with `chain-alpha-mismatch` to define the industry, screen growth, and confirm mismatch links cheaply before committing to the full run.

## Skills By Category

InvestFlow's skills group into four user-facing categories by what you bring in — a theme, a ticker, a calendar, or an index — plus a supporting infrastructure layer.

### 1. Find opportunities (you bring a theme)

Turn a big theme into investable companies. `chain-alpha` is the flagship — see [Featured Workflow: chain-alpha](#featured-workflow-chain-alpha).

| Skill | Purpose | Use when |
|---|---|---|
| `chain-alpha` | Orchestrates the four canonical chain-alpha steps (`chain-alpha-mismatch` → `chain-alpha-monopoly` → `chain-alpha-verification` → `chain-alpha-entry-plan`) with in-step subagent fan-out (Claude Code parallel; Codex parallel when explicitly requested and available; otherwise serial fallback) and funnel discipline. | You want the full theme-to-company-to-entry-plan workflow in one run. |
| `chain-alpha-mismatch` | Plain-language industry definition, growth hard gate with industry-cycle staging (four-stage timeline + current-stage marker), full industry-chain panorama, and supply-demand mismatch link discovery with a profit-growth gate. | You have a big theme and need to understand what the industry actually is, which cycle stage it is in, why growth can stay high, the whole chain, and the links where demand outruns supply and can translate into profit growth. |
| `chain-alpha-monopoly` | Sub-link breakdown and monopoly screening with CR3, margin, revenue-share, and profit-growth gates. | You confirmed a mismatch link and need the <=10 strongest companies in it. |
| `chain-alpha-verification` | 100-point four-tier company verification with profit-growth gating (grading only, no position sizing). | You have candidates and need a gold-pool/pass/pending/reject grade; pass-and-above names hand off to step 4 for sizing. |
| `chain-alpha-entry-plan` | chain-alpha step 4: type gate → PE/PS ruler (with alert lines) → 5-year TTM percentile band → potential risk → growth-digestion check → entry decision, position cap, entry range, staged buying plan, and blocking/reopen conditions. | Verification produced a grade and you need an executable entry plan. (Also listed under category 2.) |
| `chain-alpha-delivery-tracking` | Forward-looking revenue/profit-delivery tracking for pending-verification candidates with a 5-gate ladder plus delivery-window timeouts, growth/attribution/dynamic-valuation engines, structure sentinels, and symmetric grade up/down. | You hold a pending-verification name (e.g. a harmonic-reducer supplier) and need a quarterly read on whether revenue and profit growth are actually being delivered. (Also a quarterly tracking task — see category 3.) |
| `ai-infrastructure-sector-discovery` | Weekly AI infrastructure sector scan and scoring; the handoff queue feeds chain-alpha. | You want a scheduled weekly read on which AI infrastructure sectors to research next. (Also a weekly tracking task — see category 3.) |
| `non-consensus-company-discovery` | Theme-to-company discovery for high-potential non-consensus opportunities. | You want names the market may still value using the wrong framework. |

### 2. Research a single stock (you bring a ticker)

Judge one company from several independent angles. `multi-agent-stock-analysis` orchestrates the rest in one session.

| Skill | Purpose | Use when |
|---|---|---|
| `multi-agent-stock-analysis` | In-session orchestration across the single-stock skills below (company profile → fundamentals → capital flow → reflexivity → Reportify → non-consensus). | You want one stock analyzed from several independent angles. |
| `company-profile` | Builds a company primer before investment analysis. | A user is hearing about a company for the first time and needs business, technology, value-chain, AI relevance, competitors, and industry-position context. |
| `fundamental-analysis` | Single-stock fundamental, valuation, and technical analysis. | You need a fast but structured view of a company. |
| `chain-alpha-entry-plan` | Type-gated entry planning backed by a valuation percentile band, potential-risk calculation, growth-digestion check, and drawdown-budget position cap. The output owns the entry decision, position cap, entry range, staged buying plan, and blocking/reopen conditions. | You need an executable buying plan rather than valuation analysis alone. (Also chain-alpha step 4 — see category 1.) |
| `institutional-accumulation-analysis` | Institutional accumulation and distribution analysis. | You want to judge whether major players are buying, distributing, or hedging. |
| `reflexivity-analysis` | Soros-style reflexivity analysis with quick (5-minute stage check) and deep (full-cycle) modes. | You need to read where a narrative sits — a fast stage check, or a full narrative/price/reality/reversal map. |
| `reportify-stock-analysis` | Standardized 8-part stock report with a buy-side-grade decision layer (3-scenario valuation, falsifiable thesis, catalysts, tracking dashboard). | You need a repeatable, formal, trackable report covering facts, interpretation, decision, and risk. |
| `earnings-report-analysis` | Institutional earnings, guidance, call, and expectation-gap analysis. | A company has reported and you need to know whether the thesis changed. |

### 3. Daily & periodic tracking (you bring a calendar)

Recurring reads that work well as scheduled tasks.

| Skill | Cadence | Purpose |
|---|---|---|
| `daily-us-market-scan` | Daily (after US close) | Conclusion-first Chinese US market close report with a hard length budget, dynamic sector/theme ranking, and a new-dynamics radar. |
| `ai-infrastructure-sector-discovery` | Weekly | AI infrastructure sector scan whose handoff queue feeds chain-alpha (also listed under category 1). |
| `index-pe-sensitivity` | Weekly / ad-hoc | Index valuation price-sensitivity table (±price move -> TTM P/E, aggregate caliber -> N-year percentile) with single-caliber guardrails and cyclical-earnings distortion checks. |
| `chain-alpha-delivery-tracking` | Quarterly / on earnings | Revenue/profit-delivery tracking for pending-verification names (also listed under category 1). |
| `gold-trend-analysis` | Monthly / ad-hoc | Gold trend, bubble-risk, and macro-driver analysis. |

### 4. Cycle scanning (you bring an index)

Maintain a repeatable index cycle history from official EOD closes, with explicit confirmation rules and stable reports that can be updated in place.

| Skill | Cadence | Purpose |
|---|---|---|
| `index-bull-bear-cycle-tracking` | Daily / ad-hoc | Create and update index bull/bear cycle tables using a configurable close-to-close reversal threshold; record extrema, duration, amplitude, turning-point P/E, evidence-backed causes, and the latest complete-market-data date. |

### Infrastructure (supporting layer, no investment view of its own)

| Skill | Purpose | Use when |
|---|---|---|
| `market-data-router` | Routed market-data fetching and fallback logic. | Another workflow needs bars, quote data, options context, or cached market data. |
| `output-report-index` | Markdown and static HTML index pages for generated reports. | You explicitly ask to generate or update the report index under `output/`. |

## Use Skills In Agent

Use InvestFlow through natural-language prompts in Codex or Claude Code. Prefer skill names when you want a specific workflow:

```text
Use invest-flow:multi-agent-stock-analysis to analyze TSLA.
Use invest-flow:daily-us-market-scan to scan today's US market close.
Use invest-flow:non-consensus-company-discovery to find non-consensus opportunities in AI data center power.
Use invest-flow:chain-alpha to find investable companies in AI data center power.
Use invest-flow:reflexivity-analysis in quick mode to check NVIDIA's current narrative stage.
Use invest-flow:index-pe-sensitivity to build a valuation-sensitivity table for the STAR 50 index.
Use invest-flow:index-bull-bear-cycle-tracking to update the SOX bull and bear market cycle tables.
Use invest-flow:chain-alpha-entry-plan to create NVDA's entry decision, position cap, entry range, and staged buying plan.
Use invest-flow:earnings-report-analysis to analyze NVIDIA's latest earnings.
Use invest-flow:output-report-index to update the output report index.
```

For provider-backed market data, create a local `.env` from `.env_example` and add the relevant API keys.

## Output Paths

Generated reports and cache files are written under `output/`:

| Workflow | Output path |
|---|---|
| Company profile | `output/company-profile/` |
| Chain Alpha entry plan | `output/chain-alpha-entry-plan/` |
| Fundamental analysis | `output/fundamental-analysis/` |
| Earnings report analysis | `output/earnings-report-analysis/` |
| AI infrastructure sector discovery | `output/ai-infrastructure-sector-discovery/` |
| Chain-alpha mismatch discovery | `output/chain-alpha-mismatch/` |
| Chain-alpha monopoly screen | `output/chain-alpha-monopoly/` |
| Chain-alpha verification | `output/chain-alpha-verification/` |
| Chain Alpha summary | `output/chain-alpha/` |
| Chain-alpha delivery tracking | `output/chain-alpha-delivery-tracking/` |
| Index PE sensitivity | `output/index-pe-sensitivity/` |
| Index bull/bear cycle tracking | `output/index-market-cycles/` |
| Institutional analysis | `output/institutional-accumulation-analysis/` |
| Non-consensus company discovery | `output/non-consensus-company-discovery/` |
| Gold analysis | `output/gold-analysis/` |
| Reflexivity analysis | `output/reflexivity-analysis/` |
| Reportify stock analysis | `output/reportify-stock-analysis/` |
| Daily US market scan | `output/daily-us-market-scan/` |
| Multi-agent summaries | `output/summary/` |
| Report index | `output/index.md`, `output/index.html` |
| Market data cache | `output/cache/market-data/` |

Report generators normally avoid overwriting and append suffixes such as `(1)` and `(2)` when needed. Index bull/bear cycle documents are the exception: their stable filenames are updated in place so each index has one current bull table and one current bear table.

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
Generate the report index.
Update the report index.
Use invest-flow:output-report-index to update the output report index.
```

To regenerate the files manually:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py
```

The generated HTML page does not convert each report into a separate HTML file. Report links use hash routes inside `output/index.html`; when a report is selected, the page calls `fetch()` for the original `.md` file and renders it in the reader pane. The direct-source links still point to the original Markdown files.

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
