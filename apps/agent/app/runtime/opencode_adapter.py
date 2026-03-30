from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models import AnalysisJobRequest, AnalysisResult, Artifact, JobEvent, ReportSummary
from app.runtime.task_router import resolve_skill_profile


DEFAULT_MODEL = "openrouter/openai/gpt-5-mini"
DEFAULT_TIMEOUT_SECONDS = 300
MAX_REPORTED_EVENTS = 48
MAX_SUMMARY_LENGTH = 220


@dataclass
class OpencodeWorkspace:
    run_dir: Path
    cli_workspace: Path
    config_root: Path
    data_root: Path
    cache_root: Path
    prompt_path: Path
    request_path: Path
    stdout_path: Path
    stderr_path: Path


@dataclass
class OpencodeExecution:
    final_text: str
    events: list[JobEvent]
    error_code: str | None = None
    error_message: str | None = None


class OpencodeAdapter:
    def __init__(self, workspace_root: str | None = None) -> None:
        self.workspace_root = Path(workspace_root or Path(__file__).resolve().parents[4])
        self.output_root = self.workspace_root / "output" / "web-agent-runs"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.skills_root = self.workspace_root / ".agents" / "skills"
        self.opencode_bin = Path(
            os.getenv("AGENT_OPENCODE_BIN", str(Path.home() / ".opencode" / "bin" / "opencode"))
        )
        self.model = os.getenv("AGENT_OPENCODE_MODEL", DEFAULT_MODEL)
        self.timeout_seconds = int(
            os.getenv("AGENT_OPENCODE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        )
        self.variant = os.getenv("AGENT_OPENCODE_VARIANT")

    def execute(self, request: AnalysisJobRequest) -> AnalysisResult:
        skills = resolve_skill_profile(
            analysis_mode=request.analysis_mode,
            target_value=request.target_value,
            preferred_profile=request.selected_skill_profile,
        )
        workspace = self._prepare_workspace(request, skills)
        base_events = [
            JobEvent(event="run.accepted", message=f"Agent accepted run {request.run_id}"),
            JobEvent(event="skill.selected", message=f"Selected skills: {', '.join(skills)}"),
        ]

        if not self.opencode_bin.exists():
            return self._build_failure_result(
                request=request,
                workspace=workspace,
                events=base_events,
                error_code="opencode_not_found",
                error_message=f"Opencode binary not found at {self.opencode_bin}",
            )

        execution = self._execute_opencode(request, skills, workspace)
        events = base_events + execution.events

        if execution.error_code:
            return self._build_failure_result(
                request=request,
                workspace=workspace,
                events=events,
                error_code=execution.error_code,
                error_message=execution.error_message or "Opencode execution failed",
            )

        report_payload = self._parse_report_payload(
            request=request,
            skills=skills,
            final_text=execution.final_text,
        )
        markdown_path = workspace.run_dir / "report.md"
        json_path = workspace.run_dir / "report.json"
        markdown_path.write_text(report_payload["markdown"], encoding="utf-8")
        json_path.write_text(
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        artifacts = [
            Artifact(kind="markdown", path=str(markdown_path)),
            Artifact(kind="json", path=str(json_path)),
            Artifact(kind="prompt", path=str(workspace.prompt_path)),
            Artifact(kind="stdout", path=str(workspace.stdout_path)),
        ]
        if workspace.stderr_path.exists():
            artifacts.append(Artifact(kind="stderr", path=str(workspace.stderr_path)))

        return AnalysisResult(
            run_id=request.run_id,
            status="completed",
            events=events + [JobEvent(event="run.completed", message="Report artifacts generated")],
            artifacts=artifacts,
            report_summary=ReportSummary(
                title=report_payload["title"],
                summary=report_payload["summary"],
                rating=report_payload["rating"],
                confidence=report_payload["confidence"],
            ),
            raw_markdown_path=str(markdown_path),
            raw_json_path=str(json_path),
        )

    def _prepare_workspace(
        self,
        request: AnalysisJobRequest,
        skills: list[str],
    ) -> OpencodeWorkspace:
        run_dir = self.output_root / request.run_id
        cli_workspace = run_dir / "workspace"
        config_root = run_dir / "xdg-config"
        data_root = run_dir / "xdg-data"
        cache_root = run_dir / "xdg-cache"

        for path in (run_dir, cli_workspace, config_root, data_root, cache_root):
            path.mkdir(parents=True, exist_ok=True)

        self._link_skills(cli_workspace)
        self._write_opencode_config(config_root)
        self._copy_auth_file(data_root)

        request_path = run_dir / "request.json"
        request_path.write_text(
            json.dumps(request.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        prompt_path = run_dir / "prompt.md"
        prompt_path.write_text(_build_prompt(request, skills), encoding="utf-8")

        stdout_path = run_dir / "opencode.stdout.jsonl"
        stderr_path = run_dir / "opencode.stderr.log"
        if stdout_path.exists():
            stdout_path.unlink()
        if stderr_path.exists():
            stderr_path.unlink()

        return OpencodeWorkspace(
            run_dir=run_dir,
            cli_workspace=cli_workspace,
            config_root=config_root,
            data_root=data_root,
            cache_root=cache_root,
            prompt_path=prompt_path,
            request_path=request_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )

    def _execute_opencode(
        self,
        request: AnalysisJobRequest,
        skills: list[str],
        workspace: OpencodeWorkspace,
    ) -> OpencodeExecution:
        command = [
            str(self.opencode_bin),
            "run",
            "--format",
            "json",
            "--dir",
            str(workspace.cli_workspace),
            "--model",
            self.model,
            workspace.prompt_path.read_text(encoding="utf-8"),
        ]
        if self.variant:
            command.extend(["--variant", self.variant])

        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = str(workspace.config_root)
        env["XDG_DATA_HOME"] = str(workspace.data_root)
        env["XDG_CACHE_HOME"] = str(workspace.cache_root)

        try:
            completed = subprocess.run(
                command,
                cwd=self.workspace_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            workspace.stdout_path.write_text(exc.stdout or "", encoding="utf-8")
            if exc.stderr:
                workspace.stderr_path.write_text(exc.stderr, encoding="utf-8")
            return OpencodeExecution(
                final_text="",
                events=[JobEvent(event="opencode.timeout", message="Opencode run timed out")],
                error_code="opencode_timeout",
                error_message=f"Opencode timed out after {self.timeout_seconds}s",
            )

        workspace.stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        if completed.stderr:
            workspace.stderr_path.write_text(completed.stderr, encoding="utf-8")

        events, final_text, error_code, error_message = self._parse_opencode_output(
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            skills=skills,
        )

        if completed.returncode != 0 and error_code is None:
            error_code = "opencode_exit_nonzero"
            error_message = (
                f"Opencode exited with code {completed.returncode}. "
                f"{_tail_text(completed.stderr or completed.stdout, 400)}"
            ).strip()
            events.append(
                JobEvent(
                    event="opencode.exit_nonzero",
                    message=f"Opencode exited with code {completed.returncode}",
                )
            )

        if not final_text and error_code is None:
            error_code = "opencode_empty_response"
            error_message = "Opencode did not return any final text."
            events.append(
                JobEvent(event="opencode.empty_response", message="No final text returned")
            )

        return OpencodeExecution(
            final_text=final_text,
            events=events[:MAX_REPORTED_EVENTS],
            error_code=error_code,
            error_message=error_message,
        )

    def _parse_opencode_output(
        self,
        stdout: str,
        stderr: str,
        skills: list[str],
    ) -> tuple[list[JobEvent], str, str | None, str | None]:
        events: list[JobEvent] = []
        text_parts: list[str] = []
        error_code: str | None = None
        error_message: str | None = None

        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                events.append(JobEvent(event="opencode.output", message=_truncate(line, 120)))
                continue

            event_type = str(payload.get("type", "unknown"))
            if event_type == "text":
                text_value = _extract_text_value(payload)
                if text_value:
                    text_parts.append(text_value)
                continue

            if event_type == "error":
                error_data = payload.get("error", {})
                error_code = str(error_data.get("name") or "opencode_error")
                error_message = _extract_error_message(error_data)
                events.append(
                    JobEvent(
                        event="opencode.error",
                        message=_truncate(f"{error_code}: {error_message}", 160),
                    )
                )
                continue

            message = _summarize_event(payload)
            if message:
                events.append(JobEvent(event=f"opencode.{event_type}", message=message))

        if stderr.strip():
            events.append(
                JobEvent(
                    event="opencode.stderr",
                    message=_truncate(_tail_text(stderr, 180), 160),
                )
            )

        if not text_parts and skills:
            events.append(
                JobEvent(
                    event="opencode.skill_context",
                    message=f"Skill context provided: {', '.join(skills)}",
                )
            )

        return events, "".join(text_parts).strip(), error_code, error_message

    def _parse_report_payload(
        self,
        request: AnalysisJobRequest,
        skills: list[str],
        final_text: str,
    ) -> dict[str, Any]:
        parsed = _extract_json_blob(final_text)
        title = f"{request.target_value} 深度分析报告"
        rating = "WATCH"
        confidence = 0.5
        markdown = final_text.strip()
        summary = ""

        if parsed is not None:
            title = str(parsed.get("title") or title)
            rating = _normalize_rating(parsed.get("rating"))
            confidence = _normalize_confidence(parsed.get("confidence"))
            markdown = str(parsed.get("markdown") or markdown).strip()
            summary = str(parsed.get("summary") or "").strip()
        else:
            confidence = 0.45

        if not markdown:
            markdown = _fallback_markdown(request, skills, final_text)

        summary = summary or _extract_summary_from_markdown(markdown)
        return {
            "run_id": request.run_id,
            "target": request.target_value,
            "skills": skills,
            "analysis_mode": request.analysis_mode,
            "title": title,
            "summary": summary,
            "rating": rating,
            "confidence": confidence,
            "markdown": markdown,
            "raw_response": final_text,
        }

    def _build_failure_result(
        self,
        request: AnalysisJobRequest,
        workspace: OpencodeWorkspace,
        events: list[JobEvent],
        error_code: str,
        error_message: str,
    ) -> AnalysisResult:
        artifacts = [Artifact(kind="prompt", path=str(workspace.prompt_path))]
        if workspace.stdout_path.exists():
            artifacts.append(Artifact(kind="stdout", path=str(workspace.stdout_path)))
        if workspace.stderr_path.exists():
            artifacts.append(Artifact(kind="stderr", path=str(workspace.stderr_path)))

        return AnalysisResult(
            run_id=request.run_id,
            status="failed",
            events=events + [JobEvent(event="run.failed", message=_truncate(error_message, 160))],
            artifacts=artifacts,
            report_summary=ReportSummary(
                title=f"{request.target_value} 分析失败",
                summary=_truncate(error_message, MAX_SUMMARY_LENGTH),
                rating="ERROR",
                confidence=0.0,
            ),
            error_code=error_code,
            error_message=error_message,
        )

    def _link_skills(self, cli_workspace: Path) -> None:
        local_agents_dir = cli_workspace / ".agents"
        local_agents_dir.mkdir(parents=True, exist_ok=True)
        local_skills_path = local_agents_dir / "skills"

        if local_skills_path.exists() or local_skills_path.is_symlink():
            if local_skills_path.is_symlink() or local_skills_path.is_file():
                local_skills_path.unlink()
            else:
                shutil.rmtree(local_skills_path)

        os.symlink(self.skills_root, local_skills_path, target_is_directory=True)

    def _write_opencode_config(self, config_root: Path) -> None:
        config_path = config_root / "opencode.json"
        config_payload = {
            "$schema": "https://opencode.ai/config.json",
            "plugin": [],
        }
        config_path.write_text(json.dumps(config_payload, indent=2), encoding="utf-8")

    def _copy_auth_file(self, data_root: Path) -> None:
        source = Path.home() / ".local" / "share" / "opencode" / "auth.json"
        if not source.exists():
            return

        target_dir = data_root / "opencode"
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / "auth.json")


def _build_prompt(request: AnalysisJobRequest, skills: list[str]) -> str:
    skill_lines = "\n".join(f"- .agents/skills/{skill}/SKILL.md" for skill in skills)
    return f"""你是投资分析 Agent。当前运行在一个隔离工作目录中，但可以读取本地 skill。

请优先阅读以下 skill 定义，并仅在必要时继续读取这些 skill 的 scripts 或 references：
{skill_lines}

任务上下文：
- 分析模式: {request.analysis_mode}
- 目标类型: {request.target_type}
- 目标: {request.target_value}
- 风险偏好: {request.risk_profile}
- 输出语言: {request.preferred_language}
- 用户问题: {request.question}

要求：
1. 使用上述 skill 作为分析方法来源，不要浏览无关项目文件。
2. 最终只输出一个 JSON 对象，不要加代码块，不要加解释性前后缀。
3. JSON 必须包含以下字段：
   - title: string
   - summary: string
   - rating: string
   - confidence: number between 0 and 1
   - markdown: string
4. markdown 必须是一份完整中文报告，至少包含这些二级标题：
   - 执行摘要
   - 核心结论
   - Skill 路由
   - 用户问题
   - 分析正文
   - 风险
   - 数据限制
5. 如果信息不足，请在 markdown 的“数据限制”部分明确写出，而不是跳过。
"""


def _extract_text_value(payload: dict[str, Any]) -> str:
    part = payload.get("part")
    if isinstance(part, dict):
        for key in ("text", "content", "message"):
            value = part.get(key)
            if isinstance(value, str):
                return value

    for key in ("text", "content", "message"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    nested = _find_named_text(payload)
    if nested:
        return nested

    for key, value in payload.items():
        if key in {"type", "sessionID", "id"}:
            continue
        nested = _find_fallback_text(value)
        if nested:
            return nested

    return ""


def _find_named_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "content", "message"):
            nested = value.get(key)
            if isinstance(nested, str):
                return nested
        for nested in value.values():
            result = _find_named_text(nested)
            if result:
                return result
    if isinstance(value, list):
        for nested in value:
            result = _find_named_text(nested)
            if result:
                return result
    return ""


def _find_fallback_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for nested in value.values():
            result = _find_fallback_text(nested)
            if result:
                return result
    if isinstance(value, list):
        for nested in value:
            result = _find_fallback_text(nested)
            if result:
                return result
    return ""


def _summarize_event(payload: dict[str, Any]) -> str:
    event_type = str(payload.get("type", "unknown"))
    if event_type == "step_start":
        return "Model step started"
    if event_type == "step_finish":
        return "Model step finished"
    if event_type == "tool_use":
        part = payload.get("part")
        if isinstance(part, dict):
            tool_name = part.get("tool")
            state = part.get("state")
            if isinstance(state, dict):
                status = state.get("status")
                error = state.get("error")
                if isinstance(tool_name, str) and isinstance(status, str):
                    if isinstance(error, str) and error:
                        return _truncate(f"{tool_name} {status}: {error}", 140)
                    return _truncate(f"{tool_name} {status}", 140)
            if isinstance(tool_name, str):
                return _truncate(f"{tool_name} tool used", 140)
        return "Tool used"
    if event_type == "session.updated":
        return "Session updated"
    if event_type == "assistant":
        return "Assistant response received"

    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("message", "summary", "status"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return _truncate(value, 140)

    for key in ("message", "summary", "status"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return _truncate(value, 140)

    return _truncate(event_type.replace("_", " "), 80)


def _extract_error_message(error_data: dict[str, Any]) -> str:
    data = error_data.get("data")
    if isinstance(data, dict):
        for key in ("message", "responseBody", "details"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    for key in ("message", "name"):
        value = error_data.get(key)
        if isinstance(value, str) and value:
            return value
    return "Unknown opencode error"


def _extract_json_blob(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(cleaned[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _fallback_markdown(
    request: AnalysisJobRequest,
    skills: list[str],
    final_text: str,
) -> str:
    stripped = final_text.strip() or "本次分析没有返回可解析的正文，请查看 opencode 原始输出。"
    return f"""# {request.target_value} 深度分析报告

## 执行摘要

{_truncate(stripped, 320)}

## 核心结论

- 当前输出未命中结构化 JSON，已将原始响应降级为报告正文。

## Skill 路由

- Selected profile: `{request.selected_skill_profile}`
- Resolved skills: `{", ".join(skills)}`

## 用户问题

{request.question}

## 分析正文

{stripped}

## 风险

- 当前为自动降级结果，需人工复核核心结论。

## 数据限制

- 上游模型未按要求返回结构化 JSON。
"""


def _extract_summary_from_markdown(markdown: str) -> str:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    collected: list[str] = []
    for line in lines:
        if line.startswith("#"):
            continue
        collected.append(line)
        if len(" ".join(collected)) >= MAX_SUMMARY_LENGTH:
            break
    summary = " ".join(collected).strip()
    return _truncate(summary or "分析已完成，但摘要为空。", MAX_SUMMARY_LENGTH)


def _normalize_rating(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "WATCH"
    return value.strip().upper()[:32]


def _normalize_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, number))


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _tail_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return "..." + text[-(limit - 3) :]
