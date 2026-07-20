# Agent Guidelines

## Project Overview

This repository is an AI-driven investment analysis system packaged as a repo-local plugin compatible with both Codex and Claude Code. The canonical runtime surface is `plugins/invest-flow/`, which contains the plugin manifests, assets, and all investment skills. The skills directory is shared by both platforms; only the manifest/marketplace wrappers differ.

**Project Language**: Documentation and investment reports are primarily in Chinese (中文). Code comments are in English. Financial terms remain in English (RSI, MACD, P/E, OBV, etc.).

## Technology Stack

- **Python**: 3.12.10 (virtual environment at `.venv/`)
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
│           ├── ai-infrastructure-sector-discovery/
│           ├── chain-alpha-mismatch-discovery/
│           ├── chain-alpha-monopoly-screen/
│           ├── chain-alpha-verification/
│           ├── chain-alpha-pipeline/
│           ├── chain-alpha-delivery-tracking/
│           ├── company-profile/
│           ├── company-valuation-risk/
│           ├── fundamental-analysis/
│           ├── earnings-report-analysis/
│           ├── institutional-accumulation-analysis/
│           ├── index-pe-sensitivity/
│           ├── non-consensus-company-discovery/
│           ├── gold-trend-analysis/
│           ├── reflexivity-analysis/
│           ├── reportify-stock-analysis/
│           ├── daily-us-market-scan/
│           ├── multi-agent-stock-analysis/
│           ├── output-report-index/
│           └── market-data-router/
├── output/
│   ├── chain-alpha-mismatch-discovery/
│   ├── chain-alpha-monopoly-screen/
│   ├── chain-alpha-verification/
│   ├── chain-alpha-pipeline/
│   ├── chain-alpha-delivery-tracking/
│   ├── company-profile/
│   ├── company-valuation-risk/
│   ├── fundamental-analysis/
│   ├── earnings-report-analysis/
│   ├── ai-infrastructure-sector-discovery/
│   ├── index-pe-sensitivity/
│   ├── institutional-accumulation-analysis/
│   ├── non-consensus-company-discovery/
│   ├── gold-analysis/
│   ├── reflexivity-analysis/
│   ├── reportify-stock-analysis/
│   ├── daily-us-market-scan/
│   ├── summary/
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
- `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py` - multi-agent orchestration entrypoint
- `plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py` - market data router entrypoint
- `plugins/invest-flow/skills/earnings-report-analysis/scripts/generate_report.py` - earnings report analysis skeleton generator
- `plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py` - non-consensus discovery report skeleton generator
- `plugins/invest-flow/skills/index-pe-sensitivity/scripts/generate_report.py` - index valuation price-sensitivity table generator
- `plugins/invest-flow/skills/company-valuation-risk/scripts/generate_report.py` - company valuation percentile-band and risk report generator
- `plugins/invest-flow/skills/output-report-index/scripts/generate_index.py` - output report index generator
- `plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py` - UTF-8 local report static server

## Build/Test Commands

This project uses lightweight `unittest` coverage for packaged helper scripts. Broader validation is still done through direct script execution and real analysis tasks.

