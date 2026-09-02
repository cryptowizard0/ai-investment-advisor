# Agent Guidelines

## Project Overview

This repository is an AI-driven investment analysis system packaged as a repo-local plugin compatible with both Codex and Claude Code. The canonical runtime surface is `plugins/invest-flow/`, which contains the plugin manifests, assets, and all investment skills. The skills directory is shared by both platforms; only the manifest/marketplace wrappers differ.

**Project Language**: Documentation and investment reports are primarily in Chinese (中文). Code comments are in English. Financial terms remain in English (RSI, MACD, P/E, OBV, etc.).

## Technology Stack

- **Python**: 3.12.10 (virtual environment at `.venv/`)
- **Web reader**: FastAPI + uvicorn backend, React + Vite + TypeScript frontend
- **Agent runtimes**: Codex and Claude Code
- **Key Python Libraries**:
  - `yfinance`
  - `pandas`
  - `requests`
  - `PyYAML`

## Current Repository Structure

```text
.
├── AGENTS.md
├── CLAUDE.md            # imports AGENTS.md for Claude Code
├── README.md
├── .agents/
│   └── plugins/
│       └── marketplace.json        # Codex local marketplace
├── .claude-plugin/
│   └── marketplace.json            # Claude Code local marketplace
├── plugins/
│   └── invest-flow/
│       ├── .codex-plugin/plugin.json    # Codex manifest
│       ├── .claude-plugin/plugin.json   # Claude Code manifest
│       ├── assets/
│       └── skills/
│           ├── monitor-ai-infrastructure/
│           ├── chain-alpha-industry-analysis/
│           ├── chain-alpha-company-discovery/
│           ├── chain-alpha-company-verification/
│           ├── chain-alpha/
│           ├── monitor-chain-alpha-delivery/
│           ├── research-profile/
│           ├── chain-alpha-position-plan/
│           ├── research-fundamentals/
│           ├── research-earnings/
│           ├── research-institutional/
│           ├── monitor-index-valuation/
│           ├── monitor-index-cycle/
│           ├── monitor-nhnl-bottom/
│           ├── monitor-gold/
│           ├── research-reflexivity/
│           ├── research-reportify/
│           ├── monitor-us-market/
│           ├── research-stock/
│           ├── output-report-index/
│           └── market-data-router/
├── web/
│   ├── backend/                    # FastAPI report metadata/raw API
│   ├── frontend/                   # React/Vite report reader
│   └── run.sh                      # local one-command launcher
├── output/
│   ├── chain-alpha/
│   ├── research/
│   ├── monitor/
│   ├── index.md
│   ├── index.html
│   └── cache/market-data/
└── .venv/
```

## Source Of Truth

- Investment skills live only in `plugins/invest-flow/skills/`. Both Codex and Claude Code load the same skill files.
- Codex plugin discovery metadata lives in `.agents/plugins/marketplace.json`.
- Claude Code plugin discovery metadata lives in `.claude-plugin/marketplace.json`.
- Do not reintroduce duplicate investment skills under `.agents/skills/`, `.claude/skills/`, or legacy agent-definition folders.

## Key Files

- `plugins/invest-flow/.codex-plugin/plugin.json` - Codex plugin manifest
- `plugins/invest-flow/.claude-plugin/plugin.json` - Claude Code plugin manifest
- `.agents/plugins/marketplace.json` - repo-local Codex marketplace entry
- `.claude-plugin/marketplace.json` - repo-local Claude Code marketplace entry
- `CLAUDE.md` - Claude Code memory entry that imports this file via `@AGENTS.md`
- `plugins/invest-flow/skills/research-stock/scripts/orchestrator.py` - multi-agent orchestration entrypoint
- `plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py` - market data router entrypoint
- `plugins/invest-flow/skills/research-earnings/scripts/generate_report.py` - earnings report analysis skeleton generator
- `plugins/invest-flow/skills/monitor-index-valuation/scripts/generate_report.py` - index valuation price-sensitivity table generator
- `plugins/invest-flow/skills/monitor-index-cycle/scripts/calculate_cycles.py` - close-to-close threshold cycle detector for index bull/bear tables
- `plugins/invest-flow/skills/monitor-nhnl-bottom/scripts/build_nhnl.py` - Elder NH-NL breadth state machine (capitulation/divergence/bull-confirm) calculator
- `plugins/invest-flow/skills/chain-alpha-position-plan/scripts/generate_report.py` - Chain Alpha entry-plan report generator
- `plugins/invest-flow/skills/output-report-index/scripts/generate_index.py` - output report index generator
- `plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py` - UTF-8 local report static server
- `web/backend/app.py` - local report-list/raw Markdown API and built frontend host
- `web/run.sh` - dependency check, stale frontend build, and localhost uvicorn launcher

## Build/Test Commands

