# InvestFlow

`InvestFlow` is a repo-local Codex plugin for investment research workflows. The repository now treats the plugin package under `plugins/invest-flow/` as the canonical source for all investment skills.

## Current Structure

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
│           ├── reportify-stock-analysis/
│           ├── multi-agent-stock-analysis/
│           └── market-data-router/
└── output/
```

## Plugin Location

- Plugin root: `plugins/invest-flow`
- Plugin manifest: `plugins/invest-flow/.codex-plugin/plugin.json`
- Repo marketplace: `.agents/plugins/marketplace.json`

## Included Skills

- `fundamental-analysis`
- `institutional-accumulation-analysis`
- `gie-investment-framework`
- `gold-trend-analysis`
- `reflexivity-quick-scan`
- `reflexivity-deep-analysis`
- `reportify-stock-analysis`
- `multi-agent-stock-analysis`
- `market-data-router`

## Install In Codex

1. Open this repository in Codex.
2. Reload Codex so it reads `.agents/plugins/marketplace.json`.
3. Open the plugin marketplace and install `InvestFlow`.

If `InvestFlow` does not appear, verify that `plugins/invest-flow/.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` both exist and contain valid JSON.

## Use In Codex

After installation, call the packaged skills directly through normal prompts.

Examples:

- `Use InvestFlow to run a multi-agent analysis for TSLA.`
- `Use InvestFlow to analyze institutional accumulation in AAPL over the last 3 months.`
- `Use InvestFlow to assess gold bubble risk this week.`
- `Use InvestFlow to perform a reflexivity quick scan on NVIDIA.`
- `Use InvestFlow to run a deep reflexivity analysis on AI power infrastructure.`
- `Use InvestFlow to generate a structured stock report for TSLA.`
- `Use InvestFlow to fetch 5m market data for TSLA with market-data-router.`
- `Use InvestFlow to evaluate whether NVIDIA is a GIE-style golden shovel asset.`

## Environment Variables

If you want `market-data-router` to use external market data providers, create a local `.env` from `.env_example`:

```bash
cp .env_example .env
```

Current template variables:

- `POLYGON_API_KEY` - Polygon API key for US options and dark-pool related data
- `ALLTICK_API_KEY` - AllTick API key for routed quote/bar data
- `YAHOO_ENABLED` - enable Yahoo fallback when routed sources are unavailable
- `ALLTICK_BASE_URL` - AllTick API base URL
- `POLYGON_BASE_URL` - Polygon API base URL

The packaged scripts search for `.env` automatically from the current working directory upward, so placing `.env` in the repo root is sufficient.

## Direct Script Usage

You can also run the packaged scripts directly from the repo root:

```bash
python plugins/invest-flow/skills/multi-agent-stock-analysis/scripts/orchestrator.py TSLA --execution-mode command
python plugins/invest-flow/skills/market-data-router/scripts/fetch_market_data.py --market US --symbol TSLA --interval 5m --types bars --out -
```

## Output Paths

Generated analysis files are written under `output/`:

- `output/fundamental-analysis/`
- `output/institutional-accumulation-analysis/`
- `output/gie-investment-framework/`
- `output/gold-analysis/`
- `output/reflexivity-quick-scan/`
- `output/reflexivity-deep-analysis/`
- `output/reportify-stock-analysis/`
- `output/summary/`
- `output/cache/market-data/`

## Notes

- This is a repo-local plugin, not a published remote marketplace plugin.
- Investment skills are maintained only inside `plugins/invest-flow/skills/`.
- `.agents/plugins/marketplace.json` is the only remaining repo-local `.agents` asset needed for plugin discovery.
