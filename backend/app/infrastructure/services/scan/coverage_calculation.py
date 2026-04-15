from __future__ import annotations


PHASE_ORDER = [
    "Discovery",
    "Repository mapping",
    "Segmentation",
    "Path tracing",
    "Reviewing paths",
    "Validation",
    "Scoring",
]

PHASE_WEIGHTS = {
    "Discovery": 10,
    "Repository mapping": 20,
    "Segmentation": 10,
    "Path tracing": 10,
    "Reviewing paths": 35,
    "Validation": 10,
    "Scoring": 5,
}


def _ratio(done: int | float, total: int | float) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((max(0, done) / total) * 100)))


def build_progress_state(current_phase: str, counters: dict | None = None) -> dict:
    counters = counters or {}
    if current_phase == "Completed":
        return {
            "progress": 100,
            "phase_progress": 100,
            "progress_counters": counters,
        }
    if current_phase == "Failed":
        return {
            "progress": 100,
            "phase_progress": 100,
            "progress_counters": counters,
        }
    normalized_phase = current_phase if current_phase in PHASE_WEIGHTS else "Discovery"
    phase_progress = _compute_phase_progress(normalized_phase, counters)

    overall = 0.0
    for phase in PHASE_ORDER:
        weight = PHASE_WEIGHTS[phase]
        if PHASE_ORDER.index(phase) < PHASE_ORDER.index(normalized_phase):
            overall += weight
            continue
        if phase == normalized_phase:
            overall += weight * (phase_progress / 100)
        break

    return {
        "progress": max(0, min(100, round(overall))),
        "phase_progress": max(0, min(100, phase_progress)),
        "progress_counters": counters,
    }


def _compute_phase_progress(current_phase: str, counters: dict) -> int:
    if current_phase == "Discovery":
        return _ratio(int(counters.get("files_indexed", 0)), int(counters.get("files_total", 0)))
    if current_phase == "Repository mapping":
        artifact_progress = _ratio(int(counters.get("mapping_artifacts_ready", counters.get("mapping_units_completed", 0))), int(counters.get("mapping_artifacts_total", counters.get("mapping_units_total", 0))))
        ai_progress = _ratio(int(counters.get("mapping_ai_steps_completed", 0)), int(counters.get("mapping_ai_steps_total", 0)))
        if int(counters.get("mapping_ai_steps_total", 0)) > 0:
            return round((artifact_progress * 0.65) + (ai_progress * 0.35))
        return artifact_progress
    if current_phase == "Segmentation":
        return _ratio(int(counters.get("files_segmented", 0)), int(counters.get("files_to_segment", 0)))
    if current_phase == "Path tracing":
        queue_progress = _ratio(int(counters.get("review_items_prepared", 0)), int(counters.get("review_items_total", 0)))
        path_progress = _ratio(int(counters.get("paths_prepared", 0)), int(counters.get("paths_total", 0)))
        if int(counters.get("review_items_total", 0)) > 0:
            return round((path_progress * 0.55) + (queue_progress * 0.45))
        return path_progress
    if current_phase == "Reviewing paths":
        block_progress = _ratio(int(counters.get("blocks_reviewed", 0)), int(counters.get("blocks_total", 0)))
        batch_progress = _ratio(int(counters.get("review_batches_completed", 0)), int(counters.get("review_batches_total", 0)))
        path_progress = _ratio(int(counters.get("paths_reviewed", 0)), int(counters.get("paths_total", 0)))
        if int(counters.get("review_batches_total", 0)) > 0:
            return round((block_progress * 0.6) + (batch_progress * 0.25) + (path_progress * 0.15))
        return round((block_progress * 0.75) + (path_progress * 0.25))
    if current_phase == "Validation":
        candidate_progress = _ratio(int(counters.get("candidates_validated", 0)), int(counters.get("candidates_total", 0)))
        review_progress = _ratio(int(counters.get("validation_artifacts_ready", 0)), int(counters.get("validation_artifacts_total", 0)))
        if int(counters.get("validation_artifacts_total", 0)) > 0:
            return round((candidate_progress * 0.75) + (review_progress * 0.25))
        return candidate_progress
    if current_phase == "Scoring":
        return _ratio(int(counters.get("artifacts_finalized", 0)), int(counters.get("artifacts_total", 0)))
    if current_phase in {"Completed", "Failed"}:
        return 100
    return 0


def calculate_progress_metrics(
    *,
    reviewed_files_count: int,
    eligible_files_count: int,
    blocks_reviewed: int,
    blocks_total: int,
    paths_traced: int,
    paths_total: int,
    validated_findings_count: int,
    candidate_findings_count: int,
    coverage_percent: int,
) -> dict:
    return {
        "reviewed_files_count": max(0, reviewed_files_count),
        "eligible_files_count": max(0, eligible_files_count),
        "reviewed_blocks_count": max(0, blocks_reviewed),
        "total_blocks_count": max(0, blocks_total),
        "traced_paths_count": max(0, paths_traced),
        "total_paths_count": max(0, paths_total),
        "validated_findings_count": max(0, validated_findings_count),
        "candidate_findings_count": max(0, candidate_findings_count),
        "coverage_percent": max(0, min(100, coverage_percent)),
    }
