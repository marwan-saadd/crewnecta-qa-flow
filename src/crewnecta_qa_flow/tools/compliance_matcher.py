"""Compliance Pattern Matcher — bonus custom tool.

Checks a transcript against a library of REQUIRED regulatory phrases
(mandatory disclosures, opt-out language, verification steps) and returns
which elements were present vs. missing.
"""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Each requirement set defines phrases that MUST appear and phrases that
# must NOT appear in a compliant interaction.
REQUIREMENT_SETS: dict[str, dict] = {
    "general": {
        "must_contain": {
            "call_recording_disclosure": [
                "call may be recorded",
                "call is being recorded",
                "this call is recorded",
                "for quality and training",
                "chat is being recorded",
            ],
            "identity_verification": [
                "verify your identity",
                "confirm your name",
                "can you confirm",
                "for security purposes",
                "verify your account",
            ],
        },
        "must_not_contain": {
            "full_card_readback": [
                "your card number is",
                "card number is ",
                "read back your card",
                "your full card number",
            ],
            "ssn_spoken": [
                "your social security number is",
                "your ssn is",
            ],
        },
    },
    "pci_dss": {
        "must_contain": {
            "secure_payment_redirect": [
                "secure payment",
                "transfer you to our payment system",
                "payment portal",
                "secure line",
            ],
        },
        "must_not_contain": {
            "card_number_spoken": [
                "your card number is",
                "card number is ",
                "read back your card",
                "repeat your card",
                "full card number",
            ],
            "cvv_spoken": [
                "your cvv is",
                "security code is",
                "cvv number is",
            ],
            "card_stored": [
                "we have your card on file",
                "stored your card",
                "keep your card",
            ],
        },
    },
    "collections": {
        "must_contain": {
            "mini_miranda": [
                "this is an attempt to collect a debt",
                "any information obtained will be used for that purpose",
                "debt collector",
            ],
            "right_party_verification": [
                "am i speaking with",
                "is this",
                "confirm your identity",
            ],
        },
        "must_not_contain": {
            "third_party_disclosure": [
                "tell them they owe",
                "inform your family",
                "let your employer know",
            ],
            "threats": [
                "we will have you arrested",
                "go to jail",
                "sue you",
                "garnish your wages",
            ],
        },
    },
    "sales": {
        "must_contain": {
            "terms_and_conditions": [
                "terms and conditions",
                "terms of service",
                "by agreeing",
                "do you accept the terms",
            ],
            "cancellation_policy": [
                "cancel within",
                "cancellation policy",
                "cooling off period",
                "money back guarantee",
            ],
            "pricing_disclosure": [
                "total cost",
                "monthly charge",
                "per month",
                "billed at",
                "price is",
            ],
        },
        "must_not_contain": {
            "misleading_claims": [
                "guaranteed to",
                "you will definitely",
                "100% guaranteed",
                "no risk at all",
            ],
        },
    },
}


class ComplianceMatchInput(BaseModel):
    transcript_text: str = Field(description="Transcript to check for compliance")
    requirement_set: str = Field(
        default="general",
        description="Which compliance set: 'general', 'pci_dss', 'collections', 'sales'",
    )


class CompliancePatternMatcher(BaseTool):
    name: str = "Compliance Pattern Matcher"
    description: str = (
        "Checks a transcript against a library of REQUIRED regulatory phrases "
        "(mandatory disclosures, opt-out language, verification steps) and phrases "
        "that must NOT appear. Returns a checklist with pass/fail per requirement. "
        "Requirement sets: 'general', 'pci_dss', 'collections', 'sales'."
    )
    args_schema: Type[BaseModel] = ComplianceMatchInput

    def _run(self, transcript_text: str, requirement_set: str = "general") -> str:
        reqs = REQUIREMENT_SETS.get(requirement_set, REQUIREMENT_SETS["general"])
        text_lower = transcript_text.lower()

        results: list[dict] = []
        total = 0
        passed = 0

        # Check must_contain requirements
        for req_name, phrases in reqs.get("must_contain", {}).items():
            total += 1
            found = any(p in text_lower for p in phrases)
            matched = [p for p in phrases if p in text_lower]
            if found:
                passed += 1
            results.append({
                "requirement": req_name,
                "type": "must_contain",
                "status": "PASS" if found else "FAIL",
                "matched_phrases": matched,
            })

        # Check must_not_contain requirements
        for req_name, phrases in reqs.get("must_not_contain", {}).items():
            total += 1
            violations = [p for p in phrases if p in text_lower]
            is_clean = len(violations) == 0
            if is_clean:
                passed += 1
            results.append({
                "requirement": req_name,
                "type": "must_not_contain",
                "status": "PASS" if is_clean else "FAIL",
                "violation_phrases_found": violations,
            })

        compliance_rate = round((passed / total) * 100, 1) if total > 0 else 100.0

        return json.dumps(
            {
                "requirement_set": requirement_set,
                "total_checks": total,
                "passed": passed,
                "failed": total - passed,
                "compliance_rate": compliance_rate,
                "results": results,
            },
            indent=2,
        )