This project uses lightweight `unittest` coverage for packaged helper scripts. Broader validation is still done through direct script execution and real analysis tasks.

```bash
# Activate virtual environment
source .venv/bin/activate

# Check orchestrator CLI
python plugins/invest-flow/skills/research-stock/scripts/orchestrator.py --help

# Check market data router CLI
python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --help

# Run helper script tests
python -m unittest \
  plugins/invest-flow/skills/research-stock/scripts/tests/test_investflow_pipeline.py \
  plugins/invest-flow/skills/monitor-us-market/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/monitor-index-valuation/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/monitor-index-cycle/scripts/tests/test_calculate_cycles.py \
  plugins/invest-flow/skills/monitor-nhnl-bottom/scripts/tests/test_build_nhnl.py \
  plugins/invest-flow/skills/chain-alpha-position-plan/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py

# Generate a multi-agent prompt plan
python plugins/invest-flow/skills/research-stock/scripts/orchestrator.py TSLA --company "Tesla"

# Generate an earnings report analysis skeleton
python plugins/invest-flow/skills/research-earnings/scripts/generate_report.py --ticker NVDA --company "NVIDIA" --period "FY2026 Q1"

# Generate an index valuation price-sensitivity report
python plugins/invest-flow/skills/monitor-index-valuation/scripts/generate_report.py --index 科创50 --code 000688 --base 232.5 --anchors "36.31:0,83.91:50,159.29:80,232.51:98.07,263.72:100" --current-percentile 98.07

# Detect bull/bear cycles from an index EOD close CSV
python plugins/invest-flow/skills/monitor-index-cycle/scripts/calculate_cycles.py --prices-file prices.csv --seed-kind auto --format markdown

# Read the NH-NL breadth state machine for the SOX universe
python plugins/invest-flow/skills/monitor-nhnl-bottom/scripts/build_nhnl.py --preset sox --format markdown

# Generate a Chain Alpha entry-plan report
python plugins/invest-flow/skills/chain-alpha-position-plan/scripts/generate_report.py NVDA --company "NVIDIA" --company-type 成长 --pe-file pe_5y.csv --current-price 181.40 --max-loss-streak 0 --ref-pe 35.4 --grade 通过 --drawdown-budget 2

# Generate or update the Markdown and HTML output report indexes
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py

# Serve output reports with UTF-8 Markdown/HTML headers
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000

# Run the local FastAPI + React report reader
./web/run.sh

# Run the report reader API contract tests
python -m unittest web/backend/tests/test_app.py
```

## Skill Layout

Each packaged skill follows this structure:

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

Active packaged skills:

