# Investment Platform Agent

Agent layer for the three-layer investment agent product.

## Responsibilities

- Owns skill routing, runtime orchestration, and artifact generation
- Mounts the local `.agents/skills/` directory
- Hides `opencode` integration details from the backend and frontend

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir apps/agent --reload --port 9002
```
