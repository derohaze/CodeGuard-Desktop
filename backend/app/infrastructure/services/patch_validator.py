from pathlib import Path

from app.domain.entities.patch_application import FixType
from app.infrastructure.services.runtime_safety_policy import ensure_safe_patch_target


def validate_patch_application(
    *,
    source_root: Path,
    target_file: str,
    before_snippet: str,
    after_snippet: str,
    evidence_file: str,
    evidence_line: int,
    manual_edit: bool,
) -> tuple[bool, list[str], FixType]:
    notes: list[str] = []
    try:
        target_path = ensure_safe_patch_target(source_root=source_root, target_file=target_file)
    except ValueError as exc:
        return False, [str(exc)], "risky_workaround"

    text = target_path.read_text(encoding="utf-8", errors="ignore")
    if not after_snippet.strip():
        return False, ["The generated patch does not contain an updated code snippet."], "risky_workaround"

    if before_snippet.strip() and before_snippet not in text:
        resolved = _resolve_snippet_match(text, before_snippet)
        if resolved is None:
            if evidence_line <= 0:
                return False, ["The original code snippet no longer matches the file on disk. Refresh the remediation plan first."], "risky_workaround"
            notes.append("Original snippet mismatch; applying patch anchored at the evidence line. Review the result carefully.")
        else:
            notes.append("Using a normalized match of the original snippet for patch application.")

    if manual_edit:
        notes.append("Manual edit mode was used before apply.")

    if evidence_file == target_file:
        notes.append("The patch targets the file that contains the traced sink.")
    else:
        notes.append("The patch targets a related file outside the direct sink location. Manual review is required.")

    if "TODO" in after_snippet or "pass" == after_snippet.strip():
        return False, notes + ["The edited patch looks incomplete or placeholder-like."], "risky_workaround"

    fix_type: FixType = "full_fix"
    lowered = after_snippet.lower()
    if any(token in lowered for token in ("if not", "raise httpexception", "return none", "return false")):
        fix_type = "temporary_guard"
        notes.append("This patch behaves like a guard or fail-fast mitigation.")
    elif any(token in lowered for token in ("%s", "preparedstatement", "parameter", "bind")):
        fix_type = "full_fix"
        notes.append("The patch introduces a structured sink protection pattern.")
    else:
        fix_type = "partial_mitigation"
        notes.append("The patch reduces risk, but manual review should confirm complete remediation.")

    notes.append(f"Evidence anchor remains {evidence_file}:{evidence_line}.")
    return True, notes, fix_type


def _resolve_snippet_match(text: str, snippet: str) -> str | None:
    if not snippet.strip():
        return None
    if snippet in text:
        return snippet
    if len(snippet.strip()) < 12:
        return None

    compact_text, index_map = _compact_with_index(text)
    compact_snippet, _ = _compact_with_index(snippet)
    if not compact_snippet:
        return None
    match_index = compact_text.find(compact_snippet)
    if match_index == -1:
        return None
    start = index_map[match_index]
    end = index_map[match_index + len(compact_snippet) - 1] + 1
    return text[start:end]


def _compact_with_index(value: str) -> tuple[str, list[int]]:
    compact_chars: list[str] = []
    index_map: list[int] = []
    for idx, char in enumerate(value):
        if char.isspace():
            continue
        compact_chars.append(char)
        index_map.append(idx)
    return "".join(compact_chars), index_map
