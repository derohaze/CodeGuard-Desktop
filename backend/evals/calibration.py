def build_score_expectation(score: int, coverage_percent: int, findings_count: int, candidate_findings_count: int) -> dict:
    return {
        "score": score,
        "coverage_percent": coverage_percent,
        "findings_count": findings_count,
        "candidate_findings_count": candidate_findings_count,
        "band": (
            "trusted_high_coverage"
            if coverage_percent >= 95 and findings_count == 0
            else "partial_or_candidate_pressure"
            if findings_count == 0
            else "validated_issues_found"
        ),
    }
