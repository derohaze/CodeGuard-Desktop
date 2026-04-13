import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from evals.calibration import build_score_expectation
from evals.cases import EVAL_CASES
from evals.real_world_cases import REAL_WORLD_CASES
from evals.reporting import build_eval_summary


def run_eval_suite() -> dict:
    client = TestClient(app)
    case_results = []

    for case in EVAL_CASES:
        case_results.append(run_eval_case(client, case))

    real_world = []
    for case in REAL_WORLD_CASES:
        real_world.append(
            {
                "name": case.name,
                "status": "available" if case.local_path.exists() else "missing_repo",
                "source_path": str(case.local_path),
                "repo_slug": case.repo_slug,
                "expected_kind": case.expected_kind,
                "notes": case.notes,
            }
        )

    return {
        "summary": build_eval_summary(case_results),
        "cases": case_results,
        "real_world_cases": real_world,
    }


def run_eval_case(client: TestClient, case) -> dict:
    response = client.post(
        "/api/v1/scans",
        json={
            "source_path": str(case.source_path),
            "target_type": case.target_type,
            "preset": "balanced",
            "scan_mode": "deep",
        },
    )
    response.raise_for_status()
    session_id = response.json()["session"]["id"]

    final_data = None
    for _ in range(90):
        detail = client.get(f"/api/v1/scans/{session_id}")
        detail.raise_for_status()
        final_data = detail.json()
        if final_data["session"]["status"] in {"completed", "failed"}:
            break
        time.sleep(0.5)

    findings_count = len(final_data["findings"])
    candidate_findings_count = len(final_data.get("candidate_findings", []))
    score = int(final_data["session"]["security_score"])
    status = final_data["session"]["status"]
    coverage = int(final_data["session"]["coverage_percent"])
    severity = final_data["issues"]

    passed = (
        status == "completed"
        and case.expected_min_findings <= findings_count <= case.expected_max_findings
        and case.expected_score_floor <= score <= case.expected_score_ceiling
    )
    mismatch_reason = ""
    if status != "completed":
        mismatch_reason = f"scan status was {status}"
    elif findings_count < case.expected_min_findings or findings_count > case.expected_max_findings:
        mismatch_reason = f"findings_count={findings_count} outside expected range {case.expected_min_findings}-{case.expected_max_findings}"
    elif score < case.expected_score_floor or score > case.expected_score_ceiling:
        mismatch_reason = f"score={score} outside expected range {case.expected_score_floor}-{case.expected_score_ceiling}"

    severity_match = True
    if case.expected_severities:
      severity_match = all(int(severity.get(key, 0)) >= value for key, value in case.expected_severities.items())

    return {
        "name": case.name,
        "status": status,
        "expected_kind": case.expected_kind,
        "coverage_percent": coverage,
        "security_score": score,
        "findings_count": findings_count,
        "candidate_findings_count": candidate_findings_count,
        "severity": severity,
        "severity_match": severity_match,
        "score_expectation": build_score_expectation(score, coverage, findings_count, candidate_findings_count),
        "passed": passed,
        "mismatch_reason": mismatch_reason,
        "tags": list(case.tags),
    }


if __name__ == "__main__":
    print(json.dumps(run_eval_suite(), indent=2))
