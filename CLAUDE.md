# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered investment analysis project that combines technical analysis tools with AI-driven fundamental and institutional analysis capabilities. The project uses a modular "skill" system where each skill encapsulates domain expertise for specific analysis types.

**Language Context**: Investment reports and skill descriptions are primarily in Chinese (中文). Code comments are in English.

## Common Commands

### Technical Analysis
```bash
# Run technical indicator calculation on TSLA data
python analyze_tsla.py
```

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Python interpreter
.venv/bin/python
```

### Skill Development
```bash
# Initialize new skill
cd .agents/skills/skill-creator
python scripts/init_skill.py <skill-name> --path ../

# Package skill for distribution
python scripts/package_skill.py <path/to/skill-folder>
```

### Report Operations
```bash
# Save fundamental analysis report
cd .agents/skills/fundamental-analysis
python scripts/save_report.py ~/report.md TSLA

# Save institutional analysis report
cd .agents/skills/institutional-accumulation-analysis
python scripts/save_report.py ~/report.md TSLA
```

## Architecture

### Skill-Based System
Skills are modular AI capabilities stored in `.agents/skills/` and `.claude/skills/`. Each skill follows a standard structure:

```
skill-name/
├── SKILL.md                    # Skill definition with YAML frontmatter (name, description)
├── scripts/                    # Helper utilities
│   └── save_report.py          # Report saving with auto-incrementing filenames
└── references/                 # Documentation and templates
    └── report-template.md
```

**Active Skills**:
- `fundamental-analysis`: Deep-dive stock analysis combining financials, valuation, and technicals. Outputs to `./output/fundamental-analysis/基础分析-{YYYYMMDD}-{TICKER}.md`
- `institutional-accumulation-analysis`: Detect institutional (whale) buying/selling patterns using VSA, divergence, microstructure, and options flow. Outputs to `./output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md`
- `gold-trend-analysis`: Gold market bubble risk assessment with 0-100 quantitative risk scores. Outputs to `./output/gold-analysis/gold-{analysis-type}-{date}.md`
- `gie-investment-framework`: "Golden Shovel" asset discovery framework for 1-3 year investment horizons. Outputs to `./output/gie-investment-framework/gie-{title}-{date}.md`

### Technical Analysis Script (`analyze_tsla.py`)
Standalone Python script using only standard library that calculates:
- **EMA**: 12-day and 26-day exponential moving averages
- **MACD**: MACD line, Signal line (9-day EMA), Histogram
- **RSI**: 14-period with Wilder's smoothing
- **OBV**: On-Balance Volume
- **CMF**: Chaikin Money Flow (20-period)

Reads from `tsla_data.csv` (expected format: `Date,Open,High,Low,Close,Volume`) and outputs last 12 days with all indicators.

### Report Saving Convention
All skills save reports following this pattern:
- Check for existing files and auto-increment with `(1)`, `(2)`, etc. to avoid overwrites
- Create output directories if they don't exist
- Confirm saved path to user

## Key Configuration

### Claude Permissions (`.claude/settings.local.json`)
Pre-configured permissions for:
- WebSearch and WebFetch
- Bash commands: python3, pip install, curl
- Financial data domains: finance.yahoo.com, finviz.com, investing.com, cnbc.com, marketwatch.com, jmbullion.com, goldsilverratio.org, cmegroup.com, and Chinese financial sites (sina.com.cn, 10jqka.com.cn, etc.)

### Data Format
- Historical data: CSV files with columns `Date,Open,High,Low,Close,Volume`
- Reports: Markdown with Chinese content
- Skill definitions: Bilingual (Chinese + English)

## Development Notes

- **Python Version**: 3.12
- **Dependencies**: Core scripts use only Python standard library (no external packages)
- **Skill Packaging**: `.skill` files are zip archives of skill directories for distribution
- **Output Structure**: All analysis reports saved to `./output/{skill-name}/` with dated filenames
