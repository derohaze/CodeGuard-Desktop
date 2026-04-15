from pathlib import Path

from app.infrastructure.services.repository.repository_analysis import read_text, relative_path


AUTH_MARKERS = ("jwt", "token", "session", "auth", "bearer", "csrf", "login", "graphqlauth", "httpsession", "filter", "securitycontext")


def detect_auth_boundaries(source_root: Path, files: list[Path]) -> list[dict]:
    boundaries: list[dict] = []
    for path in files:
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".php", ".java", ".go", ".jsp", ".jspf", ".xml"}:
            continue
        text = read_text(path).lower()
        markers = [marker for marker in AUTH_MARKERS if marker in text or marker in path.name.lower()]
        if not markers:
            continue
        boundaries.append({"file": relative_path(path, source_root), "markers": markers})
    return boundaries
