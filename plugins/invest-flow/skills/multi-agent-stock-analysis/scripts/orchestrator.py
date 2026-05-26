#!/usr/bin/env python3
"""Prompt-plan helper for the Codex-native multi-agent stock analysis skill."""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from investflow_pipeline.models import OrchestrationConfig
from investflow_pipeline.runner import analyze_stock_sync


def analyze_stock_with_retry(
    ticker: str,
    company: str = "",
    max_retries: int = 1,
    timeout: int = 240,
    **kwargs: Any,
) -> Dict[str, Any]:
    _ = (max_retries, timeout)
    compatibility_config = kwargs.get("config")
    if not isinstance(compatibility_config, OrchestrationConfig):
        compatibility_config = OrchestrationConfig()
    if compatibility_config.execution_mode != "prompt":
        raise ValueError("外部执行模式已废弃；请在 Codex 会话中使用 prompt 编排")

    requested_mode = kwargs.get("execution_mode")
    if requested_mode not in (None, "prompt"):
        raise ValueError("外部执行模式已废弃；请在 Codex 会话中使用 prompt 编排")

    project_root = kwargs.get("project_root")
    if project_root is not None:
        project_root = Path(project_root)
    result = analyze_stock_sync(
        ticker,
        company,
        compatibility_config,
        project_root=project_root,
    )
    payload = result.to_dict()
    payload["summary_report_path"] = result.summary_report_path
    payload["orchestration_json_path"] = result.orchestration_json_path
    payload["prompt_plan_path"] = result.prompt_plan_path
    payload["retried_count"] = sum(1 for stage in result.stage_results if stage.retry_count > 0)
    payload["metadata"] = {
        "start_time": result.started_at,
        "end_time": result.ended_at,
        "config": {
            "execution_mode": compatibility_config.execution_mode,
            "parallel": compatibility_config.parallel_execution,
            "continue_on_failure": compatibility_config.continue_on_failure,
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="多Agent Codex Prompt 编排计划生成器")
    parser.add_argument("ticker", nargs="?", default="TSLA", help="股票代码（默认 TSLA）")
    parser.add_argument("--company", default="", help="公司名称（可选）")
    parser.add_argument(
        "--project-root",
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    result = analyze_stock_with_retry(
        ticker=args.ticker,
        company=args.company,
        project_root=args.project_root,
    )

    print("=== 多Agent Codex Prompt 编排计划 ===")
    print(f"状态: {result['status']}")
    print(f"待执行: {result['pending_count']}/{result['total_count']}")
    print(f"Prompt计划: {result.get('prompt_plan_path') or 'N/A'}")
    print(f"编排JSON: {result.get('orchestration_json_path') or 'N/A'}")
    print("")
    for index, stage in enumerate(result["stage_results"], start=1):
        print(f"{index}. {stage['prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
