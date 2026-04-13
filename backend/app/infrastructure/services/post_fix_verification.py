from __future__ import annotations

from pathlib import Path

from app.domain.entities.scan import FindingEntity
from app.infrastructure.services.repository_analysis import read_text, run_precise_heuristics


def verify_applied_fix(
    *,
    source_root: Path,
    file: str,
    finding: FindingEntity,
) -> dict:
    target_path = (source_root / file).resolve()
    if not target_path.exists():
        return {
            "status": "failed",
            "summary": "Post-fix verification could not read the affected file.",
            "notes": ["The affected file is no longer available on disk."],
            "matching_findings": [],
        }

    heuristics = run_precise_heuristics(target_path, read_text(target_path), source_root)
    normalized_category = finding.category.strip().lower()
    normalized_title = finding.title.strip().lower()
    matching = [
        item
        for item in heuristics
        if str(item.get("file", "")).strip() == file
        and (
            str(item.get("category", "")).strip().lower() == normalized_category
            or str(item.get("title", "")).strip().lower() == normalized_title
        )
    ]
    if matching:
        return {
            "status": "failed",
            "summary": "Post-fix verification still detected a matching vulnerable pattern in the affected file.",
            "notes": [
                "The automatic verify pass still found a matching vulnerability shape after the patch apply.",
                "Manual review or a stronger remediation strategy is required before closing this finding.",
            ],
            "matching_findings": matching[:4],
        }

    return {
        "status": "verified",
        "summary": "Post-fix verification did not detect the original vulnerable pattern in the affected file.",
        "notes": [
            "A targeted verify pass on the affected file no longer detected the original vulnerability shape.",
            "A broader re-scan remains recommended for full repository freshness.",
        ],
        "matching_findings": [],
    }
