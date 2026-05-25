# Agent Guidelines

## Project Overview

This repository is an AI-driven investment analysis system packaged as a repo-local Codex plugin. The canonical runtime surface is `plugins/invest-flow/`, which contains the plugin manifest, assets, and all investment skills.

**Project Language**: Documentation and investment reports are primarily in Chinese (中文). Code comments are in English. Financial terms remain in English (RSI, MACD, P/E, OBV, etc.).

## Technology Stack

- **Python**: 3.12.10 (virtual environment at `.venv/`)
- **Node.js**: Codex/OpenCode runtime environment
- **Key Python Libraries**:
  - `yfinance`
  - `pandas`
  - `requests`
  - `PyYAML`

## Current Repository Structure

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
│           ├── fundamental-analysis/
│           ├── institutional-accumulation-analysis/
│           ├── gie-investment-framework/
│           ├── gold-trend-analysis/
│           ├── reflexivity-quick-scan/
│           ├── reflexivity-deep-analysis/
│           ├── professional-investment-analyst/
│           ├── reportify-stock-analysis/
│           ├── daily-us-market-scan/
│           ├── multi-agent-stock-analysis/
│           └── market-data-router/
├── output/
│   ├── fundamental-analysis/
│   ├── institutional-accumulation-analysis/
│   ├── gie-investment-framework/
│   ├── gold-analysis/
│   ├── reflexivity-quick-scan/
│   ├── reflexivity-deep-analysis/
│   ├── professional-investment-analyst/
│   ├── reportify-stock-analysis/
│   ├── daily-us-market-scan/
│   ├── summary/
│   └── cache/market-data/
└── .venv/
```

## Source Of Truth

- Investment skills live only in `plugins/invest-flow/skills/`.
- Plugin discovery metadata lives in `.agents/plugins/marketplace.json`.
- Do not reintroduce duplicate investment skills under `.agents/skills/`, `.claude/skills/`, or legacy agent-definition folders.

## Key Files

- `plugins/invest-flow/.codex-plugin/plugin.json` - plugin manifest
- `.agents/plugins/marketplace.json` - repo-local plugin marketplace entry
- `plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py` - multi-agent orchestration entrypoint
- `plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py` - market data router entrypoint

## Build/Test Commands

This project has no formal test suite. Validation is done through direct script execution and real analysis tasks.

```bash
# Activate virtual environment
source .venv/bin/activate

# Check orchestrator CLI
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py --help

# Check market data router CLI
python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --help

# Run multi-agent analysis
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --execution-mode command
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

- `fundamental-analysis` - stock fundamental and technical analysis
- `institutional-accumulation-analysis` - whale accumulation/distribution analysis
- `gie-investment-framework` - 1-3 year golden-shovel style investment framework
- `gold-trend-analysis` - gold bubble risk and macro signal analysis
- `reflexivity-quick-scan` - fast stage judgment with a Soros-style reflexivity lens
- `reflexivity-deep-analysis` - full-cycle reflexivity research on stocks, sectors, and narratives
- `professional-investment-analyst` - professional investment research system with evidence, valuation, reflexivity, decision, and tracking dashboard
- `reportify-stock-analysis` - fixed-template structured stock research report generation
- `daily-us-market-scan` - Chinese daily US market close scan covering indices, macro, sectors, themes, breadth, technicals, earnings, flows, watchlists, and next-session plans
- `multi-agent-stock-analysis` - orchestration across multiple analysis skills
- `market-data-router` - routed market data fetch and fallback logic

## Orchestrator Notes

`multi-agent-stock-analysis` is implemented by the packaged orchestrator script, not by separate legacy agent-definition files. The current orchestrator:

- resolves the repo root dynamically
- executes three skill commands directly
- validates each result
- retries once on empty output, timeout, or exception
- aggregates partial success into a final summary flow

## Output Conventions

- Fundamental analysis: `output/fundamental-analysis/{ticker}-{company-name}-{date}.md`
- Institutional analysis: `output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md`
- GIE framework: `output/gie-investment-framework/gie-{title}-{date}.md`
- Gold analysis: `output/gold-analysis/gold-{analysis-type}-{date}.md`
- Reflexivity quick scan: `output/reflexivity-quick-scan/`
- Reflexivity deep analysis: `output/reflexivity-deep-analysis/`
- Professional investment analyst: `output/professional-investment-analyst/professional-investment-analyst-{TICKER}-{YYYY-MM-DD}.md`
- Reportify stock analysis: `output/reportify-stock-analysis/reportify-stock-analysis-{TICKER}-{YYYY-MM-DD}.md`
- Daily US market scan: `output/daily-us-market-scan/us-market-close-daily-{YYYY-MM-DD}.md`
- Summary report: `output/summary/综合分析-{TICKER}-{date}.md`
- Market data cache: `output/cache/market-data/`

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
- If plugin packaging changes, update both `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`.
