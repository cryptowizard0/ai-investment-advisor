# Agent Guidelines

## Project Overview

This is an AI-driven Investment Analysis Multi-Agent System built on a local "Skill + Subagent" architecture. The system combines multiple specialized AI agents to perform comprehensive investment analysis from different dimensions: fundamental analysis, institutional flow detection, GIE investment framework evaluation, and gold market bubble risk assessment.

The project uses a modular skill-based design where each skill encapsulates domain expertise for specific financial analysis tasks. Skills are reusable packages that extend AI agent capabilities.

**Project Language**: Documentation and investment reports are primarily in Chinese (中文). Code comments are in English. Financial terms remain in English (RSI, MACD, P/E, OBV, etc.).

## Technology Stack

- **Python**: 3.12.10 (virtual environment at `.venv/`)
- **Runtime**: Local Python skill scripts (no external orchestrator dependency)
- **Key Python Libraries**: 
  - `yfinance` - Market data fetching from Yahoo Finance
  - `pandas` - Data processing
  - `requests` - HTTP requests for CFTC COT data
  - Standard library for technical indicator calculations

## Project Structure

```
.
├── .agents/skills/              # Core skill definitions
│   ├── chief-investment-advisor/  # Chief advisor orchestration
│   ├── fundamental-analysis/    # Stock fundamental analysis
│   ├── institutional-accumulation-analysis/  # Whale detection
│   ├── gold-trend-analysis/     # Gold bubble risk assessment
│   ├── gie-investment-framework/  # "Golden shovel" asset discovery
│   └── skill-creator/           # Skill development utilities
├── .claude/skills/              # Claude-specific skill copies
├── .claude/settings.local.json  # Claude permissions config
├── output/                      # Generated reports
│   ├── fundamental-analysis/
│   ├── institutional-accumulation-analysis/
│   ├── gie-investment-framework/
│   ├── gold-analysis/
│   └── summary/
├── .agents/skills/chief-investment-advisor/SKILL.md                   # Chief advisor orchestration
├── .agents/skills/market-data-router/scripts/fetch_market_data.py     # Market data router
├── .agents/skills/institutional-accumulation-analysis/scripts/save_report.py
└── AGENTS.md
```

## Key Configuration Files

### `.claude/settings.local.json`
Pre-configured permissions for:
- WebSearch and WebFetch capabilities
- Bash commands: python3, pip install, curl, tree
- Financial data domains whitelist (yahoo.com, investing.com, cftc.gov, cmegroup.com, and Chinese financial sites)

### `.venv/pyvenv.cfg`
Python 3.12.10 virtual environment with `include-system-site-packages = false` for isolation.

## Build/Test/Lint Commands

This is an AI agent project with **no formal test suite**. Testing is done by executing skills on real tasks.

```bash
# Activate virtual environment
source .venv/bin/activate

# Run market data router script
python .agents/skills/market-data-router/scripts/fetch_market_data.py --help

# Run chief investment advisor (skill trigger)
/chief-investment-advisor TSLA

# Validate skill structure
python .agents/skills/skill-creator/scripts/quick_validate.py <skill-directory>

# Package a skill
python .agents/skills/skill-creator/scripts/package_skill.py <skill-folder>

# Initialize new skill
python .agents/skills/skill-creator/scripts/init_skill.py <skill-name> --path ../
```

## Code Organization

### 1. Skill-Based Analysis System (`.agents/skills/`)
Each skill follows a standard structure:
```
skill-name/
├── SKILL.md              # Required - skill definition with YAML frontmatter
├── scripts/              # Executable Python/shell scripts
├── references/           # Documentation (loaded on demand)
└── assets/               # Templates, files for output
```

**Active Skills:**
- `chief-investment-advisor`: Two-layer advisor pipeline (analysis layer + decision layer)
  - Output: `./output/summary/advisor-{target}-{YYYYMMDD}.md` and `.json`
  - Orchestrates market data, fundamental/institutional/GIE analysis, and final decisioning
- `fundamental-analysis`: Deep-dive stock analysis combining financials, valuation, and technicals
  - Output: `./output/fundamental-analysis/{ticker}-{company-name}-{date}.md`
  - Template: `references/report-template.md`
  
- `institutional-accumulation-analysis`: Detect institutional (whale) buying/selling patterns
  - Output: `./output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md`
  - Uses scoring system: -100 to +100 with classification thresholds
  - References: `scoring-system.md`, `scoring-quickref.md`, `analysis-template.md`
  
- `gold-trend-analysis`: Gold market bubble risk assessment with 0-100 risk scores
  - Output: `./output/gold-analysis/gold-bubble-risk-{date}.md`
  - Analyzes: real interest rates, COT positioning, gold-silver ratio, gold/SPX ratio
  
- `gie-investment-framework`: "Golden Shovel" asset discovery for 1-3 year investment horizons
  - Output: `./output/gie-investment-framework/gie-{title}-{date}.md`
  - Four-dimensional analysis: macro, supply-demand, financial, timing
  