- `monitor-ai-infrastructure` - weekly AI infrastructure sector discovery and scoring, designed to run as a scheduled weekly tracking task; sectors scoring >=70 hand off to chain-alpha (`chain-alpha-industry-analysis` or `chain-alpha`)
- `research-profile` - company primer covering overview, core business, technology barriers, industry-chain position, AI relevance, competitors, and industry position
- `chain-alpha-position-plan` - chain-alpha step 4 (after verification) and standalone entry-planning tool: company-type gate (growth/cash-cow/toll-station analyzable; cyclical/pulse/distressed excluded), PE-vs-PS ruler selection via four PE-distortion conditions plus an alert-line prominent warning (current TTM PE >100x or TTM PS >40x -> prominent warning, flow continues with all readouts at reduced confidence) and an insufficient-history prominent warning (<5y span), 5-year TTM PE/PS percentile band vs the company's own history (current percentile + 10/20/25/50/60/75/80/90/95 key percentiles), potential risk taken as the worse of two drawdowns (reversion to the 50th percentile vs reversion to the bear-low reference-point multiple, default 2026-03-31; current below reference is prominently flagged) under a static TTM denominator, a growth-digestion signal check against a growth-model fair TTM PE (exit multiple x (1+g)^(N+1) / (1+r)^N, default r=10% and 15x exit; digestion time = ln(current/fair)/ln(1+r) capped by the growth duration; verdicts fair-or-cheap / digestible <=1y / partial 1-2y / overpriced, fed by verification's numeric growth handoff of g with evidence tier, duration N, and revenue growth), a mandatory industry-and-company context note in the conclusion (high percentile in a booming industry/company is not a sell signal, low percentile under industry-level fear is not a buy signal; qualitative only, never alters computed results), and chain-alpha's single entry outlet: entry decision, position cap, entry range, staged buying plan, and blocking/reopen conditions. Position cap = drawdown budget (max account-level drawdown one name may inflict) / potential risk, tabulated across a fixed budget ladder (2/5/10/20/30/50/70%; --drawdown-budget picks the highlighted primary rung, default 2%), with stacking structural discounts (gold-pool full / pass x0.5 / pending & reject no position, elastic x0.5, short-history x0.5) plus two signal-layer factors (always <=1, only tighten or unlock, never amplify): a triggered alert line zeroes new entries unless released to x0.5 (--alert-release, validated and rejected unless --alert-release-evidence names tier-1 forward evidence — guidance + orders/capacity lock or delivery-tracking L4 lit — and a forward multiple --forward-pe/--forward-ps is proven back inside the line), and a 透支 digestion verdict (--digestion) adds x0.5; delivery-tracking's engine C reuses its percentile band
- `chain-alpha-industry-analysis` - chain-alpha step 1: industry definition with a plain-language explainer (what it is, what it replaces, why now), growth hard gate (industry/key-link revenue growth >20%, clear driver, >=6 month duration) plus per-driver analysis of why growth stays high, a four-stage industry-cycle timeline (tech validation -> early commercialization -> volume ramp -> mass adoption) with a current-stage marker, full industry-chain panorama list, plus supply-demand mismatch link discovery with hard evidence gates, a profit-growth gate (preferred >=30%, minimum 20%), 30-point mismatch scoring including a reverse-scored pricing-in dimension, and a supply-response clock that reads expansion evidence both ways
- `chain-alpha-company-discovery` - chain-alpha step 2: sub-link breakdown, global landscape including mainland China and JP/KR/TW/EU, CR3/margin/revenue-share/profit-growth hard gates, 30-point candidate scoring
- `chain-alpha-company-verification` - chain-alpha step 3: dual-track revenue-share gate plus profit-growth hard gate and 100-point four-tier grading (gold pool/pass/pending/reject) for global main-board candidates; grading only — no position sizing, pass-and-above names hand off (grade + elastic flag) to `chain-alpha-position-plan` step 4
- `chain-alpha` - chain-alpha orchestration: main agent runs the four canonical steps serially (`chain-alpha-industry-analysis` -> `chain-alpha-company-discovery` -> `chain-alpha-company-verification` -> `chain-alpha-position-plan`) with in-step subagent fan-out (parallel on Claude Code; parallel on Codex when explicitly requested and available; otherwise serial fallback), enforces funnel discipline (2-4 links, <=10 candidates per link, pass-and-above into step 4, 2-3 deep dives), and writes a Chinese summary report
- `monitor-chain-alpha-delivery` - chain-alpha follow-on: forward-looking revenue/profit-delivery tracking for 待验证 candidates via a 5-gate validation ladder (order->capacity->ramp->revenue->profit) with per-gate delivery windows and timeout downgrades, growth/attribution/dynamic-valuation (PE&PS dual-track) engines, structure sentinels (competitor capacity, second-sourcing, customer in-housing, demand-side capex), and symmetric grade up/down that feeds grades back into chain-alpha and re-triggers step-4 (chain-alpha-position-plan) position sizing on upgrades
- `research-fundamentals` - stock fundamental and technical analysis
- `research-earnings` - institutional earnings report, guidance, call, and expectation-gap analysis
- `research-institutional` - whale accumulation/distribution analysis
- `monitor-index-valuation` - index valuation price-sensitivity table: ±price move -> TTM P/E (整体法 aggregate caliber) -> N-year percentile, with single-caliber consistency guardrails and cyclical-earnings distortion checks
- `monitor-index-cycle` - create and update stable per-index bull/bear cycle tables from EOD closes using close-to-close reversal thresholds, with turning-point P/E, evidence-backed causes, explicit data cutoffs, and current-cycle handling
- `monitor-nhnl-bottom` - Elder-style NH-NL breadth state machine (Sell & Sell Short ch.10) over an index/sector universe: 250-day new-high/new-low counts, universe-size-rescaled capitulation (-0.571) / floor (-0.857) / bull-confirmation (+0.357) ratio thresholds, S1-S4 major-bottom checklist (capitulation spike -> zero recross -> valid bullish divergence -> low-volume retest), P0-P6+PX state classification with two-sided trigger playbooks, plus index-level Impulse/value-zone/false-breakout reads; ships a SOX 30-member preset and offline price-file mode
- `monitor-gold` - gold bubble risk and macro signal analysis
- `research-reflexivity` - Soros-style reflexivity analysis with quick (5-minute stage check) and deep (full-cycle) modes
- `research-reportify` - fixed-template structured stock research report with a buy-side-grade decision layer (3-scenario valuation, falsifiable thesis, catalysts, tracking dashboard)
- `monitor-us-market` - Chinese daily US market close scan with a conclusion-first summary card, hard length budget (<=300 lines), dynamic sector/theme ranking from same-day moves, threshold-based watchlist reporting, and a required new-dynamics radar for emerging themes outside the fixed pool
- `research-stock` - orchestration across multiple analysis skills
- `output-report-index` - explicit Markdown and HTML report index generator for `output/index.md` and `output/index.html`
- `market-data-router` - routed market data fetch and fallback logic

