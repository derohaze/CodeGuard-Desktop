from __future__ import annotations


def build_remediation_summary(repo_results: list[dict]) -> dict:
    available = [item for item in repo_results if item.get("status") == "completed"]
    finding_results = [finding for item in available for finding in item.get("remediation_findings", [])]
    total_findings = len(finding_results)
    if not total_findings:
        return {
            "repos_total": len(repo_results),
            "repos_completed": len(available),
            "findings_evaluated": 0,
            "best_strategy_accuracy": 0.0,
            "full_fix_rate": 0.0,
            "sink_aligned_rate": 0.0,
            "residual_risk_clarity_rate": 0.0,
            "quality_pass_rate": 0.0,
        }

    return {
        "repos_total": len(repo_results),
        "repos_completed": len(available),
        "findings_evaluated": total_findings,
        "best_strategy_accuracy": round(sum(1 for item in finding_results if item.get("best_strategy_fit")) / total_findings, 2),
        "full_fix_rate": round(sum(1 for item in finding_results if item.get("recommended_fix_type") == "full_fix") / total_findings, 2),
        "sink_aligned_rate": round(sum(1 for item in finding_results if item.get("sink_aligned")) / total_findings, 2),
        "residual_risk_clarity_rate": round(sum(1 for item in finding_results if item.get("residual_risk_clear")) / total_findings, 2),
        "quality_pass_rate": round(sum(1 for item in finding_results if item.get("quality_pass")) / total_findings, 2),
        "average_remediation_score": round(sum(item.get("remediation_score", 0) for item in finding_results) / total_findings, 2),
        "score_distribution": {
            "80_plus": sum(1 for item in finding_results if item.get("remediation_score", 0) >= 80),
            "60_79": sum(1 for item in finding_results if 60 <= item.get("remediation_score", 0) < 80),
            "40_59": sum(1 for item in finding_results if 40 <= item.get("remediation_score", 0) < 60),
            "below_40": sum(1 for item in finding_results if item.get("remediation_score", 0) < 40),
        },
    }
