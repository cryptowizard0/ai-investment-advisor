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
    config = OrchestrationConfig(
        execution_mode=kwargs.get(
            "execution_mode",
            os.environ.get("ORCH_EXECUTION_MODE", "command"),
        ),
        max_retries=max_retries,
        timeout_seconds=timeout,
        parallel_execution=kwargs.get("parallel_execution", True),
        continue_on_failure=kwargs.get("continue_on_failure", True),
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