## Orchestrator Notes

`research-stock` is implemented by the packaged orchestrator script, not by separate legacy agent-definition files. The current orchestrator:

- resolves the repo root dynamically
- generates five skill prompts for the basic stock-analysis workflow: profile, fundamentals, institutional, reflexivity (deep mode), and Reportify
- writes a prompt plan Markdown file and orchestration JSON
- does not execute child skills or launch another agent process
- supports summary composition from already completed handoff data

Recommended live usage is to say `使用 invest-flow:research-stock 分析 MRVL` in Codex or Claude Code. The agent then executes the child skill prompts in the current session and writes the final Chinese report.

## Output Conventions

- Chain Alpha 系列（`chain-alpha-*` 与 `chain-alpha`）：
  - `output/chain-alpha/chain-alpha-{主题}-{YYYY-MM-DD}.md`
  - `output/chain-alpha/chain-alpha-industry-analysis-{主题}-{YYYY-MM-DD}.md`
  - `output/chain-alpha/chain-alpha-company-discovery-{环节}-{YYYY-MM-DD}.md`
  - `output/chain-alpha/chain-alpha-company-verification-{TICKER或环节}-{YYYY-MM-DD}.md`
  - `output/chain-alpha/chain-alpha-position-plan-{TICKER}-{YYYY-MM-DD}.md`
- Research 类（单股研究流程与其子任务）：
  - `output/research/research-stock-{TICKER}-{date}.md`
  - `output/research/research-profile-{TICKER}-{YYYY-MM-DD}.md`
  - `output/research/research-fundamentals-{ticker}-{company-name}-{date}.md`
  - `output/research/research-earnings-{TICKER}-{period}-{YYYY-MM-DD}.md`
  - `output/research/research-institutional-机构操作分析-{YYYYMMDD}-{TICKER}.md`
  - `output/research/research-reflexivity-quick-{ticker}-{date}.md`
  - `output/research/research-reflexivity-deep-{ticker}-{date}.md`
  - `output/research/research-reportify-{TICKER}-{YYYY-MM-DD}.md`
- Monitor 类：
  - `output/monitor/monitor-chain-alpha-delivery-{TICKER}-{YYYY-MM-DD}.md`
  - `output/monitor/monitor-ai-infrastructure-{YYYY-MM-DD}.md`
  - `output/monitor/monitor-index-valuation-{index}-{YYYY-MM-DD}.md`
  - `output/monitor/monitor-index-cycle-bull-{CODE}.md`
  - `output/monitor/monitor-index-cycle-bear-{CODE}.md`（文件名稳定，原地更新）
  - `output/monitor/monitor-nhnl-bottom-{LABEL}-{YYYY-MM-DD}.md`
  - `output/monitor/monitor-gold-{analysis-type}-{date}.md`
  - `output/monitor/monitor-us-market-{YYYY-MM-DD}.md`
- Report index: `output/index.md` and `output/index.html`
- Market data cache: `output/cache/market-data/`

Open the primary local report reader with `./web/run.sh`, then visit `http://127.0.0.1:8000/`. The generated `output/index.html` remains available as a legacy fallback through `python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000`.

If an output file already exists, scripts should append numbered suffixes like `(1)` and `(2)` instead of overwriting.

## Code Style

### Python

- Standard library imports first, then third-party imports
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefer explicit `try/except` with meaningful error messages
- Prefer f-strings for formatting
- Use 4-space indentation

### Skill Authoring

- `SKILL.md` must include YAML frontmatter with `name` and `description`
- Keep detailed methodology in `references/` instead of bloating `SKILL.md`
- Keep helper code in `scripts/`
- Keep templates and assets in `assets/`

## Data Sources

Primary sources used by the packaged skills:

- Yahoo Finance (`yfinance`)
- CFTC COT data
- Web search for current market/news context

Reference cache:

- `output/cache/market-data/`

## Dependencies

Install Python dependencies with:

```bash
source .venv/bin/activate
pip install yfinance pandas requests pyyaml
```

The local report reader installs its backend requirements from `web/backend/requirements.txt` and its locked frontend packages from `web/frontend/package-lock.json` when `./web/run.sh` runs.

## Maintenance Guidance

- When updating investment workflows, edit the packaged plugin content directly under `plugins/invest-flow/`.
- Keep `README.md` and this file aligned with the actual on-disk structure.
- If plugin packaging changes, update all four metadata files together and keep versions in sync: `plugins/invest-flow/.codex-plugin/plugin.json`, `plugins/invest-flow/.claude-plugin/plugin.json`, `.agents/plugins/marketplace.json`, and `.claude-plugin/marketplace.json`.
- Keep skill wording platform-neutral (say "agent 会话" or mention both Codex and Claude Code) so the same SKILL.md works on both platforms.
