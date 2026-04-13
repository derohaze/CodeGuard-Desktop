from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app
from evals.remediation_benchmark import REMEDIATION_BENCHMARK_CASES, TARGET_CATEGORY_RULES, normalize_category
from evals.remediation_reporting import build_remediation_summary


def run_remediation_benchmark() -> dict:
    client = TestClient(app)
    repo_results: list[dict] = []

    for case in REMEDIATION_BENCHMARK_CASES:
        if not case.local_path.exists():
            repo_results.append(
                {
                    "name": case.name,
                    "status": "missing_repo",
                    "source_path": str(case.local_path),
                    "remediation_findings": [],
                }
            )
            continue
        repo_results.append(_run_repo_case(client, case.name, case.local_path))

    return {
        "summary": build_remediation_summary(repo_results),
        "repos": repo_results,
    }


def _run_repo_case(client: TestClient, repo_name: str, source_path: Path) -> dict:
    started = time.perf_counter()
    response = client.post(
        "/api/v1/scans",
        json={
            "source_path": str(source_path),
            "target_type": "folder",
            "preset": "balanced",
            "scan_mode": "deep",
        },
    )
    response.raise_for_status()
    session_id = response.json()["session"]["id"]

    final_data = None
    for _ in range(600):
        detail = client.get(f"/api/v1/scans/{session_id}")
        detail.raise_for_status()
        final_data = detail.json()
        if final_data["session"]["status"] in {"completed", "failed"}:
            break
        time.sleep(0.5)

    elapsed_seconds = round(time.perf_counter() - started, 2)
    session = final_data["session"]
    findings = final_data.get("findings", [])
    remediation_findings = _evaluate_findings(client, session_id, findings)
    return {
        "name": repo_name,
        "status": session["status"],
        "coverage_percent": session["coverage_percent"],
        "files_reviewed": session["reviewed_files_count"],
        "files_total": session["eligible_files_count"],
        "blocks_reviewed": session["reviewed_blocks_count"],
        "blocks_total": session["total_blocks_count"],
        "paths_traced": session["traced_paths_count"],
        "paths_total": session["total_paths_count"],
        "validated_findings": len(findings),
        "candidate_findings": len(final_data.get("candidate_findings", [])),
        "security_score": session["security_score"],
        "elapsed_seconds": elapsed_seconds,
        "remediation_findings": remediation_findings,
    }


def _evaluate_findings(client: TestClient, session_id: str, findings: list[dict]) -> list[dict]:
    selected = _select_representative_findings(findings)
    evaluated: list[dict] = []
    for finding in selected:
        plan_response = client.post(
            "/api/v1/remediation/fix",
            json={"session_id": session_id, "finding_id": finding["id"]},
        )
        plan_response.raise_for_status()
        plan = plan_response.json()
        evaluated.append(_grade_remediation(finding, plan))
    return evaluated


def _select_representative_findings(findings: list[dict]) -> list[dict]:
    chosen: list[dict] = []
    seen_categories: set[str] = set()
    for finding in findings:
        category = normalize_category(str(finding.get("category", "")))
        if category in TARGET_CATEGORY_RULES and category not in seen_categories:
            chosen.append(finding)
            seen_categories.add(category)
        if len(chosen) >= 6:
            break
    if chosen:
        return chosen
    return findings[:3]


def _grade_remediation(finding: dict, plan: dict) -> dict:
    category = normalize_category(str(finding.get("category", "")))
    expected = TARGET_CATEGORY_RULES.get(category)
    strategies = plan.get("strategies", [])
    recommended = _recommended_strategy(plan, strategies)
    patch = plan.get("patch") or {}
    score = plan.get("score") or {}
    recommended_fix_type = str(recommended.get("fix_type", patch.get("fix_type", "partial_mitigation")))
    recommended_kind = str(recommended.get("kind", ""))
    recommendation_text = " ".join(
        [
            str(recommended.get("summary", "")),
            str(recommended.get("rationale", "")),
            str(recommended.get("selection_reason", "")),
            str(patch.get("rationale", "")),
            " ".join(patch.get("validation_notes", [])),
        ]
    ).lower()
    patch_file = str(patch.get("file", finding.get("file", ""))).replace("\\", "/").lower()
    finding_file = str(finding.get("file", "")).replace("\\", "/").lower()
    sink_aligned = patch_file == finding_file or any(token in patch_file for token in ("service", "dao", "repo", "query", "db"))
    residual_risk_clear = bool(patch.get("residual_risks")) or bool(recommended.get("residual_risks"))

    best_strategy_fit = True
    if expected is not None:
        must_mention_any = expected.get("must_mention_any", [])
        reject_if_mentions_any = expected.get("reject_if_mentions_any", [])
        best_strategy_fit = (
            recommended_fix_type == expected["preferred_fix_type"]
            and recommended_kind == expected["preferred_kind"]
            and (not must_mention_any or any(token in recommendation_text for token in must_mention_any))
            and not any(token in recommendation_text for token in reject_if_mentions_any)
        )

    quality_pass = best_strategy_fit and residual_risk_clear and sink_aligned
    return {
        "finding_id": finding["id"],
        "title": finding.get("title", ""),
        "category": finding.get("category", ""),
        "file": finding.get("file", ""),
        "recommended_strategy_id": plan.get("recommended_strategy_id"),
        "recommended_fix_type": recommended_fix_type,
        "recommended_kind": recommended_kind,
        "best_strategy_fit": best_strategy_fit,
        "sink_aligned": sink_aligned,
        "residual_risk_clear": residual_risk_clear,
        "quality_pass": quality_pass,
        "selection_reason": recommended.get("selection_reason", ""),
        "non_selection_reason": recommended.get("non_selection_reason", ""),
        "validation_notes": patch.get("validation_notes", []),
        "residual_risks": patch.get("residual_risks", []),
        "remediation_score": int(score.get("total", 0) or 0),
        "score_breakdown": {
            "strategy_quality": int(score.get("strategy_quality", 0) or 0),
            "fix_completeness": int(score.get("fix_completeness", 0) or 0),
            "sink_alignment": int(score.get("sink_alignment", 0) or 0),
            "residual_risk": int(score.get("residual_risk", 0) or 0),
            "confidence": int(score.get("confidence", 0) or 0),
        },
    }


def _recommended_strategy(plan: dict, strategies: list[dict]) -> dict:
    recommended_id = plan.get("recommended_strategy_id")
    for strategy in strategies:
        if strategy.get("id") == recommended_id:
            return strategy
    return strategies[0] if strategies else {}


if __name__ == "__main__":
    print(json.dumps(run_remediation_benchmark(), indent=2))
