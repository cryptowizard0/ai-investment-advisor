# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered investment analysis system built on the OpenCode "Skill + Subagent" architecture. Multiple specialized AI agents perform comprehensive investment analysis across dimensions: fundamental analysis, institutional flow detection, GIE investment framework evaluation, and gold market bubble risk assessment.

**Language Context**: Investment reports and skill descriptions are primarily in Chinese (中文). Code comments are in English. Financial terms remain in English (RSI, MACD, P/E, OBV, CMF, etc.).

## Repository Structure

```
.
├── .agents/
│   ├── agents/                          # OpenCode agent definitions
│   │   ├── fundamental-analysis-agent/
│   │   ├── gie-framework-agent/
│   │   ├── institutional-accumulation-agent/
│   │   ├── summary-synthesis-agent/
│   │   └── super-analyzer/
│   └── skills/                          # Core skill implementations
│       ├── fundamental-analysis/
│       ├── institutional-accumulation-analysis/
│       ├── gold-trend-analysis/
│       ├── gie-investment-framework/
│       ├── multi-agent-stock-analysis/
│       ├── market-data-router/
│       ├── skill-creator/
│       └── ui-ux-pro-max/
├── .claude/
│   ├── skills/                          # Claude-specific skill copies
│   │   ├── fundamental-analysis/
│   │   ├── gold-trend-analysis/
│   │   └── gie-investment-framework/
│   └── settings.local.json             # Claude permissions config (if present)
├── .opencode/                           # OpenCode framework artifacts
├── output/                              # Generated reports (created on first save)
│   ├── fundamental-analysis/
│   ├── institutional-accumulation-analysis/
│   ├── gie-investment-framework/
│   ├── gold-analysis/
│   └── summary/
├── *.skill                              # Packaged skills (zip archives)
├── AGENTS.md                            # Multi-agent system documentation
└── CLAUDE.md                            # This file
```

## Common Commands

### Virtual Environment
```bash
source .venv/bin/activate   # Activate virtual environment (Python 3.12.10)
.venv/bin/python            # Direct interpreter path
pip install yfinance pandas requests pyyaml  # Install dependencies
```

