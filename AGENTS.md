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
│           ├── ai-infrastructure-scarcity-radar/
│           ├── ai-infrastructure-sector-discovery/
│           ├── chain-alpha-mismatch-discovery/
│           ├── chain-alpha-monopoly-screen/
│           ├── chain-alpha-verification/
│           ├── chain-alpha-pipeline/
│           ├── company-profile/
│           ├── company-buyability-score/
│           ├── fundamental-analysis/
│           ├── earnings-report-analysis/
│           ├── institutional-accumulation-analysis/
│           ├── gie-investment-framework/
│           ├── industry-chain-analysis/
│           ├── index-pe-sensitivity/
│           ├── non-consensus-company-discovery/
│           ├── gold-trend-analysis/
│           ├── reflexivity-quick-scan/
│           ├── reflexivity-deep-analysis/
│           ├── professional-investment-analyst/
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
│   ├── company-profile/
│   ├── company-buyability-score/
│   ├── fundamental-analysis/
│   ├── earnings-report-analysis/
│   ├── ai-infrastructure-sector-discovery/
│   ├── ai-infrastructure-scarcity-radar/
│   ├── industry-chain-analysis/
│   ├── index-pe-sensitivity/
│   ├── institutional-accumulation-analysis/
│   ├── gie-investment-framework/
│   ├── non-consensus-company-discovery/
│   ├── gold-analysis/
│   ├── reflexivity-quick-scan/
│   ├── reflexivity-deep-analysis/
│   ├── professional-investment-analyst/
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
- `plugins/invest-flow/skills/company-buyability-score/scripts/generate_report.py` - buyability score skeleton generator
- `plugins/invest-flow/skills/earnings-report-analysis/scripts/generate_report.py` - earnings report analysis skeleton generator
- `plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py` - non-consensus discovery report skeleton generator
- `plugins/invest-flow/skills/index-pe-sensitivity/scripts/generate_report.py` - index valuation price-sensitivity table generator
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
  plugins/invest-flow/skills/company-buyability-score/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/non-consensus-company-discovery/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/daily-us-market-scan/scripts/tests/test_create_report.py \
  plugins/invest-flow/skills/index-pe-sensitivity/scripts/tests/test_generate_report.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_generate_index.py \
  plugins/invest-flow/skills/output-report-index/scripts/tests/test_serve_reports.py

# Generate a multi-agent prompt plan
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --company "Tesla"

# Generate a non-consensus company discovery report skeleton
python plugins/invest-flow/skills/non-consensus-company-discovery/scripts/generate_report.py --theme "AI 数据中心电力"

# Generate an earnings report analysis skeleton
python plugins/invest-flow/skills/earnings-report-analysis/scripts/generate_report.py --ticker NVDA --company "NVIDIA" --period "FY2026 Q1"

# Generate a company buyability score skeleton
python plugins/invest-flow/skills/company-buyability-score/scripts/generate_report.py --ticker NVDA --company "NVIDIA"

# Generate an index valuation price-sensitivity report
python plugins/invest-flow/skills/index-pe-sensitivity/scripts/generate_report.py --index 科创50 --code 000688 --base 232.5 --anchors "36.31:0,83.91:50,159.29:80,232.51:98.07,263.72:100" --current-percentile 98.07

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

- `ai-infrastructure-sector-discovery` - weekly AI infrastructure sector discovery and scoring
- `ai-infrastructure-scarcity-radar` - AI infrastructure scarcity opportunity and bottleneck analysis
- `company-profile` - company primer covering overview, core business, technology barriers, industry-chain position, AI relevance, competitors, and industry position
- `chain-alpha-mismatch-discovery` - chain-alpha step 1: industry definition with a plain-language explainer (what it is, what it replaces, why now), growth hard gate (industry/key-link revenue growth >20%, clear driver, >=6 month duration) plus per-driver analysis of why growth stays high, a four-stage industry-cycle timeline (tech validation -> early commercialization -> volume ramp -> mass adoption) with a current-stage marker, full industry-chain panorama list, plus supply-demand mismatch link discovery with hard evidence gates, a profit-growth gate (preferred >=30%, minimum 20%), 30-point mismatch scoring including a reverse-scored pricing-in dimension, and a supply-response clock that reads expansion evidence both ways
- `chain-alpha-monopoly-screen` - chain-alpha step 2: sub-link breakdown, global landscape including mainland China and JP/KR/TW/EU, CR3/margin/revenue-share/profit-growth hard gates, 30-point candidate scoring
- `chain-alpha-verification` - chain-alpha step 3: dual-track revenue-share gate plus profit-growth hard gate, 100-point four-tier grading (gold pool/pass/pending/reject), drawdown inference and risk-budget position sizing for global main-board candidates
- `chain-alpha-pipeline` - chain-alpha orchestration: main agent runs the three steps serially with in-step subagent fan-out (parallel on Claude Code; parallel on Codex when explicitly requested and available; otherwise serial fallback), enforces funnel discipline (2-4 links, <=10 candidates per link, 2-3 deep dives), and writes a Chinese summary report
- `chain-alpha-delivery-tracking` - chain-alpha follow-on: forward-looking revenue/profit-delivery tracking for 待验证 candidates via a 5-gate validation ladder (order->capacity->ramp->revenue->profit) with per-gate delivery windows and timeout downgrades, growth/attribution/dynamic-valuation (PE&PS dual-track) engines, structure sentinels (competitor capacity, second-sourcing, customer in-housing, demand-side capex), and symmetric grade up/down that feeds back into chain-alpha
- `company-buyability-score` - quantified buyability score for US-listed equities/ADRs covering AI exposure, value-chain position, growth, drawdown risk, sentiment mismatch, and negative factors
- `fundamental-analysis` - stock fundamental and technical analysis
- `earnings-report-analysis` - institutional earnings report, guidance, call, and expectation-gap analysis
- `institutional-accumulation-analysis` - whale accumulation/distribution analysis
- `gie-investment-framework` - 1-3 year golden-shovel style investment framework
- `industry-chain-analysis` - two-layer industry chain and bottleneck analysis for upstream/midstream/downstream positioning
- `index-pe-sensitivity` - index valuation price-sensitivity table: ±price move -> TTM P/E (整体法 aggregate caliber) -> N-year percentile, with single-caliber consistency guardrails and cyclical-earnings distortion checks
- `non-consensus-company-discovery` - theme-to-company discovery for high-potential non-consensus opportunities
- `gold-trend-analysis` - gold bubble risk and macro signal analysis
- `reflexivity-quick-scan` - fast stage judgment with a Soros-style reflexivity lens
- `reflexivity-deep-analysis` - full-cycle reflexivity research on stocks, sectors, and narratives
- `professional-investment-analyst` - professional investment research system with evidence, valuation, reflexivity, decision, and tracking dashboard
- `reportify-stock-analysis` - fixed-template structured stock research report generation
- `daily-us-market-scan` - Chinese daily US market close scan with a conclusion-first summary card, hard length budget (<=300 lines), dynamic sector/theme ranking from same-day moves, threshold-based watchlist reporting, and a required new-dynamics radar for emerging themes outside the fixed pool
- `multi-agent-stock-analysis` - orchestration across multiple analysis skills
- `output-report-index` - explicit Markdown and HTML report index generator for `output/index.md` and `output/index.html`
- `market-data-router` - routed market data fetch and fallback logic

