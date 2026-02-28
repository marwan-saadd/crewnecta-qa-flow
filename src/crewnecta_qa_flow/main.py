"""Entry point for the QA Auditor Flow.

Loads transcripts from JSON, creates state, runs the flow, and saves results.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from crewnecta_qa_flow.state.models import InteractionTranscript, QAAuditorState
from crewnecta_qa_flow.flow.qa_auditor_flow import QAAuditorFlow


def load_transcripts(path: str) -> list[InteractionTranscript]:
    """Load transcripts from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)

    raw = data.get("transcripts", data) if isinstance(data, dict) else data
    return [InteractionTranscript(**t) for t in raw]


def save_results(state: QAAuditorState, output_dir: str = "output") -> None:
    """Save the full state and reports to the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    # Full state as JSON
    state_path = os.path.join(output_dir, "full_state.json")
    with open(state_path, "w") as f:
        json.dump(state.model_dump(mode="json"), f, indent=2, default=str)
    print(f"Full state saved to {state_path}")

    # Executive summary as text
    if state.executive_summary:
        summary_path = os.path.join(output_dir, "executive_summary.txt")
        with open(summary_path, "w") as f:
            f.write(state.executive_summary)
        print(f"Executive summary saved to {summary_path}")

    # Detailed report as text
    if state.detailed_qa_report:
        report_path = os.path.join(output_dir, "detailed_report.txt")
        with open(report_path, "w") as f:
            f.write(state.detailed_qa_report)
        print(f"Detailed report saved to {report_path}")

    # Escalation report if present
    if state.compliance_escalation_report:
        esc_path = os.path.join(output_dir, "compliance_escalation.txt")
        with open(esc_path, "w") as f:
            f.write(state.compliance_escalation_report)
        print(f"Escalation report saved to {esc_path}")


def main() -> None:
    """Run the QA Auditor Flow."""
    load_dotenv()

    # Determine transcript source
    data_path = sys.argv[1] if len(sys.argv) > 1 else "data/mock_transcripts.json"

    if not os.path.exists(data_path):
        print(f"Error: transcript file not found at {data_path}")
        sys.exit(1)

    print(f"Loading transcripts from {data_path}...")
    transcripts = load_transcripts(data_path)
    print(f"Loaded {len(transcripts)} transcripts")

    # Build initial state
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

    # Run the flow
    flow = QAAuditorFlow()
    flow.initial_state = state
    flow.kickoff()

    # Print results
    print("\n\n")
    print(flow.state.executive_summary)

    # Save outputs
    save_results(flow.state)

    if flow.state.errors:
        print(f"\n⚠ {len(flow.state.errors)} error(s) occurred during processing")
        for err in flow.state.errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
