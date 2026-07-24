from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    PARTIAL = "partial"


@dataclass
class CompanyProfile:
    one_liner: str = ""
    business_summary: str = ""
    core_products: List[str] = field(default_factory=list)
    revenue_model: str = ""
    customers_and_end_markets: List[str] = field(default_factory=list)
    technical_advantages: List[str] = field(default_factory=list)
    moat_assessment: str = ""
    industry_chain_position: str = ""
    ai_relevance: str = ""
    ai_value_chain_position: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    industry_position: str = ""
    key_uncertainties: List[str] = field(default_factory=list)
    pre_analysis_questions: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "one_liner": self.one_liner,
            "business_summary": self.business_summary,
            "core_products": list(self.core_products),
            "revenue_model": self.revenue_model,
            "customers_and_end_markets": list(self.customers_and_end_markets),
            "technical_advantages": list(self.technical_advantages),
            "moat_assessment": self.moat_assessment,
            "industry_chain_position": self.industry_chain_position,
            "ai_relevance": self.ai_relevance,
            "ai_value_chain_position": list(self.ai_value_chain_position),
            "competitors": list(self.competitors),
            "industry_position": self.industry_position,
            "key_uncertainties": list(self.key_uncertainties),
            "pre_analysis_questions": list(self.pre_analysis_questions),
            "data_sources": list(self.data_sources),
        }


@dataclass
class Handoff:
    conclusion: str = ""
    recommendation: str = ""
    confidence: Optional[int] = None
    key_evidence: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    contradiction_points: List[str] = field(default_factory=list)
    monitoring_signals: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)
    company_profile: Optional[CompanyProfile] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "key_evidence": list(self.key_evidence),
            "risk_flags": list(self.risk_flags),
            "contradiction_points": list(self.contradiction_points),
            "monitoring_signals": list(self.monitoring_signals),
            "data_gaps": list(self.data_gaps),
            "company_profile": (
                self.company_profile.to_dict() if self.company_profile else None
            ),
        }


@dataclass
class TaskRequest:
    task_id: str
    intent: str
    target: str
    ticker: str = ""
    company_name: str = ""
    market: str = "unknown"
    horizon: str = "mixed"
    requested_outputs: List[str] = field(default_factory=lambda: ["summary", "handoff_json"])


@dataclass
class SkillSpec:
    skill_name: str
    agent_name: str
    stage: str
    prompt_template: str
    output_dir: str
    required: bool = False
    extractor_type: str = "markdown"


@dataclass
class StageResult:
    skill_name: str
    agent_name: str
    status: AnalysisStatus
    output: str = ""
    report_path: Optional[str] = None
    handoff: Handoff = field(default_factory=Handoff)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    retry_count: int = 0
    prompt: str = ""

    @property
    def is_success(self) -> bool:
        return self.status == AnalysisStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "report_path": self.report_path,
            "handoff": self.handoff.to_dict(),
            "errors": list(self.errors),
            "duration": self.duration,
            "retry_count": self.retry_count,
            "prompt": self.prompt,
        }


@dataclass
class OrchestrationConfig:
    execution_mode: str = "prompt"
    parallel_execution: bool = True
    continue_on_failure: bool = True


@dataclass
class PipelineResult:
    task_id: str
    status: str
    intent: str
    target: str
    ticker: str
    company_name: str
    started_at: str
    ended_at: str
    stage_results: List[StageResult]
    summary_report_path: Optional[str]
    orchestration_json_path: Optional[str]
    prompt_plan_path: Optional[str] = None
    failed_required: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        success_count = sum(1 for result in self.stage_results if result.is_success)
        failed_count = sum(
            1 for result in self.stage_results if result.status == AnalysisStatus.FAILED
        )
        pending_count = sum(
            1 for result in self.stage_results if result.status == AnalysisStatus.PENDING
        )
        stage_results = [result.to_dict() for result in self.stage_results]
        return {
            "task_id": self.task_id,
            "status": self.status,
            "intent": self.intent,
            "target": self.target,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "completed_count": success_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "total_count": len(self.stage_results),
            "summary_report_path": self.summary_report_path,
            "orchestration_json_path": self.orchestration_json_path,
            "prompt_plan_path": self.prompt_plan_path,
            "failed_required": list(self.failed_required),
            "warnings": list(self.warnings),
            "stage_results": stage_results,
            "agents": {result["agent_name"]: result for result in stage_results},
        }
