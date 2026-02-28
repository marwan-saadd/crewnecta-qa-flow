"""Streamlit UI for the QA Auditor Flow.

Live run mode: triggers the full flow and displays results in real-time.
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path so imports work
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "src"))

from dotenv import load_dotenv

from crewnecta_qa_flow.state.models import (
    ComplianceSeverity,
    InteractionTranscript,
    QAAuditorState,
)
from crewnecta_qa_flow.flow.qa_auditor_flow import QAAuditorFlow

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CrewNecta QA Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("CrewNecta — Intelligent QA Auditor")
st.caption("AI-powered BPO quality assurance and coaching engine")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_transcripts_from_file(file_path: str) -> list[dict]:
    with open(file_path, "r") as f:
        data = json.load(f)
    return data.get("transcripts", data) if isinstance(data, dict) else data


def load_transcripts_from_upload(uploaded) -> list[dict]:
    data = json.loads(uploaded.read())
    return data.get("transcripts", data) if isinstance(data, dict) else data


def run_flow(transcripts_raw: list[dict]) -> QAAuditorState:
    """Run the full QA auditor flow and return final state."""
    transcripts = [InteractionTranscript(**t) for t in transcripts_raw]

    state = QAAuditorState(
        raw_transcripts=transcripts,
        campaign_name="Customer Support — Q1 2026 Audit",
        evaluation_period="February 2026",
        compliance_requirements=[
            "PCI-DSS: No card numbers read back",
            "Call recording disclosure required",
            "Identity verification before account changes",
            "Terms and conditions disclosure on sales calls",
        ],
    )

    flow = QAAuditorFlow()
    flow.initial_state = state
    flow.kickoff()
    return flow.state


# ---------------------------------------------------------------------------
# Sidebar — Input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Input")

    input_mode = st.radio(
        "Transcript source",
        ["Use Demo Data", "Upload JSON"],
        index=0,
    )

    transcripts_raw = None

    if input_mode == "Upload JSON":
        uploaded = st.file_uploader("Upload transcripts JSON", type=["json"])
        if uploaded:
            transcripts_raw = load_transcripts_from_upload(uploaded)
            st.success(f"Loaded {len(transcripts_raw)} transcripts")
    else:
        demo_path = os.path.join(project_root, "data", "mock_transcripts.json")
        if os.path.exists(demo_path):
            transcripts_raw = load_transcripts_from_file(demo_path)
            st.info(f"Demo data: {len(transcripts_raw)} transcripts")
        else:
            st.error("Demo data not found")

    run_btn = st.button(
        "Run QA Audit",
        type="primary",
        disabled=transcripts_raw is None,
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if run_btn and transcripts_raw:
    with st.status("Running QA Audit Flow...", expanded=True) as status:
        st.write("Step 1/7: Risk scoring all transcripts...")
        state = run_flow(transcripts_raw)
        status.update(label="QA Audit Complete!", state="complete", expanded=False)

    st.session_state["state"] = state

if "state" not in st.session_state:
    st.info("Configure input in the sidebar and click **Run QA Audit** to start.")
    st.stop()

state: QAAuditorState = st.session_state["state"]

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "Overview",
    "Risk Scores",
    "Agent Scores",
    "Compliance",
    "Patterns",
    "Coaching",
    "Raw Data",
])

# ---- Overview Tab ----
with tabs[0]:
    st.header("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transcripts", len(state.raw_transcripts))
    col2.metric("Avg Score", f"{state.average_scores.get('overall', 0):.1f}")
    col3.metric(
        "Critical Violations",
        len(state.critical_violations),
        delta=None,
    )
    col4.metric("Agents Coached", len(state.coaching_plans))

    if state.has_critical_violations:
        st.error(
            f"CRITICAL COMPLIANCE VIOLATIONS DETECTED — "
            f"{len(state.critical_violations)} interaction(s) require immediate review"
        )

    st.text(state.executive_summary)

    if state.errors:
        with st.expander(f"Errors ({len(state.errors)})"):
            for err in state.errors:
                st.warning(err)

# ---- Risk Scores Tab ----
with tabs[1]:
    st.header("Risk Score Distribution")

    if state.risk_scores:
        risk_data = [
            {
                "Interaction": rs.interaction_id,
                "Risk Score": rs.risk_score,
                "Priority": rs.priority_for_review,
                "Factors": ", ".join(rs.risk_factors[:3]),
            }
            for rs in state.risk_scores
        ]

        color_map = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
        fig = px.bar(
            risk_data,
            x="Interaction",
            y="Risk Score",
            color="Priority",
            color_discrete_map=color_map,
            title="Risk Scores by Interaction",
            hover_data=["Factors"],
        )
        fig.update_layout(yaxis_range=[0, 1.05])
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(risk_data, use_container_width=True)
    else:
        st.info("No risk scores available.")

# ---- Agent Scores Tab ----
with tabs[2]:
    st.header("Per-Agent Score Breakdown")

    if state.qa_evaluations:
        # Group evaluations by agent
        agent_scores: dict[str, dict] = {}
        for ev in state.qa_evaluations:
            aid = ev.agent_id
            if aid not in agent_scores:
                agent_scores[aid] = {
                    "compliance": [],
                    "empathy": [],
                    "resolution": [],
                    "process": [],
                }
            agent_scores[aid]["compliance"].append(ev.compliance_score)
            agent_scores[aid]["empathy"].append(ev.empathy_score)
            agent_scores[aid]["resolution"].append(ev.resolution_score)
            agent_scores[aid]["process"].append(ev.process_adherence_score)

        # Get agent names
        agent_names = {}
        for t in state.raw_transcripts:
            agent_names[t.agent_id] = t.agent_name

        # Radar chart per agent
        categories = ["Compliance", "Empathy", "Resolution", "Process"]
        fig = go.Figure()

        for aid, scores in agent_scores.items():
            avg_vals = [
                sum(scores["compliance"]) / len(scores["compliance"]),
                sum(scores["empathy"]) / len(scores["empathy"]),
                sum(scores["resolution"]) / len(scores["resolution"]),
                sum(scores["process"]) / len(scores["process"]),
            ]
            name = agent_names.get(aid, aid)
            fig.add_trace(
                go.Scatterpolar(
                    r=avg_vals + [avg_vals[0]],  # close the polygon
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=f"{name} ({aid})",
                )
            )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Agent Performance Radar",
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Per-agent detail table
        for aid, scores in agent_scores.items():
            name = agent_names.get(aid, aid)
            with st.expander(f"{name} ({aid})"):
                agent_evals = [e for e in state.qa_evaluations if e.agent_id == aid]
                for ev in agent_evals:
                    st.markdown(f"**{ev.interaction_id}** — Overall: {ev.overall_score}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Compliance", f"{ev.compliance_score:.0f}")
                    c2.metric("Empathy", f"{ev.empathy_score:.0f}")
                    c3.metric("Resolution", f"{ev.resolution_score:.0f}")
                    c4.metric("Process", f"{ev.process_adherence_score:.0f}")
                    if ev.strengths:
                        st.success("Strengths: " + ", ".join(ev.strengths))
                    if ev.improvement_areas:
                        st.warning("Improve: " + ", ".join(ev.improvement_areas))
                    st.divider()
    else:
        st.info("No evaluations available.")

# ---- Compliance Tab ----
with tabs[3]:
    st.header("Compliance Overview")

    if state.qa_evaluations:
        for ev in state.qa_evaluations:
            severity = ev.compliance_severity.value
            if severity == "critical":
                badge = "🔴 CRITICAL"
            elif severity == "major":
                badge = "🟠 MAJOR"
            elif severity == "minor":
                badge = "🟡 MINOR"
            else:
                badge = "🟢 NONE"

            with st.expander(f"{badge} — {ev.interaction_id} (Agent: {ev.agent_id})"):
                st.metric("Compliance Score", f"{ev.compliance_score:.0f}/100")
                if ev.compliance_issues:
                    st.error("Issues:")
                    for issue in ev.compliance_issues:
                        st.markdown(f"- {issue}")
                else:
                    st.success("No compliance issues detected")

        if state.compliance_escalation_report:
            st.divider()
            st.subheader("Escalation Report")
            st.code(state.compliance_escalation_report, language=None)
    else:
        st.info("No compliance data available.")

# ---- Patterns Tab ----
with tabs[4]:
    st.header("Pattern Insights")

    if state.pattern_insights:
        for p in state.pattern_insights:
            type_colors = {
                "agent_specific": "blue",
                "systemic": "red",
                "script_issue": "orange",
                "training_gap": "violet",
            }
            color = type_colors.get(p.pattern_type, "gray")

            with st.container(border=True):
                st.markdown(f":{color}[**{p.pattern_type.upper()}**]")
                st.markdown(f"**{p.description}**")
                st.markdown(f"Affected agents: {', '.join(p.affected_agents)}")
                st.markdown(f"Frequency: {p.frequency}")
                st.markdown(f"Evidence: {', '.join(p.evidence_interaction_ids)}")
                st.info(f"Recommended: {p.recommended_action}")
    else:
        st.info("No patterns detected.")

# ---- Coaching Tab ----
with tabs[5]:
    st.header("Coaching Plans")

    if state.coaching_plans:
        for cp in state.coaching_plans:
            perf_icon = {
                "exceeds": "🌟",
                "meets": "✅",
                "below": "⚠️",
                "critical": "🚨",
            }.get(cp.overall_performance, "❓")

            with st.expander(
                f"{perf_icon} {cp.agent_name} ({cp.agent_id}) — {cp.overall_performance.upper()}"
            ):
                st.markdown(f"**Follow-up:** {cp.follow_up_timeline}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Key Strengths:**")
                    for s in cp.key_strengths:
                        st.markdown(f"- {s}")

                with col2:
                    st.markdown("**Priority Improvements:**")
                    for imp in cp.priority_improvements:
                        st.markdown(f"- {imp}")

                if cp.specific_examples:
                    st.markdown("**Specific Examples:**")
                    for ex in cp.specific_examples:
                        st.markdown(f"> {ex}")

                if cp.suggested_training:
                    st.markdown("**Suggested Training:**")
                    for t in cp.suggested_training:
                        st.markdown(f"- {t}")
    else:
        st.info("No coaching plans generated.")

# ---- Raw Data Tab ----
with tabs[6]:
    st.header("Full State (JSON)")

    state_json = state.model_dump(mode="json")
    st.json(state_json)

    st.download_button(
        label="Download Full State (JSON)",
        data=json.dumps(state_json, indent=2, default=str),
        file_name="qa_audit_results.json",
        mime="application/json",
        use_container_width=True,
    )
