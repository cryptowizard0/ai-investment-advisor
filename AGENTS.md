# Agent Guidelines

## Purpose

This file is the repo index for human contributors and coding agents. Keep it short.
Put detailed rules in dedicated documents and link to them from here.

## Project Summary

AI-driven investment analysis system built around local skills plus a three-layer product app:

- `apps/web`: frontend layer
- `apps/backend`: product backend layer
- `apps/agent`: agent runtime layer
- `.agents/skills/`: reusable investment analysis skills
- `packages/contracts/`: shared backend-agent contracts
- `output/`: generated reports and run artifacts

Project language rules:

- Documentation and investment reports: Chinese
- Code comments: English
- Financial terms: keep standard English terms such as `RSI`, `MACD`, `P/E`, `OBV`

## Start Here

Read only what matches your task:

1. Repo architecture: `ARCHITECTURE.md`
2. Code style and authoring rules: `docs/code-style.md`
3. App layer boundaries and runbook: `docs/apps-guide.md`
4. Container notes: `apps/container-runtime.md`
5. Claude-specific notes: `CLAUDE.md`
6. Skill-specific workflow: the target skill's `SKILL.md`

## Key Paths

```text
.
├── .agents/skills/
│   ├── chief-investment-advisor/
│   ├── fundamental-analysis/
│   ├── institutional-accumulation-analysis/
│   ├── gie-investment-framework/
│   ├── gold-trend-analysis/
│   └── market-data-router/
├── apps/
│   ├── web/
│   ├── backend/
│   └── agent/
├── packages/contracts/
├── output/
├── ARCHITECTURE.md
├── CLAUDE.md
└── AGENTS.md
```

## Available Skills

Use the target skill's `SKILL.md` for workflow details. This section is only a capability index.

- `chief-investment-advisor`: 多 skill 汇总决策入口，适合单票或主题的日常投顾结论
- `fundamental-analysis`: 个股基本面、估值、财务与技术面深度分析
- `institutional-accumulation-analysis`: 主力吸筹/派发、量价和资金行为分析
- `gie-investment-framework`: 1 到 3 年视角的“金铲子”资产发现与评估
- `gold-trend-analysis`: 黄金市场泡沫风险与交易风险分析
- `market-data-router`: 金融行情数据抓取、路由与降级兜底
- `reflexivity-quick-scan`: 反身性 5 分钟快速阶段判断
- `reflexivity-deep-analysis`: 反身性完整周期深度研究
- `reportify-stock-analysis`: 固定模板的结构化个股投研报告
- `skill-creator`: 创建或更新 skill 的规范与脚手架指南
- `ui-ux-pro-max`: Web 或产品界面的 UI/UX 设计与评审辅助

## Working Rules

### Skills

- Each skill must keep its own workflow, scripts, references, and assets inside its directory.
- Each skill requires a `SKILL.md` with YAML frontmatter.
- Do not duplicate large skill instructions into this file.
- When editing or creating a skill, also read `.agents/skills/skill-creator/SKILL.md`.

### Apps

- `apps/web` must not call `.agents/skills` or `opencode` directly.
- `apps/backend` owns browser-facing APIs, jobs, threads, SSE, and report metadata.
- `apps/agent` owns skill routing, runtime orchestration, and artifact generation.
- Shared request and response schemas belong in `packages/contracts`.

### Output

- Generated reports must live under `output/`.
- Use the existing naming convention already defined by the relevant skill.
- If a naming rule changes, update that skill's `SKILL.md` or its local reference docs, not this file.

## Common Commands

```bash
source .venv/bin/activate

python .agents/skills/market-data-router/scripts/fetch_market_data.py --help

uvicorn app.main:app --app-dir apps/agent --reload --port 9002
AGENT_SERVICE_URL=http://127.0.0.1:9002 uvicorn app.main:app --app-dir apps/backend --reload --port 8000
BACKEND_API_URL=http://127.0.0.1:8000 pnpm --dir apps/web dev

python -m compileall apps/backend/app apps/agent/app
bash -n apps/start-entrypoint.sh
```

## Testing

There is no formal test suite yet. Default verification:

1. Run the smallest relevant command for the changed layer.
2. For backend or agent Python code, run `python -m compileall apps/backend/app apps/agent/app`.
3. For shell startup changes, run `bash -n apps/start-entrypoint.sh`.
4. For skill changes, execute the smallest realistic workflow or validator for that skill.

## Source Documents

Use these files as the canonical home for details:

- `docs/code-style.md`: Python, TypeScript, comments, naming, skill authoring
- `docs/apps-guide.md`: layer ownership, run commands, change routing for `apps/`
- `apps/web/README.md`: frontend quick start
- `apps/backend/README.md`: backend quick start
- `apps/agent/README.md`: agent quick start
- `apps/container-runtime.md`: container behavior

## Maintenance Rule

Keep `AGENTS.md` under 200 lines and index-oriented.
If a section starts accumulating examples, edge cases, or policy detail, move it into a dedicated doc and leave only a short summary plus link here.