```bash
# Activate virtual environment
source .venv/bin/activate

# Check orchestrator CLI
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py --help

# Check market data router CLI
python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --help

# Run helper script tests
python -m unittest \
  plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/tests/test_investflow_pipeline.py \
  plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/index-pe-sensitivity/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/company-valuation-risk/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py

# Generate a multi-agent prompt plan
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company "Tesla"

# Generate a non-consensus company discovery report skeleton
python plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py --theme "AI 数据中心电力"

# Generate an earnings report analysis skeleton
python plugins/invest-flow/skills/earnings-report-analysis/scripts/generate_report.py --ticker NVDA --company "NVIDIA" --period "FY2026 Q1"

# Generate an index valuation price-sensitivity report
python plugins/invest-flow/skills/index-pe-sensitivity/scripts/generate_report.py --index 科创50 --code 000688 --base 232.5 --anchors "36.31:0,83.91:50,159.29:80,232.51:98.07,263.72:100" --current-percentile 98.07

# Generate a company valuation percentile-band risk report
python plugins/invest-flow/skills/company-valuation-risk/scripts/generate_report.py NVDA --company "NVIDIA" --company-type 成长 --pe-file pe_5y.csv --current-price 181.40 --max-loss-streak 0 --ref-pe 35.4 --grade 通过 --drawdown-budget 2

# Generate or update the Markdown and HTML output report indexes
python plugins/invest-flow/skills/output-report-index/scripts/generate_index.py

# Serve output reports with UTF-8 Markdown/HTML headers
python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000
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

- `ai-infrastructure-sector-discovery` - weekly AI infrastructure sector discovery and scoring, designed to run as a scheduled weekly tracking task; sectors scoring >=70 hand off to chain-alpha (`chain-alpha-mismatch-discovery` or `chain-alpha-pipeline`)
- `company-profile` - company primer covering overview, core business, technology barriers, industry-chain position, AI relevance, competitors, and industry position
- `company-valuation-risk` - chain-alpha step 4 (after verification) and standalone valuation tool: company-type gate (growth/cash-cow/toll-station analyzable; cyclical/pulse/distressed excluded), PE-vs-PS ruler selection via four PE-distortion conditions plus an alert-line prominent warning (current TTM PE >100x or TTM PS >40x -> prominent warning, flow continues with all readouts at reduced confidence) and an insufficient-history prominent warning (<5y span), 5-year TTM PE/PS percentile band vs the company's own history (current percentile + 10/20/25/50/60/75/80/90/95 key percentiles), potential risk taken as the worse of two drawdowns (reversion to the 50th percentile vs reversion to the bear-low reference-point multiple, default 2026-03-31; current below reference is prominently flagged) under a static TTM denominator, and the position plan that is chain-alpha's single position outlet: position cap = drawdown budget (max account-level drawdown one name may inflict) / potential risk, tabulated across a fixed budget ladder (2/5/10/20/30/50/70%; --drawdown-budget picks the highlighted primary rung, default 2%), with stacking discounts (gold-pool full / pass x0.5 / pending & reject no position, elastic x0.5, short-history x0.5) and a triggered alert line zeroing new entries; delivery-tracking's engine C reuses its percentile band
- `chain-alpha-mismatch-discovery` - chain-alpha step 1: industry definition with a plain-language explainer (what it is, what it replaces, why now), growth hard gate (industry/key-link revenue growth >20%, clear driver, >=6 month duration) plus per-driver analysis of why growth stays high, a four-stage industry-cycle timeline (tech validation -> early commercialization -> volume ramp -> mass adoption) with a current-stage marker, full industry-chain panorama list, plus supply-demand mismatch link discovery with hard evidence gates, a profit-growth gate (preferred >=30%, minimum 20%), 30-point mismatch scoring including a reverse-scored pricing-in dimension, and a supply-response clock that reads expansion evidence both ways
- `chain-alpha-monopoly-screen` - chain-alpha step 2: sub-link breakdown, global landscape including mainland China and JP/KR/TW/EU, CR3/margin/revenue-share/profit-growth hard gates, 30-point candidate scoring
- `chain-alpha-verification` - chain-alpha step 3: dual-track revenue-share gate plus profit-growth hard gate and 100-point four-tier grading (gold pool/pass/pending/reject) for global main-board candidates; grading only — no position sizing, pass-and-above names hand off (grade + elastic flag) to `company-valuation-risk` step 4
- `chain-alpha-pipeline` - chain-alpha orchestration: main agent runs the four steps serially (mismatch-discovery -> monopoly-screen -> verification grading -> company-valuation-risk pricing and position sizing) with in-step subagent fan-out (parallel on Claude Code; parallel on Codex when explicitly requested and available; otherwise serial fallback), enforces funnel discipline (2-4 links, <=10 candidates per link, pass-and-above into step 4, 2-3 deep dives), and writes a Chinese summary report
- `chain-alpha-delivery-tracking` - chain-alpha follow-on: forward-looking revenue/profit-delivery tracking for 待验证 candidates via a 5-gate validation ladder (order->capacity->ramp->revenue->profit) with per-gate delivery windows and timeout downgrades, growth/attribution/dynamic-valuation (PE&PS dual-track) engines, structure sentinels (competitor capacity, second-sourcing, customer in-housing, demand-side capex), and symmetric grade up/down that feeds grades back into chain-alpha and re-triggers step-4 (company-valuation-risk) position sizing on upgrades
- `fundamental-analysis` - stock fundamental and technical analysis
- `earnings-report-analysis` - institutional earnings report, guidance, call, and expectation-gap analysis
- `institutional-accumulation-analysis` - whale accumulation/distribution analysis
- `index-pe-sensitivity` - index valuation price-sensitivity table: ±price move -> TTM P/E (整体法 aggregate caliber) -> N-year percentile, with single-caliber consistency guardrails and cyclical-earnings distortion checks
- `non-consensus-company-discovery` - theme-to-company discovery for high-potential non-consensus opportunities
- `gold-trend-analysis` - gold bubble risk and macro signal analysis
- `reflexivity-analysis` - Soros-style reflexivity analysis with quick (5-minute stage check) and deep (full-cycle) modes
- `reportify-stock-analysis` - fixed-template structured stock research report with a buy-side-grade decision layer (3-scenario valuation, falsifiable thesis, catalysts, tracking dashboard)
- `daily-us-market-scan` - Chinese daily US market close scan with a conclusion-first summary card, hard length budget (<=300 lines), dynamic sector/theme ranking from same-day moves, threshold-based watchlist reporting, and a required new-dynamics radar for emerging themes outside the fixed pool
- `multi-agent-stock-analysis` - orchestration across multiple analysis skills
- `output-report-index` - explicit Markdown and HTML report index generator for `output/index.md` and `output/index.html`
- `market-data-router` - routed market data fetch and fallback logic

## Orchestrator Notes

`multi-agent-stock-analysis` is implemented by the packaged orchestrator script, not by separate legacy agent-definition files. The current orchestrator:

- resolves the repo root dynamically
- generates six skill prompts for the basic stock-analysis workflow: company profile, fundamental, institutional, reflexivity (deep mode), reportify, and non-consensus
- writes a prompt plan Markdown file and orchestration JSON
- does not execute child skills or launch another agent process
- supports summary composition from already completed handoff data

Recommended live usage is to say `使用 invest-flow:multi-agent-stock-analysis 分析 MRVL` in Codex or Claude Code. The agent then executes the child skill prompts in the current session and writes the final Chinese report.

## Output Conventions

- Fundamental analysis: `output/fundamental-analysis/{ticker}-{company-name}-{date}.md`
- Earnings report analysis: `output/earnings-report-analysis/earnings-report-analysis-{TICKER}-{period}-{YYYY-MM-DD}.md`
- AI infrastructure sector discovery: `output/ai-infrastructure-sector-discovery/ai-infrastructure-sector-discovery-{YYYY-MM-DD}.md`
- Chain-alpha mismatch discovery: `output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-{主题}-{YYYY-MM-DD}.md`
- Chain-alpha monopoly screen: `output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节}-{YYYY-MM-DD}.md`
- Chain-alpha verification: `output/chain-alpha-verification/chain-alpha-verification-{TICKER或环节}-{YYYY-MM-DD}.md`
- Chain-alpha pipeline summary: `output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`
- Chain-alpha delivery tracking: `output/chain-alpha-delivery-tracking/chain-alpha-delivery-tracking-{TICKER}-{YYYY-MM-DD}.md`
- Company profile: `output/company-profile/company-profile-{TICKER}-{YYYY-MM-DD}.md`
- Company valuation risk: `output/company-valuation-risk/company-valuation-risk-{TICKER}-{YYYY-MM-DD}.md`
- Index PE sensitivity: `output/index-pe-sensitivity/index-pe-sensitivity-{index}-{YYYY-MM-DD}.md`
- Institutional analysis: `output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md`
- Non-consensus company discovery: `output/non-consensus-company-discovery/non-consensus-company-discovery-{theme}-{YYYY-MM-DD}.md`
- Gold analysis: `output/gold-analysis/gold-{analysis-type}-{date}.md`
- Reflexivity analysis: `output/reflexivity-analysis/`
- Reportify stock analysis: `output/reportify-stock-analysis/reportify-stock-analysis-{TICKER}-{YYYY-MM-DD}.md`
- Daily US market scan: `output/daily-us-market-scan/us-market-close-daily-{YYYY-MM-DD}.md`
- Summary report: `output/summary/综合分析-{TICKER}-{date}.md`
- Report index: `output/index.md` and `output/index.html`
- Market data cache: `output/cache/market-data/`

Open the HTML report reader through the UTF-8 report server, for example `python plugins/invest-flow/skills/output-report-index/scripts/serve_reports.py --port 8000` from the repo root and then `http://127.0.0.1:8000/output/index.html`, so the page can fetch Markdown reports on demand and direct `.md` links render Chinese correctly.

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

## Maintenance Guidance

- When updating investment workflows, edit the packaged plugin content directly under `plugins/invest-flow/`.
- Keep `README.md` and this file aligned with the actual on-disk structure.
- If plugin packaging changes, update all four metadata files together and keep versions in sync: `plugins/invest-flow/.codex-plugin/plugin.json`, `plugins/invest-flow/.claude-plugin/plugin.json`, `.agents/plugins/marketplace.json`, and `.claude-plugin/marketplace.json`.
- Keep skill wording platform-neutral (say "agent 会话" or mention both Codex and Claude Code) so the same SKILL.md works on both platforms.
