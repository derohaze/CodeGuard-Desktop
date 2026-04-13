from pathlib import Path
from tempfile import NamedTemporaryFile


def apply_patch_locally(
    *,
    source_root: Path,
    target_file: str,
    before_snippet: str,
    after_snippet: str,
    evidence_line: int,
) -> Path:
    target_path = (source_root / target_file).resolve()
    text = target_path.read_text(encoding="utf-8", errors="ignore")

    resolved_snippet = _resolve_snippet_match(text, before_snippet)
    if resolved_snippet:
        updated = text.replace(resolved_snippet, after_snippet, 1)
    elif evidence_line > 0 and after_snippet.strip():
        updated = _apply_anchor_patch(text, after_snippet, before_snippet, evidence_line)
    else:
        updated = after_snippet

    _atomic_write_text(target_path, updated)
    return target_path


def restore_patch_checkpoint(*, target_path: Path, original_content: str) -> Path:
    _atomic_write_text(target_path, original_content)
    return target_path


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


def _apply_anchor_patch(text: str, after_snippet: str, before_snippet: str, evidence_line: int) -> str:
    lines = text.splitlines(keepends=True)
    if not lines:
        return after_snippet

    span = max(1, len(before_snippet.splitlines()) if before_snippet.strip() else 1)
    start = max(0, min(len(lines) - 1, evidence_line - 1))
    end = min(len(lines), start + span)
    replacement = after_snippet
    if not replacement.endswith("\n") and end < len(lines):
        replacement += "\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:])


def _atomic_write_text(target_path: Path, content: str) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target_path.parent, suffix=target_path.suffix) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(target_path)
