# Apps Guide

## Purpose

This document explains how to work inside `apps/` without mixing responsibilities.

## Layer Ownership

### `apps/web`

- Owns UI, routing, report reading, and user interaction
- Talks only to the backend layer
- Must not call `.agents/skills` or `opencode` directly

### `apps/backend`

- Owns browser-facing APIs, jobs, threads, SSE, and report metadata
- Talks to the agent layer through gateway code
- Must not implement investment skill logic directly

### `apps/agent`

- Owns skill routing, runtime orchestration, and artifact generation
- Mounts and executes local skills
- Must not absorb product UI or browser-facing concerns

### `packages/contracts`

- Shared schemas between backend and agent live here
- If a request or response shape is shared across layers, define it here instead of duplicating types

## How To Route Changes

- UI change, page behavior, styling, client interaction: `apps/web`
- Product API, job lifecycle, SSE, report indexing: `apps/backend`
- Skill execution, runtime orchestration, output generation: `apps/agent`
- Shared payload schema: `packages/contracts`

If a change crosses multiple layers, keep each concern in its owning layer instead of collapsing logic into one app.

## Local Run Commands

```bash
source .venv/bin/activate

uvicorn app.main:app --app-dir apps/agent --reload --port 9002
AGENT_SERVICE_URL=http://127.0.0.1:9002 uvicorn app.main:app --app-dir apps/backend --reload --port 8000
BACKEND_API_URL=http://127.0.0.1:8000 pnpm --dir apps/web dev
```

## Quick Verification

- Agent or backend Python changes: `python -m compileall apps/backend/app apps/agent/app`
- Entrypoint changes: `bash -n apps/start-entrypoint.sh`
- Web changes: run the web dev server and validate the changed flow manually

## Related Files

- `apps/README.md`
- `apps/web/README.md`
- `apps/backend/README.md`
- `apps/agent/README.md`
- `apps/container-runtime.md`