### Skill Development
```bash
# Initialize new skill
cd .agents/skills/skill-creator
python scripts/init_skill.py <skill-name> --path ../

# Validate skill structure
python scripts/quick_validate.py <skill-directory>

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

### Multi-Agent Orchestration
```bash
python .agents/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --execution-mode command
```

### Market Data
```bash
python .agents/skills/market-data-router/scripts/fetch_market_data.py --help
```

## Architecture

### Skill-Based System

Skills are modular AI capabilities stored in `.agents/skills/` and `.claude/skills/`. Each skill follows:

```
skill-name/
├── SKILL.md          # Required — YAML frontmatter (name, description) + workflow instructions
├── scripts/          # Executable Python helpers
├── references/       # Detailed documentation loaded on demand
└── assets/           # Templates and output assets
```

**SKILL.md frontmatter format:**
```yaml
---
name: skill-name
description: "Clear description with WHEN to use this skill"
---
```

Keep SKILL.md under 500 lines. Use `references/` for detailed docs. No README.md or CHANGELOG.md inside skill directories.

### Active Skills

| Skill | Purpose | Output Path |
|-------|---------|-------------|
| `fundamental-analysis` | Deep-dive stock analysis (financials, valuation, technicals) | `./output/fundamental-analysis/{ticker}-{company-name}-{date}.md` |
| `institutional-accumulation-analysis` | Detect whale accumulation/distribution via VSA, divergence, microstructure, options flow | `./output/institutional-accumulation-analysis/机构操作分析-{YYYYMMDD}-{TICKER}.md` |
| `gold-trend-analysis` | Gold bubble risk assessment (0-100 quantitative score) | `./output/gold-analysis/gold-{analysis-type}-{date}.md` |
| `gie-investment-framework` | "Golden Shovel" asset discovery for 1-3 year horizons | `./output/gie-investment-framework/gie-{title}-{date}.md` |
| `multi-agent-stock-analysis` | Orchestrate parallel execution of fundamental, institutional, and GIE agents | `./output/summary/综合分析-{TICKER}-{date}.md` |
| `market-data-router` | Unified market data fetcher with fallback routing | Cache only; data returned in-memory |
| `skill-creator` | Scaffold and package new skills | N/A |

### Multi-Agent Orchestrator

`.agents/skills/multi-agent-stock-analysis/scripts/orchestrator.py` — core orchestration engine.

**Key classes:**
- `MultiAgentOrchestrator` — coordinates parallel agents
- `AgentExecutor` — runs individual agents with retry logic
- `SubAgentResult` — dataclass for execution results (`status`, `output`, `report_path`, `retry_count`, `key_findings`, `key_metrics`)
- `OrchestrationConfig` — configures retry behavior and timeouts
- `AnalysisStatus` — enum (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `RETRYING`, `PARTIAL`)

**Failure detection triggers retry:**
- Output < 100 characters (empty response)
- Timeout > 240 seconds
- Exception during execution
- Missing keywords: `"分析"`, `"报告"`, `"结论"`

**Retry strategy:** immediate retry, max 1 retry per agent, continue with partial results on failure.

```python
OrchestrationConfig(
    max_retries=1,
    timeout_seconds=240,
    retry_on_empty=True,
    retry_on_timeout=True,
    parallel_execution=True
)
```

**Python API:**
```python
from orchestrator import analyze_stock_with_retry
result = analyze_stock_with_retry(ticker="TSLA", max_retries=1, timeout=240, execution_mode="command")
```

### Market Data Router

`.agents/skills/market-data-router/scripts/fetch_market_data.py` — unified data fetcher with fallback.

- **US stocks**: Yahoo Finance primary, Polygon for options/dark pools
- **Intervals**: `5m`, `1h`, `1d`, `auto` (auto-selects based on time span)
- **Fallback flags**: `fallback_to_yahoo`, `partial_data`
- **Cache**: `--cache-dir`, `--cache-ttl` options

### Institutional Analysis Scoring

Scoring range: **-100 to +100**

- Strong accumulation: +60 to +100
- Moderate accumulation: +20 to +59
- Neutral: -19 to +19
- Moderate distribution: -20 to -59
- Strong distribution: -60 to -100

References: `references/scoring-system.md`, `references/scoring-quickref.md`, `references/vsa-patterns.md`, `references/divergence-guide.md`

## Output Conventions

### Report Naming
- Fundamental: `TSLA-Tesla-2026-02-06.md`
- Institutional: `机构操作分析-20260206-TSLA.md`
- GIE: `gie-宁德时代-2026-01-29.md`
- Gold: `gold-bubble-risk-2026-01-28.md`
- Summary: `综合分析-TSLA-2026-02-06.md`

### Duplicate Handling
Auto-increment if file exists:
- First: `report.md`
- Second: `report(1).md`
- Third: `report(2).md`

```python
os.makedirs(output_dir, exist_ok=True)
```

## Code Style

### Python
- Standard library imports first, then third-party, separated by blank line
- `snake_case` for functions/variables, `UPPER_SNAKE_CASE` for constants, `PascalCase` for classes
- Skill directories use `hyphen-case`
- f-strings preferred; 4-space indentation; 100-char soft line limit
- Explicit `try/except` with meaningful messages; no bare `except:`
- Docstrings for modules and functions

### Skill Development
- Progressive disclosure: SKILL.md → references/ → assets/
- SKILL.md must have YAML frontmatter with `name` and `description`
- Descriptions should explain **when** to use the skill (trigger conditions)

## Key Configuration

### Claude Permissions (`.claude/settings.local.json`)
Pre-configured permissions for:
- `WebSearch` and `WebFetch`
- Bash commands: `python3`, `pip install`, `curl`, `tree`
- Financial data domains: `finance.yahoo.com`, `finviz.com`, `investing.com`, `cnbc.com`, `marketwatch.com`, `cftc.gov`, `cmegroup.com`, `jmbullion.com`, `goldsilverratio.org`, and Chinese financial sites (`sina.com.cn`, `10jqka.com.cn`, etc.)

### OpenCode Framework
`.opencode/package.json` depends on `@opencode-ai/plugin: 1.1.53`.

### Data Format
- Historical data CSV: `Date,Open,High,Low,Close,Volume`
- Reports: Markdown with primarily Chinese content
- Skill definitions: Bilingual YAML frontmatter

## Development Notes

- **Python Version**: 3.12.10 (virtual environment at `.venv/`)
- **Dependencies**: Core scripts use only Python standard library; external packages (`yfinance`, `pandas`, `requests`, `PyYAML`) used in specific scripts
- **No formal test suite**: testing done by executing skills on real tasks and using `quick_validate.py`
- **Skill Packaging**: `.skill` files are zip archives of skill directories for distribution
- **Output directory**: `./output/` is git-ignored and created on first report save
- **No credentials in repo**: API keys and secrets must be provided via environment variables at runtime

## Data Sources

- **Yahoo Finance** (`yfinance`) — real-time quotes and historical OHLCV data
- **Polygon.io** — options chains and dark pool data (US markets)
- **CFTC COT reports** — institutional futures positioning
- **Web search** — latest news and analyst estimates
