# CrewNecta QA Flow

An AI-powered QA auditor and coaching engine for BPO (Business Process Outsourcing) contact centers, built with [CrewAI Flows](https://docs.crewai.com/concepts/flows).

BPO QA teams manually review only 1-3% of customer interactions using random sampling. This project analyzes **100% of transcripts** — risk-scoring them, auditing compliance, evaluating quality, detecting patterns across agents, and generating personalized coaching plans.

---

## How It Works

The system runs a 7-step pipeline orchestrated as a CrewAI Flow:

```
Transcripts ──> Risk Scoring ──> QA Analysis ──> Compliance Router
                                                    │           │
                                              CRITICAL      No critical
                                                    │           │
                                              Escalation        │
                                              Report            │
                                                    │           │
                                                    └─────┬─────┘
                                                          v
                                                  Pattern Detection
                                                          │
                                                  Coaching Plans
                                                          │
                                                   Final Report
```

**5 AI agents** across **4 crews** collaborate through a shared typed state:

| Agent | Role | Tools |
|-------|------|-------|
| Risk Scorer | Triage transcripts by risk priority | Keyword Red Flag Scanner |
| Compliance Auditor | Check regulatory compliance (PCI-DSS, GDPR) | Compliance Pattern Matcher |
| Quality Evaluator | Score empathy, resolution, process adherence | QA Scorecard Calculator |
| Pattern Analyst | Find systemic issues across agents | - |
| Coaching Architect | Generate actionable coaching plans | - |

---

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-org>/crewnecta-qa-flow.git
cd crewnecta-qa-flow

# Create .env from template and fill in your API credentials
cp .env.example .env

# Install dependencies
uv sync
```

### Configure `.env`

```env
OPENAI_API_KEY=<your-api-key>
OPENAI_API_BASE=<your-litellm-proxy-url>
MODEL_NAME=openai/gemini-2.5-flash
```

The project uses a LiteLLM-compatible proxy with an OpenAI-compatible API. Set `OPENAI_API_BASE` to your proxy URL and `OPENAI_API_KEY` to your proxy key.

### Run (CLI)

```bash
uv run python -m crewnecta_qa_flow.main
```

This runs the full pipeline on the included 10 mock transcripts and saves results to `output/`.

To use your own data:

```bash
uv run python -m crewnecta_qa_flow.main path/to/your/transcripts.json
```

### Run (Streamlit UI)

```bash
uv run streamlit run ui/app.py
```

Opens a dashboard at `http://localhost:8501` with file upload, live flow execution, charts, and export.

---

## Project Structure

```
crewnecta-qa-flow/
├── data/
│   └── mock_transcripts.json          # 10 realistic test transcripts
├── src/crewnecta_qa_flow/
│   ├── main.py                        # CLI entry point
│   ├── state/
│   │   └── models.py                  # Pydantic models (19-field state)
│   ├── tools/
│   │   ├── red_flag_scanner.py        # Keyword Red Flag Scanner
│   │   ├── scorecard_calc.py          # QA Scorecard Calculator
│   │   └── compliance_matcher.py      # Compliance Pattern Matcher
│   ├── crews/
│   │   ├── risk_scoring/              # Crew 1: risk triage
│   │   ├── qa_analysis/               # Crew 2: compliance + quality
│   │   ├── pattern_analysis/          # Crew 3: cross-agent patterns
│   │   └── coaching/                  # Crew 4: coaching plans
│   └── flow/
│       └── qa_auditor_flow.py         # Flow orchestration (7 steps)
├── ui/
│   └── app.py                         # Streamlit dashboard
├── pyproject.toml
├── .env.example
└── explainer.md                       # Detailed project explainer
```

Each crew directory contains:
- `config/agents.yaml` — agent role, goal, backstory, LLM
- `config/tasks.yaml` — task description, expected output, input variables
- `*_crew.py` — Python wiring (tools, `output_pydantic`, task context)

---

## Flow Steps

| Step | Method | What It Does | State Written |
|------|--------|-------------|---------------|
| 1 | `ingest_and_risk_score` | Scans all transcripts for red flags, assigns risk priority | `risk_scores` |
| 2 | `deep_qa_analysis` | Full compliance + quality analysis on HIGH/MEDIUM risk; LOW gets a default pass | `qa_evaluations`, `average_scores` |
| 3 | `route_by_compliance` | **Conditional router** — CRITICAL violations trigger escalation path | `has_critical_violations` |
| 4a | `handle_compliance_escalation` | Builds urgent escalation report (only if CRITICAL found) | `compliance_escalation_report` |
| 5 | `detect_patterns` | Finds systemic vs. agent-specific patterns across all evaluations | `pattern_insights`, `agents_needing_coaching` |
| 6 | `generate_coaching_plans` | Creates personalized plans with specific examples per agent | `coaching_plans` |
| 7 | `compile_final_report` | Aggregates executive summary and detailed report | `executive_summary`, `detailed_qa_report` |

---

## Custom Tools

### Keyword Red Flag Scanner (required)
Scans transcripts for compliance risks (critical), complaint signals (high), and process issues (medium). Returns categorized flags with a calculated risk score.

### QA Scorecard Calculator (bonus)
Applies weighted scoring across 4 dimensions. Supports 3 weight profiles: `standard`, `compliance_heavy`, `cx_focused`.

### Compliance Pattern Matcher (bonus)
Checks transcripts against regulatory requirement sets (`general`, `pci_dss`, `collections`, `sales`) for must-contain and must-not-contain phrases.

---

## Mock Data

10 transcripts across 5 agents (2 each) covering:

| Agent | Scenarios |
|-------|-----------|
| Maria Santos (AGT-042) | Clean interaction, excellent cancel save |
| James Park (AGT-017) | **Critical** PCI violation (card readback), empathy failure |
| David Lee (AGT-089) | Process failure (no verification), poor escalation handling |
| Lisa Chen (AGT-023) | Repeat contact frustration, good chat resolution |
| Sarah Kim (AGT-056) | Minor compliance (missing T&C), high empathy (bereavement) |

---

## Streamlit UI

The dashboard has 7 tabs:

- **Overview** — Key metrics, executive summary, violation alerts
- **Risk Scores** — Bar chart of risk scores by interaction, colored by priority
- **Agent Scores** — Radar chart comparing agents across compliance, empathy, resolution, process
- **Compliance** — Severity-badged findings per interaction with expandable details
- **Patterns** — Color-coded pattern insight cards with recommendations
- **Coaching** — Expandable coaching plans per agent
- **Raw Data** — Full JSON state viewer with download

---


## Input Format

Transcripts JSON should follow this structure:

```json
{
  "transcripts": [
    {
      "interaction_id": "INT-001",
      "agent_id": "AGT-042",
      "agent_name": "Maria Santos",
      "channel": "voice",
      "timestamp": "2026-02-25T09:15:00Z",
      "duration_seconds": 340,
      "transcript_text": "Agent: Hello...\nCustomer: Hi...",
      "customer_issue": "Billing inquiry",
      "resolution_status": "resolved"
    }
  ]
}
```

---

## Output

The CLI saves to `output/`:

| File | Contents |
|------|----------|
| `full_state.json` | Complete flow state (all inputs, enrichments, decisions, outputs) |
| `executive_summary.txt` | High-level metrics, scores, violation counts, patterns |
| `detailed_report.txt` | Full report with individual evaluations and coaching plans |
| `compliance_escalation.txt` | Urgent escalation report (only if critical violations found) |

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| CrewAI | Agent orchestration framework (Flows, Agents, Tasks, Tools) |
| Pydantic | Typed state, structured LLM outputs, data validation |
| LiteLLM | LLM proxy (routes to gemini-2.5-flash via OpenAI-compatible API) |
| Streamlit | Web dashboard |
| Plotly | Interactive charts (radar, bar) |
| UV | Package management |
