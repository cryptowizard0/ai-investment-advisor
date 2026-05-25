from __future__ import annotations

from datetime import datetime
from typing import List

from .models import SkillSpec, TaskRequest
from .registry import SkillRegistry


def create_stock_request(ticker: str, company_name: str = "") -> TaskRequest:
    normalized_ticker = ticker.strip().upper() or "TSLA"
    task_id = f"ma_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return TaskRequest(
        task_id=task_id,
        intent="stock_decision_basic",
        target=normalized_ticker,
        ticker=normalized_ticker,
        company_name=company_name.strip(),
        market="unknown",
        horizon="mixed",
        requested_outputs=["summary", "handoff_json"],
    )


def plan_basic_stock_analysis(request: TaskRequest, registry: SkillRegistry) -> List[SkillSpec]:
    if not request.ticker:
        raise ValueError("ticker is required for stock_decision_basic")
    return registry.basic_stock_specs()
