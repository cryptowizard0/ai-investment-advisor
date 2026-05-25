from __future__ import annotations

import re
from datetime import datetime
from typing import List
from uuid import uuid4

from .models import SkillSpec, TaskRequest
from .registry import SkillRegistry


_TICKER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,15}$")


def _normalize_ticker(ticker: str) -> str:
    stripped_ticker = ticker.strip()
    if not stripped_ticker:
        raise ValueError("ticker is required for stock_decision_basic")
    if not _TICKER_PATTERN.fullmatch(stripped_ticker):
        raise ValueError(f"invalid ticker for stock_decision_basic: {ticker}")
    return stripped_ticker.upper()


def create_stock_request(ticker: str, company_name: str = "") -> TaskRequest:
    normalized_ticker = _normalize_ticker(ticker)
    task_id = f"ma_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
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
    if request.intent != "stock_decision_basic":
        raise ValueError(f"unsupported intent for basic stock analysis: {request.intent}")
    normalized_ticker = _normalize_ticker(request.ticker)
    if request.ticker != normalized_ticker:
        raise ValueError("ticker must be normalized before planning")
    return registry.basic_stock_specs()
