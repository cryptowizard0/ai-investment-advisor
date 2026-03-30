from __future__ import annotations

import os

import httpx

from app.models.schemas import AnalysisJobRequest, AnalysisResult


class AgentGateway:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url or os.getenv("AGENT_SERVICE_URL", "http://127.0.0.1:9002")
        self.timeout = timeout

    async def run_analysis(self, payload: AnalysisJobRequest) -> AnalysisResult:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/v1/agent-runs", json=payload.model_dump(mode="json"))
            response.raise_for_status()
            return AnalysisResult.model_validate(response.json())

    async def get_artifacts(self, run_id: str) -> list[dict]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(f"/v1/agent-runs/{run_id}/artifacts")
            response.raise_for_status()
            return response.json()

    async def cancel(self, run_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(f"/v1/agent-runs/{run_id}/cancel")
            response.raise_for_status()
            return response.json()
