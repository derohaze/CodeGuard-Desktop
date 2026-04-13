def build_eval_summary(case_results: list[dict]) -> dict:
    completed_cases = [item for item in case_results if item.get("status") == "completed"]
    total_cases = len(case_results)
    false_positive_count = sum(1 for item in case_results if item.get("expected_kind") == "clean" and item.get("findings_count", 0) > 0)
    false_negative_count = sum(1 for item in case_results if item.get("expected_kind") == "vulnerable" and item.get("findings_count", 0) == 0)
    cross_file_cases = [item for item in case_results if item.get("tags") and "cross_file" in item["tags"]]
    sanitizer_cases = [item for item in case_results if item.get("tags") and "sanitizer" in item["tags"]]

    return {
        "total_cases": total_cases,
        "completed_cases": len(completed_cases),
        "passed_cases": sum(1 for item in case_results if item.get("passed")),
        "false_positive_rate": false_positive_count / max(1, total_cases),
        "false_negative_rate": false_negative_count / max(1, total_cases),
        "average_security_score": round(sum(item.get("security_score", 0) for item in case_results) / max(1, total_cases), 2),
        "average_coverage_percent": round(sum(item.get("coverage_percent", 0) for item in case_results) / max(1, total_cases), 2),
        "sanitizer_handling_accuracy": round(
            sum(1 for item in sanitizer_cases if item.get("passed")) / max(1, len(sanitizer_cases)),
            2,
        ),
        "cross_file_validation_success_rate": round(
            sum(1 for item in cross_file_cases if item.get("passed")) / max(1, len(cross_file_cases)),
            2,
        ),
        "severity_accuracy": round(
            sum(1 for item in case_results if item.get("severity_match", True)) / max(1, total_cases),
            2,
        ),
    }
