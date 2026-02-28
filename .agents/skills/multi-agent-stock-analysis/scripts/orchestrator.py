#!/usr/bin/env python3
"""
多Agent股票分析编排器 - 带失败重试机制（命令驱动版）

默认执行模式:
- command: 真实执行外部命令（默认）
- mock: 本地模拟（仅用于调试）
"""

import argparse
import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _safe_read_text(file_path: Path) -> str:
    if not file_path.exists() or not file_path.is_file():
        return ""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    PARTIAL = "partial"


@dataclass
class SubAgentResult:
    """SubAgent执行结果"""

    agent_name: str
    status: AnalysisStatus
    output: Optional[str] = None
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    key_findings: Dict[str, Any] = field(default_factory=dict)
    key_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "report_path": self.report_path,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "key_findings": self.key_findings,
            "key_metrics": self.key_metrics,
        }

    @property
    def is_success(self) -> bool:
        return self.status == AnalysisStatus.SUCCESS

    @property
    def is_empty(self) -> bool:
        return not self.output or len(self.output.strip()) < 100


@dataclass
class OrchestrationConfig:
    max_retries: int = 1
    retry_on_empty: bool = True
    retry_on_timeout: bool = True
    timeout_seconds: int = 240
    parallel_execution: bool = True
    fail_fast: bool = False
    continue_on_failure: bool = True
    execution_mode: str = "command"  # command | mock


class AgentExecutor:
    """Agent执行器 - 带重试逻辑"""

    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=3)

    def _validate_result(self, result: SubAgentResult) -> Tuple[bool, str]:
        if result.status == AnalysisStatus.FAILED:
            return False, f"执行失败: {result.error_message}"

        content = result.output or ""
        if result.report_path:
            report_text = _safe_read_text(Path(result.report_path))
            if not report_text:
                return False, f"报告文件不可读或为空: {result.report_path}"
            content = report_text

        if len(content.strip()) < 200:
            return False, "输出内容不完整"

        required_keywords = ["分析", "报告", "结论"]
        if not any(kw in content for kw in required_keywords):
            return False, "输出缺少关键内容标识"

        return True, ""

    async def execute_with_retry(
        self, agent_name: str, execute_fn: Callable[[], SubAgentResult]
    ) -> SubAgentResult:
        last_result: Optional[SubAgentResult] = None

        for attempt in range(self.config.max_retries + 1):
            attempt_start = datetime.now()
            is_retry = attempt > 0

            if is_retry:
                logger.warning("[%s] 第%d次重试...", agent_name, attempt)

            try:
                logger.info("[%s] 开始执行 (attempt %d)", agent_name, attempt + 1)
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, execute_fn),
                    timeout=self.config.timeout_seconds,
                )

                result.agent_name = agent_name
                result.retry_count = attempt
                result.execution_time = (datetime.now() - attempt_start).total_seconds()

                is_valid, fail_reason = self._validate_result(result)
                if is_valid:
                    logger.info("[%s] 执行成功 (耗时%.1fs)", agent_name, result.execution_time)
                    return result

                logger.warning("[%s] 结果验证失败: %s", agent_name, fail_reason)
                result.error_message = fail_reason
                last_result = result

                if attempt < self.config.max_retries:
                    continue
                break

            except asyncio.TimeoutError:
                error_msg = f"执行超时 (>{self.config.timeout_seconds}s)"
                logger.error("[%s] %s", agent_name, error_msg)
                last_result = SubAgentResult(
                    agent_name=agent_name,
                    status=AnalysisStatus.FAILED,
                    error_message=error_msg,
                    retry_count=attempt,
                    execution_time=(datetime.now() - attempt_start).total_seconds(),
                )
                if attempt < self.config.max_retries and self.config.retry_on_timeout:
                    continue
                break

            except Exception as exc:
                error_msg = f"执行异常: {exc}"
                logger.error("[%s] %s", agent_name, error_msg)
                last_result = SubAgentResult(
                    agent_name=agent_name,
                    status=AnalysisStatus.FAILED,
                    error_message=error_msg,
                    retry_count=attempt,
                    execution_time=(datetime.now() - attempt_start).total_seconds(),
                )
                if attempt < self.config.max_retries:
                    continue
                break

        if last_result:
            last_result.status = AnalysisStatus.FAILED
            return last_result

        return SubAgentResult(
            agent_name=agent_name,
            status=AnalysisStatus.FAILED,
            error_message="未知错误",
            retry_count=self.config.max_retries,
        )


