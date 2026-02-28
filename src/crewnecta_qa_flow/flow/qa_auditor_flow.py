"""QA Auditor Flow — main orchestration for the BPO QA pipeline.

Steps:
  1. ingest_and_risk_score   — Risk Scorer scans ALL transcripts
  2. deep_qa_analysis        — Compliance Auditor + Quality Evaluator on HIGH/MEDIUM
  3. route_by_compliance     — Router: CRITICAL → escalation, else standard
  4a. handle_compliance_escalation — Build urgent escalation report
  4b/5. detect_patterns      — Pattern Analyst finds systemic issues
  6. generate_coaching_plans — Coaching Architect per agent
  7. compile_final_report    — Aggregate executive summary + detailed report
"""

import json
import os
import re
from datetime import datetime

from crewai.flow.flow import Flow, listen, or_, router, start

from crewnecta_qa_flow.state.models import (
    ComplianceSeverity,
    CoachingPlan,
    PatternInsight,
    QAEvaluation,
    QAAuditorState,
    RiskScore,
)
from crewnecta_qa_flow.crews.risk_scoring.risk_scoring_crew import RiskScoringCrew
from crewnecta_qa_flow.crews.qa_analysis.qa_analysis_crew import QAAnalysisCrew
from crewnecta_qa_flow.crews.pattern_analysis.pattern_analysis_crew import PatternAnalysisCrew
from crewnecta_qa_flow.crews.coaching.coaching_crew import CoachingCrew


