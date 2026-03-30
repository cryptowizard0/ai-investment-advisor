from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.models import AnalysisJobRequest, AnalysisResult
from app.runtime.opencode_adapter import OpencodeAdapter


app = FastAPI(title="Investment Platform Agent", version="0.1.0")
adapter = OpencodeAdapter()
runs: dict[str, AnalysisResult] = {}


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "layer": "agent"}


@app.post("/v1/agent-runs", response_model=AnalysisResult)
async def create_agent_run(payload: AnalysisJobRequest) -> AnalysisResult:
    result = adapter.execute(payload)
    runs[payload.run_id] = result
    return result


@app.get("/v1/agent-runs/{run_id}", response_model=AnalysisResult)
async def get_agent_run(run_id: str) -> AnalysisResult:
    result = runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@app.post("/v1/agent-runs/{run_id}/cancel")
async def cancel_agent_run(run_id: str) -> dict[str, str]:
    result = runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    result.status = "canceled"
    return {"run_id": run_id, "status": "canceled"}


@app.get("/v1/agent-runs/{run_id}/artifacts")
async def get_artifacts(run_id: str) -> list[dict[str, str]]:
    result = runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return [artifact.model_dump(mode="json") for artifact in result.artifacts]
