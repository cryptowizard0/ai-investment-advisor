# Investment Platform Backend

Backend layer for the three-layer investment agent product.

## Responsibilities

- Owns product APIs, job lifecycle, report indexing, and SSE delivery
- Talks to the agent layer through `AgentGateway`
- Does not execute skills directly

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir apps/backend --reload --port 8000
```
