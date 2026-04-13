from pathlib import Path

from app.infrastructure.services.repository_analysis import read_text


def extract_evidence(path: Path, line_start: int, line_end: int | None = None, radius: int = 2) -> dict:
    content = read_text(path)
    lines = content.splitlines()
    if not lines:
        return {
            "line_start": max(1, line_start),
            "line_end": max(1, line_end or line_start),
            "snippet": "",
        }

    resolved_start = max(1, min(len(lines), line_start))
    resolved_end = max(resolved_start, min(len(lines), line_end or line_start))
    snippet_start = max(1, resolved_start - radius)
    snippet_end = min(len(lines), resolved_end + radius)
    snippet = "\n".join(
        f"{index}: {lines[index - 1]}"
        for index in range(snippet_start, snippet_end + 1)
    )
    return {
        "line_start": resolved_start,
        "line_end": resolved_end,
        "snippet": snippet,
    }
