from .red_flag_scanner import KeywordRedFlagScanner
from .scorecard_calc import QAScorecardCalculator
from .compliance_matcher import CompliancePatternMatcher

keyword_red_flag_scanner = KeywordRedFlagScanner()
scorecard_calculator = QAScorecardCalculator()
compliance_pattern_matcher = CompliancePatternMatcher()

__all__ = [
    "KeywordRedFlagScanner",
    "QAScorecardCalculator",
    "CompliancePatternMatcher",
    "keyword_red_flag_scanner",
    "scorecard_calculator",
    "compliance_pattern_matcher",
]