## Orchestrator Notes

`multi-agent-stock-analysis` is implemented by the packaged orchestrator script, not by separate legacy agent-definition files. The current orchestrator:

- resolves the repo root dynamically
- generates seven skill prompts for the basic stock-analysis workflow: company profile, fundamental, institutional, GIE, reflexivity deep, reportify, and non-consensus
- writes a prompt plan Markdown file and orchestration JSON
- does not execute child skills or launch another agent process
- supports summary composition from already completed handoff data

Recommended live usage is to say `使用 invest-flow:multi-agent-stock-analysis 分析 MRVL` in Codex or Claude Code. The agent then executes the child skill prompts in the current session and writes the final Chinese report.

## Output Conventions

- Fundamental analysis: `output/fundamental-analysis/{ticker}-{company-name}-{date}.md`
- Earnings report analysis: `output/earnings-report-analysis/earnings-report-analysis-{TICKER}-{period}-{YYYY-MM-DD}.md`
- AI infrastructure sector discovery: `output/ai-infrastructure-sector-discovery/ai-infrastructure-sector-discovery-{YYYY-MM-DD}.md`
- AI infrastructure scarcity radar: `output/ai-infrastructure-scarcity-radar/ai-infrastructure-scarcity-radar-{topic}-{YYYY-MM-DD}.md`
- Chain-alpha mismatch discovery: `output/chain-alpha-mismatch-discovery/chain-alpha-mismatch-discovery-{主题}-{YYYY-MM-DD}.md`
- Chain-alpha monopoly screen: `output/chain-alpha-monopoly-screen/chain-alpha-monopoly-screen-{环节}-{YYYY-MM-DD}.md`
- Chain-alpha verification: `output/chain-alpha-verification/chain-alpha-verification-{TICKER或环节}-{YYYY-MM-DD}.md`
- Chain-alpha pipeline summary: `output/chain-alpha-pipeline/chain-alpha-pipeline-{主题}-{YYYY-MM-DD}.md`
- Chain-alpha delivery tracking: `output/chain-alpha-delivery-tracking/chain-alpha-delivery-tracking-{TICKER}-{YYYY-MM-DD}.md`
- Company profile: `output/company-profile/company-profile-{TICKER}-{YYYY-MM-DD}.md`
- Company buyability score: `output/company-buyability-score/company-buyability-score-{TICKER}-{YYYY-MM-DD}.md`
- Industry chain analysis: `output/industry-chain-analysis/industry-chain-analysis-{topic}-{YYYY-MM-DD}.md`
- Index PE sensitivity: `output/index-pe-sensitivity/index-pe-sensitivity-{index}-{YYYY-MM-DD}.md`
- Institutional analysis: `output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md`
- GIE framework: `output/gie-investment-framework/gie-{title}-{date}.md`
- Non-consensus company discovery: `output/non-consensus-company-discovery/non-consensus-company-discovery-{theme}-{YYYY-MM-DD}.md`
- Gold analysis: `output/gold-analysis/gold-{analysis-type}-{date}.md`
- Reflexivity quick scan: `output/reflexivity-quick-scan/`
- Reflexivity deep analysis: `output/reflexivity-deep-analysis/`
- Professional investment analyst: `output/professional-investment-analyst/professional-investment-analyst-{TICKER}-{YYYY-MM-DD}.md`
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
