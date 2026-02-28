"""Keyword Red Flag Scanner — mandatory custom tool.

Scans a customer interaction transcript for BPO-specific red flag patterns.
Categorizes flags by type (compliance/complaint/process) and severity
(critical/high/medium). Returns JSON with flags, risk_score, and priority.
"""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class RedFlagInput(BaseModel):
    transcript_text: str = Field(description="The interaction transcript text to scan")
    channel: str = Field(description="Channel type: voice, chat, or email")


class KeywordRedFlagScanner(BaseTool):
    name: str = "Keyword Red Flag Scanner"
    description: str = (
        "Scans a customer interaction transcript for red flag keywords and patterns "
        "indicating compliance risks, customer complaints, escalation requests, "
        "or quality concerns. Returns categorized flags with severity levels."
    )
    args_schema: Type[BaseModel] = RedFlagInput

    def _run(self, transcript_text: str, channel: str) -> str:
        flags: list[dict] = []
        text_lower = transcript_text.lower()

        # COMPLIANCE RED FLAGS (severity: critical)
        compliance_patterns = {
            "card_number_exposure": [
                "card number is",
                "your card number",
                "read back",
                "credit card",
                "card ending in",
                "full card",
            ],
            "missing_disclosure": [
                "call may be recorded",
                "call is being recorded",
                "for quality and training",
                "chat is being recorded",
            ],
            "data_handling": [
                "social security",
                "ssn",
                "date of birth",
                "mother's maiden",
            ],
        }

        # COMPLAINT RED FLAGS (severity: high)
        complaint_patterns = {
            "escalation_request": [
                "speak to a manager",
                "speak to a supervisor",
                "transfer me to",
                "your manager",
                "escalate",
                "file a complaint",
                "formal complaint",
            ],
            "churn_risk": [
                "cancel my",
                "cancellation",
                "switch to",
                "competitor",
                "leaving",
                "done with you",
                "never coming back",
            ],
            "frustration": [
                "unacceptable",
                "ridiculous",
                "worst service",
                "been waiting",
                "third time",
                "already told",
                "keep repeating",
                "waste of time",
            ],
        }

        # PROCESS RED FLAGS (severity: medium)
        process_patterns = {
            "hold_issues": [
                "been on hold",
                "long hold",
                "holding for",
                "waited for",
            ],
            "transfer_issues": [
                "transferred again",
                "third person",
                "keep getting transferred",
                "bounced around",
            ],
            "repeat_contact": [
                "called before",
                "called yesterday",
                "already contacted",
                "third time calling",
                "same issue",
            ],
        }

        # Check for missing disclosure (inverted — absence is the flag)
        disclosure_phrases = [
            "call may be recorded",
            "call is being recorded",
            "for quality and training",
            "chat is being recorded",
        ]
        has_disclosure = any(p in text_lower for p in disclosure_phrases)

        # Scan compliance patterns
        for category, patterns in compliance_patterns.items():
            if category == "missing_disclosure":
                continue  # handled separately below
            for pattern in patterns:
                if pattern in text_lower:
                    flags.append({
                        "type": "compliance",
                        "category": category,
                        "severity": "critical",
                        "matched_pattern": pattern,
                    })

        # Missing disclosure flag (only for voice/chat where it's required)
        if not has_disclosure and channel in ("voice", "chat"):
            flags.append({
                "type": "compliance",
                "category": "missing_disclosure",
                "severity": "critical",
                "matched_pattern": "(no recording disclosure found)",
            })

        # Scan complaint patterns
        for category, patterns in complaint_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    flags.append({
                        "type": "complaint",
                        "category": category,
                        "severity": "high",
                        "matched_pattern": pattern,
                    })

        # Scan process patterns
        for category, patterns in process_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    flags.append({
                        "type": "process",
                        "category": category,
                        "severity": "medium",
                        "matched_pattern": pattern,
                    })

        # Calculate overall risk score
        severity_weights = {"critical": 1.0, "high": 0.7, "medium": 0.4}
        if flags:
            max_severity = max(severity_weights[f["severity"]] for f in flags)
            risk_score = min(1.0, max_severity + (len(flags) - 1) * 0.05)
        else:
            risk_score = 0.1  # Base low risk

        return json.dumps(
            {
                "flags_found": len(flags),
                "flags": flags,
                "risk_score": round(risk_score, 2),
                "priority": (
                    "high" if risk_score >= 0.7
                    else "medium" if risk_score >= 0.4
                    else "low"
                ),
            },
            indent=2,
        )
