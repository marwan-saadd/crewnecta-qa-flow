"""QA Scorecard Calculator — bonus custom tool.

Takes raw QA dimension scores and applies client-specific weighting to
produce a final overall QA score. Different BPO clients weight compliance
vs. empathy vs. resolution differently.
"""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


WEIGHT_PROFILES = {
    "standard": {
        "compliance": 0.30,
        "empathy": 0.25,
        "resolution": 0.25,
        "process_adherence": 0.20,
    },
    "compliance_heavy": {
        "compliance": 0.45,
        "empathy": 0.15,
        "resolution": 0.20,
        "process_adherence": 0.20,
    },
    "cx_focused": {
        "compliance": 0.20,
        "empathy": 0.35,
        "resolution": 0.30,
        "process_adherence": 0.15,
    },
}


class ScorecardInput(BaseModel):
    compliance_score: float = Field(description="Compliance score 0-100")
    empathy_score: float = Field(description="Empathy score 0-100")
    resolution_score: float = Field(description="Resolution effectiveness score 0-100")
    process_adherence_score: float = Field(description="Process adherence score 0-100")
    weight_profile: str = Field(
        default="standard",
        description="Weight profile: 'standard', 'compliance_heavy', 'cx_focused'",
    )


class QAScorecardCalculator(BaseTool):
    name: str = "QA Scorecard Calculator"
    description: str = (
        "Calculates a weighted overall QA score from individual dimension scores "
        "(compliance, empathy, resolution, process adherence). Supports different "
        "weight profiles: 'standard', 'compliance_heavy', 'cx_focused'. "
        "Returns the weighted overall score and a breakdown of each dimension's contribution."
    )
    args_schema: Type[BaseModel] = ScorecardInput

    def _run(
        self,
        compliance_score: float,
        empathy_score: float,
        resolution_score: float,
        process_adherence_score: float,
        weight_profile: str = "standard",
    ) -> str:
        weights = WEIGHT_PROFILES.get(weight_profile, WEIGHT_PROFILES["standard"])

        breakdown = {
            "compliance": {
                "raw_score": compliance_score,
                "weight": weights["compliance"],
                "weighted_score": round(compliance_score * weights["compliance"], 2),
            },
            "empathy": {
                "raw_score": empathy_score,
                "weight": weights["empathy"],
                "weighted_score": round(empathy_score * weights["empathy"], 2),
            },
            "resolution": {
                "raw_score": resolution_score,
                "weight": weights["resolution"],
                "weighted_score": round(resolution_score * weights["resolution"], 2),
            },
            "process_adherence": {
                "raw_score": process_adherence_score,
                "weight": weights["process_adherence"],
                "weighted_score": round(
                    process_adherence_score * weights["process_adherence"], 2
                ),
            },
        }

        overall = round(
            sum(dim["weighted_score"] for dim in breakdown.values()), 2
        )

        # Performance band
        if overall >= 90:
            band = "exceeds_expectations"
        elif overall >= 75:
            band = "meets_expectations"
        elif overall >= 60:
            band = "needs_improvement"
        else:
            band = "critical"

        return json.dumps(
            {
                "overall_score": overall,
                "performance_band": band,
                "weight_profile_used": weight_profile,
                "breakdown": breakdown,
            },
            indent=2,
        )
