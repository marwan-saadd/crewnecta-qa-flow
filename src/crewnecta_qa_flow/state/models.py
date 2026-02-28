"""Pydantic state models for the QA Auditor Flow.

All structured data flows through these models. QAAuditorState is the
central state object that tells the full story: inputs → enrichments →
decisions → outputs.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ComplianceSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NONE = "none"


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class InteractionTranscript(BaseModel):
    interaction_id: str
    agent_id: str
    agent_name: str
    channel: str  # "voice", "chat", "email"
    timestamp: str
    duration_seconds: Optional[int] = None
    transcript_text: str
    customer_issue: str = ""
    resolution_status: str = ""


# ---------------------------------------------------------------------------
# Enrichment models
# ---------------------------------------------------------------------------

class RiskScore(BaseModel):
    interaction_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str] = Field(default_factory=list)
    priority_for_review: str  # "high", "medium", "low"


class QAEvaluation(BaseModel):
    interaction_id: str
    agent_id: str
    compliance_score: float = Field(ge=0, le=100)
    empathy_score: float = Field(ge=0, le=100)
    resolution_score: float = Field(ge=0, le=100)
    process_adherence_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    compliance_issues: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    compliance_severity: ComplianceSeverity = ComplianceSeverity.NONE


class PatternInsight(BaseModel):
    pattern_type: str  # "agent_specific", "systemic", "script_issue", "training_gap"
    description: str
    affected_agents: list[str] = Field(default_factory=list)
    frequency: str = ""
    evidence_interaction_ids: list[str] = Field(default_factory=list)
    recommended_action: str = ""


class CoachingPlan(BaseModel):
    agent_id: str
    agent_name: str
    overall_performance: str  # "exceeds", "meets", "below", "critical"
    key_strengths: list[str] = Field(default_factory=list)
    priority_improvements: list[str] = Field(default_factory=list)
    specific_examples: list[str] = Field(default_factory=list)
    suggested_training: list[str] = Field(default_factory=list)
    follow_up_timeline: str = ""


# ---------------------------------------------------------------------------
# Wrapper output models (used as output_pydantic for CrewAI tasks)
# ---------------------------------------------------------------------------

class RiskScoreOutput(BaseModel):
    """Wrapper for a single risk-scoring task output."""
    interaction_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str] = Field(default_factory=list)
    priority_for_review: str  # "high", "medium", "low"


class QAEvaluationOutput(BaseModel):
    """Wrapper for QA analysis task output (compliance + quality combined)."""
    interaction_id: str
    agent_id: str
    compliance_score: float = Field(ge=0, le=100)
    empathy_score: float = Field(ge=0, le=100)
    resolution_score: float = Field(ge=0, le=100)
    process_adherence_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    compliance_issues: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    compliance_severity: str = "none"  # str for easier LLM output


class PatternInsightsOutput(BaseModel):
    """Wrapper for pattern analysis task output."""
    insights: list[PatternInsight] = Field(default_factory=list)
    agents_needing_coaching: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Central flow state
# ---------------------------------------------------------------------------

class QAAuditorState(BaseModel):
    # --- INPUTS ---
    raw_transcripts: list[InteractionTranscript] = Field(default_factory=list)
    campaign_name: str = ""
    evaluation_period: str = ""
    compliance_requirements: list[str] = Field(default_factory=list)

    # --- ENRICHMENTS ---
    risk_scores: list[RiskScore] = Field(default_factory=list)
    qa_evaluations: list[QAEvaluation] = Field(default_factory=list)
    pattern_insights: list[PatternInsight] = Field(default_factory=list)
    average_scores: dict = Field(default_factory=dict)

    # --- DECISIONS ---
    has_critical_violations: bool = False
    critical_violations: list[dict] = Field(default_factory=list)
    agents_needing_coaching: list[str] = Field(default_factory=list)

    # --- OUTPUTS ---
    coaching_plans: list[CoachingPlan] = Field(default_factory=list)
    compliance_escalation_report: str = ""
    executive_summary: str = ""
    detailed_qa_report: str = ""

    # --- ERROR TRACKING ---
    errors: list[str] = Field(default_factory=list)
    processing_status: str = "pending"
    transcripts_processed: int = 0
    transcripts_failed: int = 0