### 2. Market Data Router (`.agents/skills/market-data-router/scripts/fetch_market_data.py`)
Unified market data fetcher with routing and fallback:
- Multi-market bars (`5m/1h/1d`, `auto` interval support)
- US options and dark pool routing via Polygon
- Fallback and quality flags (`fallback_to_yahoo`, `partial_data`, etc.)
- Optional cache control (`--cache-dir`, `--cache-ttl`)

## Code Style Guidelines

### Python

**Imports**:
- Standard library first, then third-party
- No wildcard imports
- Group imports with blank line separation

```python
import csv
import math
from datetime import datetime

import yfinance as yf
import pandas as pd
import requests
```

**Naming**:
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Skill directories: `hyphen-case`

**Formatting**:
- f-strings preferred for string formatting
- Max line length: 100 characters (soft limit)
- 4 spaces for indentation
- Two blank lines between top-level functions/classes

**Error Handling**:
- Explicit try-except blocks
- Meaningful error messages
- Avoid bare `except:` clauses

```python
try:
    data = yf.download(tickers, period="5d")
except Exception as e:
    print(f"Error fetching data: {e}")
    return
```

**Comments**:
- Chinese for domain concepts, English for technical terms
- Docstrings for modules and functions
- Inline comments for complex logic

### Skill Development

**SKILL.md Structure**:
```yaml
---
name: skill-name
description: "Clear description with WHEN to use this skill"
---
```

- Frontmatter required: `name` (hyphen-case), `description`
- Progressive disclosure: metadata → SKILL.md → references/
- Keep SKILL.md under 500 lines
- Use references/ for detailed documentation

**File Organization**:
- Required: `SKILL.md` with YAML frontmatter
- Optional: `scripts/`, `references/`, `assets/`
- No extraneous docs (README.md, CHANGELOG.md, etc.)

**Output Handling**:
- Check for existing files before writing
- Use numbered suffixes `(1)`, `(2)` for duplicates
- Create directories: `os.makedirs(exist_ok=True)`

## Testing Strategy

This project has **no formal test suite**. Testing is done by:
1. Executing skills on real analysis tasks
2. Validating skill structure with `quick_validate.py`
3. Testing scripts manually before packaging

## Retry Mechanism

The chief advisor pipeline supports retry for sub-skill execution:

```python
AdvisorConfig(
    max_retries=1,     # Maximum retry attempts per sub-skill
    timeout=240,       # Per-sub-skill timeout in seconds
)
```

## Output Conventions

### Report Naming
- **Fundamental analysis**: `{ticker}-{company-name}-{date}.md` (e.g., `TSLA-Tesla-2026-02-06.md`)
- **Institutional analysis**: `机构操作分析-{YYYYMMDD}-{TICKER}.md`
- **GIE framework**: `gie-{title}-{date}.md`
- **Gold analysis**: `gold-bubble-risk-{date}.md`
- **Advisor summary report**: `advisor-{target}-{YYYYMMDD}.md`

### Duplicate Handling
If file exists, append numbered suffix:
- First: `report.md`
- Second: `report(1).md`
- Third: `report(2).md`

### Directory Structure
```
./output/
├── fundamental-analysis/       # Stock fundamental reports
├── institutional-accumulation-analysis/  # Whale flow reports
├── gie-investment-framework/   # Golden shovel analysis
├── gold-analysis/              # Gold risk assessments
└── summary/                    # Multi-agent aggregated reports
```

## Key Workflows

### Creating a New Skill

```bash
cd .agents/skills/skill-creator
python scripts/init_skill.py <skill-name> --path ../
# Edit SKILL.md, customize scripts/references/assets
python scripts/package_skill.py ../<skill-name>
```

### Running Chief Investment Advisor

使用 skill trigger：
- `/chief-investment-advisor TSLA`
- `/chief-investment-advisor "AI电力基础设施"`

### Running Analysis Manually

1. Load appropriate skill from `.agents/skills/`
2. Read SKILL.md for workflow instructions
3. Search for latest financial data
4. Generate report using templates from `references/`
5. Save to `./output/{skill-type}/` with unique filename

## Security Considerations

- Virtual environment isolated (`include-system-site-packages = false`)
- WebFetch limited to whitelisted financial domains
- Bash commands restricted to python, pip, curl, tree
- No sensitive credentials stored in repository

## Data Sources

**Primary**:
- Yahoo Finance (yfinance) - Real-time quotes and historical data
- CFTC COT reports - Institutional positioning
- Web search - Latest news and market data

**Reference Only**:
- `./output/cache/market-data/` - Router cache artifacts for reproducible analysis

## Dependencies

Core scripts use only Python standard library. External packages used in specific scripts:
- `yfinance` - Market data
- `pandas` - Data processing
- `requests` - HTTP requests
- `PyYAML` - YAML parsing

Install with:
```bash
source .venv/bin/activate
pip install yfinance pandas requests pyyaml
```

## Version Information

- **Python**: 3.12.10
- **Skill Runtime**: Local Python scripts
- **Last Updated**: 2026-02-10

## Additional Documentation

- `CLAUDE.md` - Claude Code specific guidance
- `RETRY_MECHANISM.md` - Detailed retry mechanism design document
- `.agents/skills/chief-investment-advisor/SKILL.md` - Chief advisor workflow definition