def _parse_json_safe(raw: str) -> dict | None:
    """Try to extract and parse JSON from raw LLM output, handling common issues."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting JSON block from markdown fences or surrounding text
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"(\{.*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    return None


class QAAuditorFlow(Flow[QAAuditorState]):
    """Main QA auditor flow that orchestrates the full pipeline."""

    # Set before kickoff to seed state with initial data
    initial_state: QAAuditorState | None = None

    # ------------------------------------------------------------------
    # Step 1: Risk scoring
    # Reads:  raw_transcripts
    # Writes: risk_scores, transcripts_processed, transcripts_failed
    # ------------------------------------------------------------------
    @start()
    def ingest_and_risk_score(self):
        """Score ALL transcripts for risk priority using the Risk Scoring Crew."""

        # Populate state from initial_state if provided (use getattr
        # instead of model_dump to preserve Pydantic objects like
        # InteractionTranscript instead of converting them to dicts)
        if self.initial_state is not None:
            for field_name in self.initial_state.model_fields:
                setattr(self.state, field_name, getattr(self.initial_state, field_name))

        print(f"\n{'='*60}")
        print("STEP 1: Risk Scoring — scanning all transcripts")
        print(f"{'='*60}")

        if not self.state.raw_transcripts:
            self.state.errors.append("No transcripts provided for analysis")
            self.state.processing_status = "failed_no_input"
            return

        for transcript in self.state.raw_transcripts:
            try:
                result = RiskScoringCrew().crew().kickoff(
                    inputs={
                        "interaction_id": transcript.interaction_id,
                        "channel": transcript.channel,
                        "agent_name": transcript.agent_name,
                        "agent_id": transcript.agent_id,
                        "transcript_text": transcript.transcript_text,
                    }
                )

                # Parse structured output (try pydantic first, then raw JSON)
                parsed = None
                if result.pydantic:
                    parsed = result.pydantic.model_dump() if hasattr(result.pydantic, 'model_dump') else vars(result.pydantic)
                else:
                    parsed = _parse_json_safe(result.raw)

                if parsed:
                    self.state.risk_scores.append(
                        RiskScore(
                            interaction_id=parsed.get("interaction_id", transcript.interaction_id),
                            risk_score=float(parsed.get("risk_score", 0.5)),
                            risk_factors=parsed.get("risk_factors", []),
                            priority_for_review=parsed.get("priority_for_review", "medium"),
                        )
                    )
                else:
                    raise ValueError(f"Could not parse risk score output: {result.raw[:200]}")

                self.state.transcripts_processed += 1
                print(f"  ✓ Scored {transcript.interaction_id}")

            except Exception as e:
                self.state.errors.append(
                    f"Failed to risk-score {transcript.interaction_id}: {str(e)}"
                )
                self.state.transcripts_failed += 1
                # Assign default medium risk so transcript isn't lost
                self.state.risk_scores.append(
                    RiskScore(
                        interaction_id=transcript.interaction_id,
                        risk_score=0.5,
                        risk_factors=["error_during_scoring"],
                        priority_for_review="medium",
                    )
                )
                print(f"  ✗ Failed {transcript.interaction_id}: {e}")
                continue

        # Sort by risk score descending
        self.state.risk_scores.sort(key=lambda r: r.risk_score, reverse=True)
        print(f"\nRisk scoring complete: {self.state.transcripts_processed} processed, "
              f"{self.state.transcripts_failed} failed")

    # ------------------------------------------------------------------
    # Step 2: Deep QA analysis
    # Reads:  risk_scores, raw_transcripts
    # Writes: qa_evaluations, average_scores
    # ------------------------------------------------------------------
    @listen(ingest_and_risk_score)
    def deep_qa_analysis(self):
        """Run compliance + quality analysis on HIGH and MEDIUM priority transcripts."""
        print(f"\n{'='*60}")
        print("STEP 2: Deep QA Analysis — compliance + quality evaluation")
        print(f"{'='*60}")

        if not self.state.risk_scores:
            self.state.errors.append("No risk scores available for QA analysis")
            return

        # Build lookup for transcripts
        transcript_map = {
            t.interaction_id: t for t in self.state.raw_transcripts
        }

        for risk in self.state.risk_scores:
            transcript = transcript_map.get(risk.interaction_id)
            if not transcript:
                self.state.errors.append(
                    f"Transcript {risk.interaction_id} not found for QA analysis"
                )
                continue

            if risk.priority_for_review == "low":
                # LOW priority: default pass scores (minimal review)
                self.state.qa_evaluations.append(
                    QAEvaluation(
                        interaction_id=risk.interaction_id,
                        agent_id=transcript.agent_id,
                        compliance_score=85.0,
                        empathy_score=75.0,
                        resolution_score=80.0,
                        process_adherence_score=80.0,
                        overall_score=80.0,
                        compliance_issues=[],
                        strengths=["Low risk — passed automated screening"],
                        improvement_areas=[],
                        compliance_severity=ComplianceSeverity.NONE,
                    )
                )
                print(f"  ○ {risk.interaction_id} — LOW priority, default pass")
                continue

            # HIGH or MEDIUM: full QA analysis
            try:
                result = QAAnalysisCrew().crew().kickoff(
                    inputs={
                        "interaction_id": transcript.interaction_id,
                        "channel": transcript.channel,
                        "agent_name": transcript.agent_name,
                        "agent_id": transcript.agent_id,
                        "transcript_text": transcript.transcript_text,
                        "customer_issue": transcript.customer_issue,
                        "resolution_status": transcript.resolution_status,
                    }
                )

                # Parse structured output (try pydantic first, then raw JSON)
                parsed = None
                if result.pydantic:
                    parsed = result.pydantic.model_dump() if hasattr(result.pydantic, 'model_dump') else vars(result.pydantic)
                else:
                    parsed = _parse_json_safe(result.raw)

                if not parsed:
                    raise ValueError(f"Could not parse QA output: {result.raw[:200]}")

                # Map severity string to enum
                sev_str = str(parsed.get("compliance_severity", "none")).lower()
                try:
                    severity = ComplianceSeverity(sev_str)
                except ValueError:
                    severity = ComplianceSeverity.NONE

                self.state.qa_evaluations.append(
                    QAEvaluation(
                        interaction_id=parsed.get("interaction_id", transcript.interaction_id),
                        agent_id=parsed.get("agent_id", transcript.agent_id),
                        compliance_score=float(parsed.get("compliance_score", 50)),
                        empathy_score=float(parsed.get("empathy_score", 50)),
                        resolution_score=float(parsed.get("resolution_score", 50)),
                        process_adherence_score=float(parsed.get("process_adherence_score", 50)),
                        overall_score=float(parsed.get("overall_score", 50)),
                        compliance_issues=parsed.get("compliance_issues", []),
                        strengths=parsed.get("strengths", []),
                        improvement_areas=parsed.get("improvement_areas", []),
                        compliance_severity=severity,
                    )
                )

                print(f"  ✓ Analyzed {risk.interaction_id} ({risk.priority_for_review} priority)")

            except Exception as e:
                self.state.errors.append(
                    f"Failed QA analysis for {risk.interaction_id}: {str(e)}"
                )
                # Graceful degradation: add default evaluation
                self.state.qa_evaluations.append(
                    QAEvaluation(
                        interaction_id=risk.interaction_id,
                        agent_id=transcript.agent_id,
                        compliance_score=50.0,
                        empathy_score=50.0,
                        resolution_score=50.0,
                        process_adherence_score=50.0,
                        overall_score=50.0,
                        compliance_issues=["evaluation_failed"],
                        strengths=[],
                        improvement_areas=["Unable to evaluate — review manually"],
                        compliance_severity=ComplianceSeverity.NONE,
                    )
                )
                print(f"  ✗ Failed {risk.interaction_id}: {e}")
                continue

        # Compute average scores
        if self.state.qa_evaluations:
            evals = self.state.qa_evaluations
            n = len(evals)
            self.state.average_scores = {
                "compliance": round(sum(e.compliance_score for e in evals) / n, 1),
                "empathy": round(sum(e.empathy_score for e in evals) / n, 1),
                "resolution": round(sum(e.resolution_score for e in evals) / n, 1),
                "process_adherence": round(
                    sum(e.process_adherence_score for e in evals) / n, 1
                ),
                "overall": round(sum(e.overall_score for e in evals) / n, 1),
            }

        print(f"\nQA analysis complete. Average overall score: "
              f"{self.state.average_scores.get('overall', 'N/A')}")

    # ------------------------------------------------------------------
    # Step 3: Conditional router
    # Reads:  qa_evaluations
    # Writes: has_critical_violations, critical_violations
    # ------------------------------------------------------------------
    @router(deep_qa_analysis)
    def route_by_compliance(self):
        """Route based on compliance severity: escalation or standard path."""
        print(f"\n{'='*60}")
        print("STEP 3: Compliance Router — checking for critical violations")
        print(f"{'='*60}")

        critical = [
            e for e in self.state.qa_evaluations
            if e.compliance_severity == ComplianceSeverity.CRITICAL
        ]

        if critical:
            self.state.has_critical_violations = True
            self.state.critical_violations = [
                {
                    "interaction_id": e.interaction_id,
                    "agent_id": e.agent_id,
                    "issues": e.compliance_issues,
                }
                for e in critical
            ]
            print(f"  ⚠ CRITICAL violations found in {len(critical)} interaction(s)")
            print(f"  → Routing to COMPLIANCE ESCALATION")
            return "compliance_escalation"

        print("  ✓ No critical violations — standard analysis path")
        return "standard_analysis"

    # ------------------------------------------------------------------
    # Step 4a: Compliance escalation (inline — no crew needed)
    # Reads:  critical_violations, qa_evaluations
    # Writes: compliance_escalation_report
    # ------------------------------------------------------------------
    @listen("compliance_escalation")
    def handle_compliance_escalation(self):
        """Build urgent compliance escalation report from state."""
        print(f"\n{'='*60}")
        print("STEP 4a: Compliance Escalation — generating urgent report")
        print(f"{'='*60}")

        lines = [
            "═══════════════════════════════════════════════════════════",
            "       URGENT COMPLIANCE ESCALATION REPORT",
            "═══════════════════════════════════════════════════════════",
            f"Campaign: {self.state.campaign_name}",
            f"Period: {self.state.evaluation_period}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Critical Violations: {len(self.state.critical_violations)}",
            "",
        ]

        for i, violation in enumerate(self.state.critical_violations, 1):
            lines.append(f"--- Violation #{i} ---")
            lines.append(f"  Interaction: {violation['interaction_id']}")
            lines.append(f"  Agent: {violation['agent_id']}")
            lines.append(f"  Issues:")
            for issue in violation["issues"]:
                lines.append(f"    • {issue}")

            # Find the full evaluation for more context
            eval_match = next(
                (e for e in self.state.qa_evaluations
                 if e.interaction_id == violation["interaction_id"]),
                None,
            )
            if eval_match:
                lines.append(f"  Compliance Score: {eval_match.compliance_score}/100")
                lines.append(f"  Overall Score: {eval_match.overall_score}/100")
            lines.append("")

        lines.extend([
            "═══════════════════════════════════════════════════════════",
            "ACTION REQUIRED: Review and remediate within 24 hours.",
            "Affected agents must be pulled from live queues until",
            "compliance retraining is completed.",
            "═══════════════════════════════════════════════════════════",
        ])

        self.state.compliance_escalation_report = "\n".join(lines)
        print("  ✓ Escalation report generated")

    # ------------------------------------------------------------------
    # Step 4b/5: Pattern detection
    # Reads:  qa_evaluations, campaign_name, evaluation_period
    # Writes: pattern_insights, agents_needing_coaching
    # ------------------------------------------------------------------
    @listen(or_("compliance_escalation", "standard_analysis"))
    def detect_patterns(self):
        """Analyze all evaluations for cross-agent and systemic patterns."""
        print(f"\n{'='*60}")
        print("STEP 5: Pattern Detection — finding systemic issues")
        print(f"{'='*60}")

        if not self.state.qa_evaluations:
            self.state.errors.append("No QA evaluations available for pattern analysis")
            return

        # Pre-format evaluations summary for the agent
        eval_lines = []
        for e in self.state.qa_evaluations:
            eval_lines.append(
                f"- {e.interaction_id} | Agent: {e.agent_id} | "
                f"Compliance: {e.compliance_score} | Empathy: {e.empathy_score} | "
                f"Resolution: {e.resolution_score} | Process: {e.process_adherence_score} | "
                f"Overall: {e.overall_score} | Severity: {e.compliance_severity.value} | "
                f"Issues: {', '.join(e.compliance_issues) if e.compliance_issues else 'None'} | "
                f"Strengths: {', '.join(e.strengths[:2]) if e.strengths else 'N/A'} | "
                f"Improvements: {', '.join(e.improvement_areas[:2]) if e.improvement_areas else 'N/A'}"
            )
        evaluations_summary = "\n".join(eval_lines)

        try:
            result = PatternAnalysisCrew().crew().kickoff(
                inputs={
                    "campaign_name": self.state.campaign_name,
                    "evaluation_period": self.state.evaluation_period,
                    "evaluations_summary": evaluations_summary,
                }
            )

            parsed = None
            if result.pydantic:
                parsed = result.pydantic.model_dump() if hasattr(result.pydantic, 'model_dump') else vars(result.pydantic)
            else:
                parsed = _parse_json_safe(result.raw)

            if parsed:
                if "insights" in parsed:
                    self.state.pattern_insights = [
                        PatternInsight(**p) for p in parsed["insights"]
                    ]
                if "agents_needing_coaching" in parsed:
                    self.state.agents_needing_coaching = parsed["agents_needing_coaching"]

            print(f"  ✓ Found {len(self.state.pattern_insights)} pattern(s)")
            print(f"  ✓ {len(self.state.agents_needing_coaching)} agent(s) need coaching")

        except Exception as e:
            self.state.errors.append(f"Pattern analysis failed: {str(e)}")
            print(f"  ✗ Pattern analysis failed: {e}")

            # Fallback: identify agents needing coaching from evaluations
            agents_below = set()
            for ev in self.state.qa_evaluations:
                if ev.overall_score < 70 or ev.compliance_severity in (
                    ComplianceSeverity.CRITICAL,
                    ComplianceSeverity.MAJOR,
                ):
                    agents_below.add(ev.agent_id)
            self.state.agents_needing_coaching = list(agents_below)
            print(f"  → Fallback: {len(agents_below)} agent(s) identified for coaching")

    # ------------------------------------------------------------------
    # Step 6: Coaching plans
    # Reads:  agents_needing_coaching, qa_evaluations, pattern_insights
    # Writes: coaching_plans
    # ------------------------------------------------------------------
    @listen(detect_patterns)
    def generate_coaching_plans(self):
        """Generate personalized coaching plans for flagged agents."""
        print(f"\n{'='*60}")
        print("STEP 6: Coaching Plans — generating per-agent plans")
        print(f"{'='*60}")

        if not self.state.agents_needing_coaching:
            print("  ○ No agents need coaching — skipping")
            return

        # Build agent name lookup from transcripts
        agent_names = {}
        for t in self.state.raw_transcripts:
            agent_names[t.agent_id] = t.agent_name

        for agent_id in self.state.agents_needing_coaching:
            agent_name = agent_names.get(agent_id, agent_id)

            # Gather this agent's evaluations
            agent_evals = [
                e for e in self.state.qa_evaluations if e.agent_id == agent_id
            ]
            eval_summary_lines = []
            for e in agent_evals:
                eval_summary_lines.append(
                    f"Interaction {e.interaction_id}: "
                    f"Compliance={e.compliance_score}, Empathy={e.empathy_score}, "
                    f"Resolution={e.resolution_score}, Process={e.process_adherence_score}, "
                    f"Overall={e.overall_score}, Severity={e.compliance_severity.value}\n"
                    f"  Issues: {', '.join(e.compliance_issues) if e.compliance_issues else 'None'}\n"
                    f"  Strengths: {', '.join(e.strengths) if e.strengths else 'None'}\n"
                    f"  Improvements: {', '.join(e.improvement_areas) if e.improvement_areas else 'None'}"
                )

            # Gather relevant patterns
            agent_patterns = [
                p for p in self.state.pattern_insights
                if agent_id in p.affected_agents
            ]
            pattern_lines = []
            for p in agent_patterns:
                pattern_lines.append(
                    f"Pattern: {p.pattern_type} — {p.description}\n"
                    f"  Recommended: {p.recommended_action}"
                )

            try:
                result = CoachingCrew().crew().kickoff(
                    inputs={
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "agent_evaluations": "\n".join(eval_summary_lines) or "No evaluations available",
                        "agent_patterns": "\n".join(pattern_lines) or "No specific patterns identified",
                    }
                )

                parsed = None
                if result.pydantic:
                    parsed = result.pydantic.model_dump() if hasattr(result.pydantic, 'model_dump') else vars(result.pydantic)
                else:
                    parsed = _parse_json_safe(result.raw)

                if parsed:
                    self.state.coaching_plans.append(CoachingPlan(
                        agent_id=parsed.get("agent_id", agent_id),
                        agent_name=parsed.get("agent_name", agent_name),
                        overall_performance=parsed.get("overall_performance", "below"),
                        key_strengths=parsed.get("key_strengths", []),
                        priority_improvements=parsed.get("priority_improvements", []),
                        specific_examples=parsed.get("specific_examples", []),
                        suggested_training=parsed.get("suggested_training", []),
                        follow_up_timeline=parsed.get("follow_up_timeline", "2 weeks"),
                    ))
                else:
                    raise ValueError(f"Could not parse coaching output: {result.raw[:200]}")

                print(f"  ✓ Coaching plan generated for {agent_name} ({agent_id})")

            except Exception as e:
                self.state.errors.append(
                    f"Failed coaching plan for {agent_id}: {str(e)}"
                )
                print(f"  ✗ Failed coaching plan for {agent_id}: {e}")
                continue

    # ------------------------------------------------------------------
    # Step 7: Final report compilation (inline — no crew)
    # Reads:  everything
    # Writes: executive_summary, detailed_qa_report, processing_status
    # ------------------------------------------------------------------
    @listen(generate_coaching_plans)
    def compile_final_report(self):
        """Compile executive summary and detailed QA report from all state."""
        print(f"\n{'='*60}")
        print("STEP 7: Final Report — compiling results")
        print(f"{'='*60}")

        # --- Executive Summary ---
        total = len(self.state.raw_transcripts)
        processed = self.state.transcripts_processed
        failed = self.state.transcripts_failed
        avg = self.state.average_scores

        critical_count = len(self.state.critical_violations)
        major_count = sum(
            1 for e in self.state.qa_evaluations
            if e.compliance_severity == ComplianceSeverity.MAJOR
        )
        agents_coached = len(self.state.coaching_plans)

        summary_lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║           QA AUDIT — EXECUTIVE SUMMARY                  ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            f"Campaign: {self.state.campaign_name}",
            f"Period: {self.state.evaluation_period}",
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "── OVERVIEW ──────────────────────────────────────────────",
            f"  Transcripts Analyzed: {total}",
            f"  Successfully Processed: {processed}",
            f"  Failed: {failed}",
            "",
            "── AVERAGE SCORES ────────────────────────────────────────",
            f"  Overall:            {avg.get('overall', 'N/A')}",
            f"  Compliance:         {avg.get('compliance', 'N/A')}",
            f"  Empathy:            {avg.get('empathy', 'N/A')}",
            f"  Resolution:         {avg.get('resolution', 'N/A')}",
            f"  Process Adherence:  {avg.get('process_adherence', 'N/A')}",
            "",
            "── COMPLIANCE ────────────────────────────────────────────",
            f"  Critical Violations: {critical_count}",
            f"  Major Violations: {major_count}",
            f"  Escalation Required: {'YES' if self.state.has_critical_violations else 'No'}",
            "",
            "── PATTERNS & COACHING ───────────────────────────────────",
            f"  Patterns Identified: {len(self.state.pattern_insights)}",
            f"  Agents Requiring Coaching: {agents_coached}",
            "",
        ]

        if self.state.pattern_insights:
            summary_lines.append("── KEY PATTERNS ──────────────────────────────────────────")
            for p in self.state.pattern_insights[:5]:
                summary_lines.append(f"  [{p.pattern_type.upper()}] {p.description}")
            summary_lines.append("")

        if self.state.errors:
            summary_lines.append("── ERRORS ────────────────────────────────────────────────")
            for err in self.state.errors:
                summary_lines.append(f"  ⚠ {err}")
            summary_lines.append("")

        self.state.executive_summary = "\n".join(summary_lines)

        # --- Detailed Report ---
        detail_lines = [self.state.executive_summary, ""]

        # Risk scores
        detail_lines.append("═══ RISK SCORES ═══════════════════════════════════════════")
        for rs in self.state.risk_scores:
            detail_lines.append(
                f"  {rs.interaction_id}: score={rs.risk_score:.2f} "
                f"priority={rs.priority_for_review} "
                f"factors={', '.join(rs.risk_factors[:3])}"
            )
        detail_lines.append("")

        # Individual evaluations
        detail_lines.append("═══ QA EVALUATIONS ════════════════════════════════════════")
        for ev in self.state.qa_evaluations:
            detail_lines.extend([
                f"\n  --- {ev.interaction_id} (Agent: {ev.agent_id}) ---",
                f"  Compliance: {ev.compliance_score} | Empathy: {ev.empathy_score} | "
                f"Resolution: {ev.resolution_score} | Process: {ev.process_adherence_score}",
                f"  Overall: {ev.overall_score} | Severity: {ev.compliance_severity.value}",
            ])
            if ev.compliance_issues:
                detail_lines.append(f"  Issues: {', '.join(ev.compliance_issues)}")
            if ev.strengths:
                detail_lines.append(f"  Strengths: {', '.join(ev.strengths)}")
            if ev.improvement_areas:
                detail_lines.append(f"  Improve: {', '.join(ev.improvement_areas)}")
        detail_lines.append("")

        # Coaching plans
        if self.state.coaching_plans:
            detail_lines.append("═══ COACHING PLANS ════════════════════════════════════════")
            for cp in self.state.coaching_plans:
                detail_lines.extend([
                    f"\n  --- {cp.agent_name} ({cp.agent_id}) ---",
                    f"  Performance: {cp.overall_performance}",
                    f"  Follow-up: {cp.follow_up_timeline}",
                    f"  Strengths: {', '.join(cp.key_strengths[:3])}",
                    f"  Priorities: {', '.join(cp.priority_improvements[:3])}",
                    f"  Training: {', '.join(cp.suggested_training[:3])}",
                ])

        self.state.detailed_qa_report = "\n".join(detail_lines)
        self.state.processing_status = "complete"

        print("  ✓ Executive summary compiled")
        print("  ✓ Detailed report compiled")
        print(f"  ✓ Processing status: {self.state.processing_status}")
        print(f"\n{'='*60}")
        print("QA AUDIT FLOW COMPLETE")
        print(f"{'='*60}")
