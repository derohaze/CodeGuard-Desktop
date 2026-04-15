from __future__ import annotations

from app.domain.entities.scan import FindingEntity, ScanSessionEntity
from app.infrastructure.services.scan.score_calibration import calibrate_security_score


def build_post_remediation_updates(
    *,
    session: ScanSessionEntity,
    applied_finding: FindingEntity,
    validation_notes: list[str],
    verification: dict | None = None,
) -> dict:
    verification = verification or {"status": "manual_review_required", "notes": []}
    verification_verified = str(verification.get("status", "")) == "verified"
    remaining_findings = [item for item in session.findings if item.id != applied_finding.id] if verification_verified else list(session.findings)
    if verification_verified:
        remaining_annotations = [
            item
            for item in session.annotations
            if not _annotation_matches_finding(item, applied_finding)
        ]
    else:
        remaining_annotations = list(session.annotations)
    score_calibration = calibrate_security_score(
        validated_findings=remaining_findings,
        candidate_findings=session.candidate_findings,
        coverage_snapshot=session.coverage_snapshot or {"coverage_percent": session.coverage_percent},
        framework_profile=session.framework_profile,
        path_summary=session.path_summary,
    )
    remaining_count = len(remaining_findings)
    logs = list(session.progress_logs[-11:])
    if verification_verified:
        logs.append(
            f"Applied and verified a local remediation for {applied_finding.file}:{applied_finding.line}. "
            f"{remaining_count} validated finding(s) remain."
        )
    else:
        logs.append(
            f"Applied a local remediation for {applied_finding.file}:{applied_finding.line}, but follow-up verification still requires review."
        )
    return {
        "findings": remaining_findings,
        "annotations": remaining_annotations,
        "annotation_summary": {
            "ready_annotations": len(remaining_annotations),
            "red_annotations": sum(1 for item in remaining_annotations if item.get("tone") == "red"),
            "yellow_annotations": sum(1 for item in remaining_annotations if item.get("tone") == "yellow"),
        },
        "review_queue_summary": {
            **(session.review_queue_summary or {}),
            "current_validated_findings_count": remaining_count,
            "current_candidate_findings_count": len(session.candidate_findings),
        },
        "is_safe": remaining_count == 0,
        "security_score": score_calibration["score"],
        "score_rationale": score_calibration["rationale"],
        "preview": _build_preview(
            findings=remaining_findings,
            file_count=session.reviewed_files_count or session.eligible_files_count,
            reviewed_hotspots=int((session.repository_inventory or {}).get("reviewed_hotspots", 0) or 0),
        ),
        "repository_summary": _build_repository_summary(
            session=session,
            remaining_findings=remaining_findings,
            validation_notes=validation_notes,
            verification=verification,
        ),
        "progress_logs": logs,
        "unread": True,
    }


def _annotation_matches_finding(annotation: dict, finding: FindingEntity) -> bool:
    file_path = str(annotation.get("file", "")).strip()
    line_start = int(annotation.get("lineStart", 0) or 0)
    line_end = int(annotation.get("lineEnd", line_start) or line_start)
    title = str(annotation.get("title", "")).strip().lower()
    return (
        file_path == finding.file
        and line_start == finding.line
        and line_end == finding.line_end
        and title == finding.title.strip().lower()
    )


def _build_preview(*, findings: list[FindingEntity], file_count: int, reviewed_hotspots: int) -> str:
    if not findings:
        return (
            f"Local remediation applied. Reviewed {file_count} files, prioritized {reviewed_hotspots} hotspots, "
            "and no validated finding currently remains open."
        )
    highest = findings[0]
    return (
        f"Local remediation applied. {len(findings)} validated finding(s) remain. Highest severity: "
        f"{highest.severity} in {highest.file}:{highest.line}."
    )


def _build_repository_summary(
    *,
    session: ScanSessionEntity,
    remaining_findings: list[FindingEntity],
    validation_notes: list[str],
    verification: dict,
) -> str:
    verification_verified = str(verification.get("status", "")) == "verified"
    if not remaining_findings and verification_verified:
        return (
            "A local remediation was applied, deterministic verification passed for the patched file, and no validated finding currently remains open in this saved scan. "
            "Run a fresh scan to confirm the full repository state after the code change."
        )
    if not verification_verified:
        lead = validation_notes[0] if validation_notes else "Local remediation was applied to one finding."
        return (
            f"{lead} Deterministic post-fix verification still requires review for this finding, so the saved scan keeps it open. "
            "Run a fresh scan after revising the patch."
        )
    note = validation_notes[0] if validation_notes else "Local remediation was applied to one finding."
    return (
        f"{note} {len(remaining_findings)} validated finding(s) still remain open in this saved scan. "
        "Run a fresh scan to verify the updated repository state."
    )
