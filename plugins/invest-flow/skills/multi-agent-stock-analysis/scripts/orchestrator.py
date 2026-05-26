#!/usr/bin/env python3
"""Legacy orchestrator compatibility wrapper around investflow_pipeline.runner."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from investflow_pipeline.models import OrchestrationConfig
from investflow_pipeline.runner import analyze_stock_sync


def analyze_stock_with_retry(
    ticker: str,
    company: str = "",
    max_retries: int = 1,
    timeout: int = 240,
    **kwargs: Any,
) -> Dict[str, Any]:
    compatibility_config = kwargs.get("config")
    if not isinstance(compatibility_config, OrchestrationConfig):
        compatibility_config = None

    execution_mode = kwargs.get("execution_mode")
    if execution_mode is None:
        execution_mode = (
            compatibility_config.execution_mode
            if compatibility_config is not None
            else os.environ.get("ORCH_EXECUTION_MODE", "command")
        )

    if "parallel_execution" in kwargs:
        parallel_execution = kwargs["parallel_execution"]
    elif compatibility_config is not None:
        parallel_execution = compatibility_config.parallel_execution
    else:
        parallel_execution = True

    if "continue_on_failure" in kwargs:
        continue_on_failure = kwargs["continue_on_failure"]
    elif compatibility_config is not None:
        continue_on_failure = compatibility_config.continue_on_failure
    else:
        continue_on_failure = True

    resolved_max_retries = max_retries
    if compatibility_config is not None and max_retries == 1:
        resolved_max_retries = compatibility_config.max_retries

    resolved_timeout = timeout
    if compatibility_config is not None and timeout == 240:
        resolved_timeout = compatibility_config.timeout_seconds

    config = OrchestrationConfig(
        execution_mode=execution_mode,
        max_retries=resolved_max_retries,
        timeout_seconds=resolved_timeout,
        parallel_execution=parallel_execution,
        continue_on_failure=continue_on_failure,
    )
    project_root = kwargs.get("project_root")
    if project_root is not None:
        project_root = Path(project_root)
    result = analyze_stock_sync(ticker, company, config, project_root=project_root)
    payload = result.to_dict()
    payload["summary_report_path"] = result.summary_report_path
    payload["orchestration_json_path"] = result.orchestration_json_path
    payload["retried_count"] = sum(1 for stage in result.stage_results if stage.retry_count > 0)
    payload["metadata"] = {
        "start_time": result.started_at,
        "end_time": result.ended_at,
        "config": {
            "execution_mode": config.execution_mode,
            "max_retries": config.max_retries,
            "timeout": config.timeout_seconds,
            "parallel": config.parallel_execution,
            "continue_on_failure": config.continue_on_failure,
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="多Agent股票分析编排器（兼容包装器）")
    parser.add_argument("ticker", nargs="?", default="TSLA", help="股票代码（默认 TSLA）")
    parser.add_argument("--company", default="", help="公司名称（可选）")
    parser.add_argument("--max-retries", type=int, default=1, help="失败重试次数")
    parser.add_argument("--timeout", type=int, default=240, help="每阶段超时时间（秒）")
    parser.add_argument(
        "--execution-mode",
        choices=("command", "mock"),
        default=os.environ.get("ORCH_EXECUTION_MODE", "command"),
        help="执行模式",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    result = analyze_stock_with_retry(
        ticker=args.ticker,
        company=args.company,
        max_retries=args.max_retries,
        timeout=args.timeout,
        execution_mode=args.execution_mode,
        project_root=args.project_root,
    )

    print("=== 多Agent分析结果 ===")
    print(f"状态: {result['status']}")
    print(f"成功: {result['completed_count']}/{result['total_count']}")
    print(f"重试: {result['retried_count']}")
    print(f"综合报告: {result.get('summary_report_path') or 'N/A'}")
    print(f"编排JSON: {result.get('orchestration_json_path') or 'N/A'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