class MultiAgentOrchestrator:
    """多Agent编排器主类"""

    DEFAULT_COMMANDS = {
        "fundamental": 'opencode run "/fundamental-analysis {ticker}" --format default',
        "institutional": (
            'opencode run "/institutional-accumulation-analysis {ticker}" --format default'
        ),
        "gie": 'opencode run "/gie-investment-framework {ticker}" --format default',
    }

    ENV_COMMAND_MAP = {
        "fundamental": "ORCH_FUNDAMENTAL_CMD",
        "institutional": "ORCH_INSTITUTIONAL_CMD",
        "gie": "ORCH_GIE_CMD",
    }

    def __init__(self, config: Optional[OrchestrationConfig] = None):
        self.config = config or OrchestrationConfig()
        self.agent_executor = AgentExecutor(self.config)
        # .../scripts/orchestrator.py -> 项目根目录
        self.project_root = Path(__file__).resolve().parents[4]
        self.output_dir = self.project_root / "output"

    def _resolve_command_template(self, agent_name: str) -> str:
        env_key = self.ENV_COMMAND_MAP.get(agent_name)
        if env_key and os.environ.get(env_key):
            return os.environ[env_key]
        return self.DEFAULT_COMMANDS.get(agent_name, "")

    def _format_command(self, template: str, ticker: str, company: str) -> str:
        return template.format(ticker=ticker, company=company or "")

    def _run_command(self, command: str) -> str:
        if not command.strip():
            raise RuntimeError("空命令，无法执行")

        logger.info("执行命令: %s", command)
        args = shlex.split(command)
        completed = subprocess.run(
            args,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )

        combined_output = "\n".join(
            [part for part in [completed.stdout, completed.stderr] if part]
        ).strip()

        if completed.returncode != 0:
            excerpt = (combined_output or "").strip()[:1000]
            raise RuntimeError(
                f"命令执行失败 (exit={completed.returncode})"
                + (f": {excerpt}" if excerpt else "")
            )

        return combined_output

    def _find_report_from_output(self, output: str) -> Optional[Path]:
        if not output:
            return None

        # 先匹配包含 output 目录的路径，兼容中英文文件名及括号
        patterns = [
            r"([./\w\-\u4e00-\u9fff()]+/output/[^\s\"'`]+\.md)",
            r"(\.?/output/[^\s\"'`]+\.md)",
            r"(/[^ \n\t\"'`]+\.md)",
        ]
        for pattern in patterns:
            for match in re.findall(pattern, output):
                path = Path(match)
                if not path.is_absolute():
                    path = (self.project_root / path).resolve()
                if path.exists() and path.is_file():
                    return path
        return None

    def _find_latest_report(
        self, output_dir: Path, ticker: str, started_at: datetime
    ) -> Optional[Path]:
        if not output_dir.exists():
            return None

        ticker_upper = ticker.upper()
        threshold_ts = started_at.timestamp() - 5
        candidates = [
            p
            for p in output_dir.glob("*.md")
            if p.is_file()
            and ticker_upper in p.name.upper()
            and p.stat().st_mtime >= threshold_ts
        ]
        if not candidates:
            candidates = [
                p
                for p in output_dir.glob("*.md")
                if p.is_file() and p.stat().st_mtime >= threshold_ts
            ]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _resolve_report_path(
        self,
        agent_def: Dict[str, Any],
        ticker: str,
        command_output: str,
        started_at: datetime,
    ) -> Optional[str]:
        by_output = self._find_report_from_output(command_output)
        if by_output:
            return str(by_output)

        output_dir = (self.project_root / agent_def["output_dir"]).resolve()
        latest = self._find_latest_report(output_dir, ticker, started_at)
        return str(latest) if latest else None

    def _get_agent_definitions(self, ticker: str, company: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fundamental",
                "skill": "fundamental-analysis",
                "description": f"基本面分析 - {ticker}",
                "priority": 1,
                "required": True,
                "output_dir": "output/fundamental-analysis",
                "command_template": self._resolve_command_template("fundamental"),
            },
            {
                "name": "institutional",
                "skill": "institutional-accumulation-analysis",
                "description": f"机构吸筹派发分析 - {ticker}",
                "priority": 2,
                "required": False,
                "output_dir": "output/institutional-accumulation-analysis",
                "command_template": self._resolve_command_template("institutional"),
            },
            {
                "name": "gie",
                "skill": "gie-investment-framework",
                "description": f"GIE投资框架分析 - {ticker}",
                "priority": 3,
                "required": True,
                "output_dir": "output/gie-investment-framework",
                "command_template": self._resolve_command_template("gie"),
            },
        ]

    async def _execute_subagent(
        self, agent_def: Dict[str, Any], ticker: str, company: str
    ) -> SubAgentResult:
        agent_name = agent_def["name"]

        def execute_fn() -> SubAgentResult:
            started_at = datetime.now()
            if self.config.execution_mode == "mock":
                import time

                logger.info("[mock] 调用 %s skill 分析 %s", agent_name, ticker)
                time.sleep(1)
                mock_output = (
                    f"{agent_name} 分析报告\n\n"
                    f"这是 {ticker} 的 mock 分析内容，用于验证编排器重试、并行和结果聚合流程。"
                    "结论：当前为调试模式，不代表真实投资建议。"
                )
                return SubAgentResult(
                    agent_name=agent_name,
                    status=AnalysisStatus.SUCCESS,
                    output=mock_output * 4,
                    report_path=None,
                    key_findings={"execution_mode": "mock"},
                    key_metrics={},
                )

            template = agent_def.get("command_template", "").strip()
            if not template:
                return SubAgentResult(
                    agent_name=agent_name,
                    status=AnalysisStatus.FAILED,
                    error_message="未配置执行命令（command_template）",
                )

            command = self._format_command(template, ticker, company)
            output = self._run_command(command)
            report_path = self._resolve_report_path(agent_def, ticker, output, started_at)
            if not report_path:
                return SubAgentResult(
                    agent_name=agent_name,
                    status=AnalysisStatus.FAILED,
                    output=output,
                    error_message="命令执行完成，但未定位到输出报告文件",
                    key_findings={"command": command},
                )

            report_text = _safe_read_text(Path(report_path))
            return SubAgentResult(
                agent_name=agent_name,
                status=AnalysisStatus.SUCCESS,
                output=report_text or output,
                report_path=report_path,
                key_findings={"command": command},
                key_metrics={},
            )

        return await self.agent_executor.execute_with_retry(agent_name, execute_fn)

    async def analyze_stock(
        self, ticker: str, company: str = "", custom_agents: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("开始多Agent分析: %s", ticker)
        logger.info(
            "配置: mode=%s, 重试=%d, 超时=%ds",
            self.config.execution_mode,
            self.config.max_retries,
            self.config.timeout_seconds,
        )
        logger.info("=" * 60)

        start_time = datetime.now()
        agents = custom_agents or self._get_agent_definitions(ticker, company)

        tasks = [(agent_def, self._execute_subagent(agent_def, ticker, company)) for agent_def in agents]
        results: List[SubAgentResult] = []
        failed_required: List[str] = []

        if self.config.parallel_execution:
            coroutines = [task for _, task in tasks]
            agent_defs = [agent_def for agent_def, _ in tasks]
            completed_results = await asyncio.gather(*coroutines, return_exceptions=True)

            for agent_def, result in zip(agent_defs, completed_results):
                if isinstance(result, Exception):
                    results.append(
                        SubAgentResult(
                            agent_name=agent_def["name"],
                            status=AnalysisStatus.FAILED,
                            error_message=str(result),
                        )
                    )
                    if agent_def.get("required", False):
                        failed_required.append(agent_def["name"])
                else:
                    results.append(result)
                    if not result.is_success and agent_def.get("required", False):
                        failed_required.append(agent_def["name"])
        else:
            for agent_def, task in tasks:
                result = await task
                results.append(result)
                if not result.is_success and agent_def.get("required", False):
                    failed_required.append(agent_def["name"])

        if failed_required and not self.config.continue_on_failure:
            raise RuntimeError(f"必要分析失败: {failed_required}")

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        success_count = sum(1 for r in results if r.is_success)
        failed_count = len(results) - success_count
        retried_count = sum(1 for r in results if r.retry_count > 0)

        if failed_count == 0:
            overall_status = "success"
        elif success_count > 0:
            overall_status = "partial_success"
        else:
            overall_status = "failed"

        aggregated_result = {
            "task_id": f"ma_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "ticker": ticker,
            "company_name": company,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "status": overall_status,
            "completed_count": success_count,
            "failed_count": failed_count,
            "total_count": len(results),
            "retried_count": retried_count,
            "agents": {r.agent_name: r.to_dict() for r in results},
            "failed_required": failed_required,
            "metadata": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "project_root": str(self.project_root),
                "config": {
                    "execution_mode": self.config.execution_mode,
                    "max_retries": self.config.max_retries,
                    "timeout": self.config.timeout_seconds,
                    "parallel": self.config.parallel_execution,
                },
            },
        }

        await self._save_results(ticker, aggregated_result)
        logger.info("分析完成: %d/%d 成功, %d 次重试", success_count, len(results), retried_count)
        return aggregated_result

    async def _save_results(self, ticker: str, result: Dict[str, Any]) -> None:
        summary_dir = self.output_dir / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)
        report_path = summary_dir / f"orchestration-{ticker}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("编排结果已保存: %s", report_path)


def analyze_stock_with_retry(
    ticker: str, company: str = "", max_retries: int = 1, timeout: int = 240, **kwargs: Any
) -> Dict[str, Any]:
    config = OrchestrationConfig(max_retries=max_retries, timeout_seconds=timeout, **kwargs)
    orchestrator = MultiAgentOrchestrator(config)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(orchestrator.analyze_stock(ticker, company))
    finally:
        loop.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多Agent股票分析编排器")
    parser.add_argument("ticker", nargs="?", default="TSLA")
    parser.add_argument("--company", default="")
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--execution-mode",
        choices=["command", "mock"],
        default=os.environ.get("ORCH_EXECUTION_MODE", "command"),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("多Agent股票分析编排器 - 失败重试机制")
    print("=" * 60)

    result = analyze_stock_with_retry(
        ticker=args.ticker,
        company=args.company,
        max_retries=args.max_retries,
        timeout=args.timeout,
        execution_mode=args.execution_mode,
    )

    print("\n分析结果:")
    print(f"  状态: {result['status']}")
    print(f"  成功: {result['completed_count']}/{result['total_count']}")
    print(f"  重试: {result['retried_count']} 次")
    print(f"  耗时: {result['metadata']['total_duration']:.1f}s")
