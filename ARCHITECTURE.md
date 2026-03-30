# Three-Layer Investment Agent Architecture

## Layer 1: Frontend

Path: `apps/web`

Responsibilities:
- Own user interaction, workspace layout, report reading, and route handlers
- Call backend APIs only
- Never access `.agents/skills` directly
- Never call `opencode` directly

Key routes:
- `/`
- `/app`
- `/report/[id]`
- `/library`
- `/settings`

Key API pass-throughs:
- `POST /api/threads`
- `POST /api/threads/:id/messages`
- `GET /api/jobs/:id/stream`
- `GET /api/reports/:id`
- `GET /api/library`
- `POST /api/reports/:id/export`

## Layer 2: Backend

Path: `apps/backend`

Responsibilities:
- Own thread lifecycle, job records, report indexing, and SSE delivery
- Act as the only product-facing API layer
- Translate frontend requests into agent runs
- Keep report metadata separate from agent runtime internals

Key endpoints:
- `POST /api/threads`
- `POST /api/threads/{thread_id}/messages`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/stream`
- `POST /api/jobs/{job_id}/cancel`
- `GET /api/jobs/{job_id}/artifacts`
- `GET /api/reports/{report_id}`
- `POST /api/reports/{report_id}/export`
- `GET /api/library`

Internal modules:
- `app/services/agent_gateway.py`
- `app/services/job_service.py`
- `app/services/report_service.py`
- `app/services/repository.py`

## Layer 3: Agent

Path: `apps/agent`

Responsibilities:
- Own skill routing and runtime orchestration
- Mount the local `.agents/skills/` directory
- Generate markdown/json artifacts
- Hide `opencode` integration details from upstream layers

Key endpoints:
- `POST /v1/agent-runs`
- `GET /v1/agent-runs/{run_id}`
- `POST /v1/agent-runs/{run_id}/cancel`
- `GET /v1/agent-runs/{run_id}/artifacts`

Internal modules:
- `app/runtime/task_router.py`
- `app/runtime/opencode_adapter.py`

## Shared Contracts

Path: `packages/contracts`

Artifacts:
- `analysis-job.schema.json`
- `analysis-result.schema.json`

These schemas define the handoff between backend and agent, and keep the frontend isolated from skill-specific formats.

## Current Runtime Status

- Frontend scaffold exists and is ready for dependency install
- Backend scaffold exists and compiles as Python source
- Agent scaffold exists and compiles as Python source
- Agent runtime is currently a controlled mock that writes real markdown/json artifacts
- Replacing the mock with real `opencode` execution should happen inside `apps/agent/app/runtime/opencode_adapter.py`
