from __future__ import annotations

from pathlib import Path

from app.infrastructure.services.remediation_policy import normalize_category
from app.infrastructure.services.repository_analysis import run_precise_heuristics


SUPPORTED_VERIFY_CATEGORIES = {
    "sql injection",
    "command injection",
    "server-side request forgery",
    "ssrf",
    "nosql injection",
    "authentication bypass",
    "session fixation",
    "privilege escalation",
    "open redirect",
    "path traversal",
}


def verify_applied_patch(
    *,
    source_root: Path,
    target_file: str,
    finding_category: str,
    finding_line: int,
) -> dict:
    target_path = (source_root / target_file).resolve()
    if not target_path.exists():
        return {
            "status": "manual_review_required",
            "notes": ["The patched file could not be read after apply. Manual verification is required."],
            "confidence": None,
            "confidence_valid": False,
        }

    category = normalize_category(finding_category)
    if category not in SUPPORTED_VERIFY_CATEGORIES:
        return {
            "status": "manual_review_required",
            "notes": ["Deterministic post-fix verification is not available for this vulnerability category yet."],
            "confidence": None,
            "confidence_valid": False,
        }

    text = target_path.read_text(encoding="utf-8", errors="ignore")
    findings = run_precise_heuristics(target_path, text, source_root)
    matching = [
        item
        for item in findings
        if normalize_category(str(item.get("category", ""))) == category
        and abs(int(item.get("line", finding_line)) - int(finding_line)) <= 6
    ]
    if matching:
        titles = ", ".join(sorted({str(item.get("title", "security finding")) for item in matching[:3]}))
        return {
            "status": "manual_review_required",
            "notes": [
                "Deterministic verification still sees a related vulnerable pattern near the patched sink.",
                f"Remaining signal: {titles}.",
                "Review the applied patch and re-scan the updated repository before closing this finding.",
            ],
            "confidence": None,
            "confidence_valid": False,
        }

    return {
        "status": "verified",
        "notes": [
            "Deterministic verification no longer detects the same vulnerable pattern in the patched file.",
            "A broader repository re-scan is still recommended to confirm dependent paths and surrounding logic.",
        ],
        "confidence": 84,
        "confidence_valid": True,
    }
