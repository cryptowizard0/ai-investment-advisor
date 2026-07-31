# InvestFlow

[中文文档](README.zh-CN.md)

InvestFlow is a repo-local agent plugin for investment research, compatible with both Codex and Claude Code. It bundles reusable skills for market scans, industry-chain research, single-stock analysis, earnings review, reflexivity analysis, and routed market data.

Its flagship workflow is **chain-alpha** — a theme → industry-chain → investable-company funnel with ongoing revenue/profit-delivery tracking. See [Featured Workflow: chain-alpha](#featured-workflow-chain-alpha).

At a glance, the skills fall into three user-facing categories, grouped by purpose (plus a supporting infrastructure layer):

| Category | Input | Start with | For |
|---|---|---|---|
| **1. Find opportunities** | a theme | `chain-alpha` | Turn a big theme into investable companies |
| **2. Research a single stock** | a ticker | `research-stock` | Judge one company from several independent angles |
| **3. Monitor recurring state** | a calendar or index | choose the matching `monitor-*` skill | Run scheduled checks and event-triggered updates |

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
Use InvestFlow to map the HBM supply chain with chain-alpha.
```

If the plugin does not appear, confirm these files exist:

- Codex: `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`
- Claude Code: `plugins/invest-flow/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`

## Featured Workflow: chain-alpha

chain-alpha is InvestFlow's flagship workflow: it turns a big theme into investable companies, defines the entry plan, then keeps tracking whether revenue and profit growth actually deliver. Six skills form a closed loop, orchestrated end-to-end by `chain-alpha`:

```text
theme ─▶ chain-alpha-mismatch ─▶ chain-alpha-monopoly ─▶ chain-alpha-verification ─▶ chain-alpha-entry-plan ⇄ monitor-chain-alpha-delivery
        industry + growth        sub-links +           4-tier grade               entry decision +         quarterly revenue/
        screen + mismatch        ≤10 candidates        (grading only)             staged buying plan       profit tracking
        └──────────────────── orchestrated by chain-alpha ────────────────────┘
```

Run the whole funnel in one command:

```text
Use invest-flow:chain-alpha to find investable companies in humanoid robots.
```

Funnel discipline: industry definition and growth gate → 2-4 mismatch links → ≤10 candidates per link → top-6 into verification → pass-and-above into step-4 position sizing → 2-3 deep dives. Industry/key-link revenue growth must be >20%, have a clear driver, and last at least 6 months before the workflow enters later steps; industry and company screens must still map back to sustainable profit growth: ≥30% is preferred, 20% is the minimum gate, and <20% is screened out. Step 3 `chain-alpha-verification` only grades; positions come exclusively from step 4 `chain-alpha-entry-plan` (position cap = drawdown budget / potential risk, with grade/elastic discounts). Names left at `pending-verification` are then tracked quarterly with `monitor-chain-alpha-delivery`, whose grade changes feed back into `chain-alpha-verification` and re-trigger step-4 sizing on upgrades. Each step can also run standalone — start with `chain-alpha-mismatch` to define the industry, screen growth, and confirm mismatch links cheaply before committing to the full run.

## Skills By Category

InvestFlow's skills group into three user-facing categories by purpose: Chain Alpha, Research, and Monitor, plus a supporting infrastructure layer.

### 1. Find opportunities (you bring a theme)

Turn a big theme into investable companies. `chain-alpha` is the flagship — see [Featured Workflow: chain-alpha](#featured-workflow-chain-alpha).

| Skill | Purpose | Use when |
|---|---|---|
| `chain-alpha` | Orchestrates the four canonical chain-alpha steps (`chain-alpha-mismatch` → `chain-alpha-monopoly` → `chain-alpha-verification` → `chain-alpha-entry-plan`) with in-step subagent fan-out (Claude Code parallel; Codex parallel when explicitly requested and available; otherwise serial fallback) and funnel discipline. | You want the full theme-to-company-to-entry-plan workflow in one run. |
| `chain-alpha-mismatch` | Plain-language industry definition, growth hard gate with industry-cycle staging (four-stage timeline + current-stage marker), full industry-chain panorama, and supply-demand mismatch link discovery with a profit-growth gate. | You have a big theme and need to understand what the industry actually is, which cycle stage it is in, why growth can stay high, the whole chain, and the links where demand outruns supply and can translate into profit growth. |
| `chain-alpha-monopoly` | Sub-link breakdown and monopoly screening with CR3, margin, revenue-share, and profit-growth gates. | You confirmed a mismatch link and need the <=10 strongest companies in it. |
| `chain-alpha-verification` | 100-point four-tier company verification with profit-growth gating (grading only, no position sizing). | You have candidates and need a gold-pool/pass/pending/reject grade; pass-and-above names hand off to step 4 for sizing. |
| `chain-alpha-entry-plan` | chain-alpha step 4: type gate → PE/PS ruler (with alert lines) → 5-year TTM percentile band → potential risk → growth-digestion check → entry decision, position cap, entry range, staged buying plan, and blocking/reopen conditions. | Verification produced a grade and you need an executable entry plan. (Also listed under category 2.) |

### 2. Research a single stock (you bring a ticker)

Judge one company from several independent angles. `research-stock` orchestrates the rest in one session.

| Skill | Purpose | Use when |
|---|---|---|
| `research-stock` | In-session orchestration across the five default single-stock stages (profile → fundamentals → institutional → reflexivity → Reportify). | You want one stock analyzed from several independent angles. |
| `research-profile` | Builds a company primer before investment analysis. | A user is hearing about a company for the first time and needs business, technology, value-chain, AI relevance, competitors, and industry-position context. |
| `research-fundamentals` | Single-stock fundamental, valuation, and technical analysis. | You need a fast but structured view of a company. |
| `research-institutional` | Institutional accumulation and distribution analysis. | You want to judge whether major players are buying, distributing, or hedging. |
| `research-reflexivity` | Soros-style reflexivity analysis with quick (5-minute stage check) and deep (full-cycle) modes. | You need to read where a narrative sits — a fast stage check, or a full narrative/price/reality/reversal map. |
| `research-reportify` | Standardized 8-part stock report with a buy-side-grade decision layer (3-scenario valuation, falsifiable thesis, catalysts, tracking dashboard). | You need a repeatable, formal, trackable report covering facts, interpretation, decision, and risk. |
| `research-earnings` | Institutional earnings, guidance, call, and expectation-gap analysis; it is not one of the five default `research-stock` stages. | The user specifies a reporting period or a relevant new earnings event occurs. |

### 3. Daily & periodic tracking (you bring a calendar)

Recurring reads that work well as scheduled tasks.

| Skill | Fixed cadence | Supplemental triggers | Purpose |
|---|---|---|---|
| `monitor-us-market` | After every completed US trading session | Major after-hours events | Conclusion-first Chinese US market close report with a hard length budget, dynamic sector/theme ranking, and a new-dynamics radar. |
| `monitor-ai-infrastructure` | Weekly | Material hyperscaler capex, architecture, order, or capacity changes | AI infrastructure sector scan whose handoff queue feeds `chain-alpha-mismatch` or `chain-alpha`. |
| `monitor-index-cycle` | Lightweight check after each trading day | State change or scheduled review triggers a full report | Maintain index bull/bear cycle state using close-to-close reversal thresholds and stable reports. |
| `monitor-index-valuation` | Monthly | Index move of at least ±5%, constituent changes, or material earnings-caliber changes | Index valuation price-sensitivity table with single-caliber guardrails and cyclical-earnings distortion checks. |
| `monitor-gold` | Weekly | FOMC, CPI, real-rate, geopolitical, or abnormal-price events | Gold trend, bubble-risk, and macro-driver analysis. |
| `monitor-chain-alpha-delivery` | After quarterly earnings | Material order, capacity, customer, guidance, or competitive-structure changes | Revenue/profit-delivery tracking that feeds grade changes back into Chain Alpha and can retrigger `chain-alpha-entry-plan`. |

### Infrastructure (supporting layer, no investment view of its own)

| Skill | Purpose | Use when |
|---|---|---|
| `market-data-router` | Routed market-data fetching and fallback logic. | Another workflow needs bars, quote data, options context, or cached market data. |
| `output-report-index` | Markdown and static HTML index pages for generated reports. | You explicitly ask to generate or update the report index under `output/`. |

## Use Skills In Agent

Use InvestFlow through natural-language prompts in Codex or Claude Code. Prefer skill names when you want a specific workflow:

```text
Use invest-flow:research-stock to analyze TSLA.
Use invest-flow:monitor-us-market to scan today's US market close.
Use invest-flow:chain-alpha to find investable companies in AI data center power.
Use invest-flow:research-reflexivity in quick mode to check NVIDIA's current narrative stage.
Use invest-flow:monitor-index-valuation to build a valuation-sensitivity table for the STAR 50 index.
Use invest-flow:monitor-index-cycle to update the SOX bull and bear market cycle tables.
Use invest-flow:chain-alpha-entry-plan to create NVDA's entry decision, position cap, entry range, and staged buying plan.
Use invest-flow:research-earnings to analyze NVIDIA's latest earnings.
Use invest-flow:output-report-index to update the output report index.
```

For provider-backed market data, create a local `.env` from `.env_example` and add the relevant API keys.

## Local Report Reader

The primary local reader lives under `web/`. It scans Markdown reports in `output/{chain-alpha,monitor,research}/`, exposes report metadata and raw Markdown through FastAPI, and renders the selected report in a light React two-pane interface.

Start the complete reader with one command:

```bash
./web/run.sh
```

Then open `http://127.0.0.1:8000/`. The launcher ensures the `.venv` backend dependencies are present, installs locked frontend packages when needed, rebuilds a missing or stale Vite bundle, and binds uvicorn only to `127.0.0.1`.

## Output Paths

Generated reports and cache files are written under `output/`:

| Workflow | Output path |
|---|---|
| Chain Alpha series | `output/chain-alpha/` |
| Research series | `output/research/` |
| Monitor series | `output/monitor/` |
| Report index | `output/index.md`, `output/index.html` |
| Market data cache | `output/cache/market-data/` |

The output root is limited to these three topic directories, `cache/`, and the two root index files.

Within each series folder, report files are distinguished by skill prefixes (e.g. `chain-alpha-mismatch-...`, `research-fundamentals-...`, `monitor-us-market-...`, etc.). Normal duplicate handling still applies using `(1)`, `(2)` suffixes.

Report generators normally avoid overwriting and append suffixes such as `(1)` and `(2)` when needed. Index bull/bear cycle documents are the exception: their stable filenames are updated in place so each index has one current bull table and one current bear table.

The generated HTML reader remains available as a legacy fallback through the UTF-8 report server:

```bash
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000
# then open http://127.0.0.1:8000/output/index.html
```

## Legacy Report Index Reader

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
- When plugin packaging changes, update both manifests and both marketplace entries together, and keep all four versions in sync.
- Keep README skill names aligned with the directories under `plugins/invest-flow/skills/`.
