from pathlib import Path
from typing import Any

from app.domain.entities.scan import FindingEntity, ScanSessionEntity
from app.infrastructure.services.repository.evidence_extraction import extract_evidence
from app.infrastructure.services.repository.file_parsing import detect_language


def build_remediation_context(session: ScanSessionEntity, finding: FindingEntity) -> dict[str, Any]:
    source_root = _resolve_source_root(session)
    target_path = (source_root / finding.file).resolve()
    path_artifact = _resolve_path_artifact(session, finding)
    source_ref = _parse_location_hint(path_artifact.get("source_hint") or finding.attack_input)
    sink_ref = _parse_location_hint(path_artifact.get("sink_hint") or f"{finding.file}:{finding.line}")
    code_window = _extract_window(target_path, finding.line, finding.line_end)
    source_window = _extract_hint_window(source_root, source_ref)
    sink_window = _extract_hint_window(source_root, sink_ref)

    return {
        "project_name": session.repo,
        "session_id": session.id,
        "source_root": str(source_root),
        "scan_mode": session.scan_mode,
        "framework_profile": session.framework_profile or {},
        "finding": {
            "id": finding.id,
            "title": finding.title,
            "severity": finding.severity,
            "category": finding.category,
            "confidence": finding.confidence,
            "file": finding.file,
            "line": finding.line,
            "line_end": finding.line_end,
            "summary": finding.summary,
            "impact": finding.impact,
            "explanation": finding.explanation,
            "evidence": finding.evidence,
            "attack_input": finding.attack_input,
            "attack_execution": finding.attack_execution,
            "attack_result": finding.attack_result,
        },
        "path": {
            "path_hint": path_artifact.get("path_hint", finding.attack_execution),
            "path_type": path_artifact.get("path_type", "unknown"),
            "source_hint": path_artifact.get("source_hint", ""),
            "sink_hint": path_artifact.get("sink_hint", ""),
            "line_sequence": path_artifact.get("line_sequence", []),
            "cross_file": bool(path_artifact.get("path_type") == "cross_file"),
        },
        "code": {
            "file": finding.file,
            "language": detect_language(target_path),
            "window": code_window,
            "source_window": source_window,
            "sink_window": sink_window,
        },
    }


def build_batch_remediation_context(session: ScanSessionEntity, findings: list[FindingEntity]) -> dict[str, Any]:
    finding_contexts = [build_remediation_context(session, finding) for finding in findings]
    return {
        "project_name": session.repo,
        "session_id": session.id,
        "scan_mode": session.scan_mode,
        "framework_profile": session.framework_profile or {},
        "findings": finding_contexts,
    }


def count_analyzed_lines(context: dict[str, Any]) -> int:
    window = context.get("code", {}).get("window", {})
    line_start = int(window.get("line_start", context.get("finding", {}).get("line", 0)) or 0)
    line_end = int(window.get("line_end", context.get("finding", {}).get("line_end", 0)) or 0)
    if line_start > 0 and line_end >= line_start:
        return (line_end - line_start) + 1
    snippet = str(window.get("snippet", "")).strip()
    return len(snippet.splitlines()) if snippet else 0


def count_path_steps(context: dict[str, Any], explanation: Any | None = None) -> int:
    line_sequence = context.get("path", {}).get("line_sequence", [])
    if isinstance(line_sequence, list) and line_sequence:
        return len(line_sequence)
    if explanation is not None and getattr(explanation, "attack_steps", None):
        return len(explanation.attack_steps)
    path_hint = str(context.get("path", {}).get("path_hint", "")).strip()
    if "->" in path_hint:
        return len([part for part in path_hint.split("->") if part.strip()])
    return 1 if path_hint else 0


def locate_finding(session: ScanSessionEntity, finding_id: str) -> FindingEntity | None:
    for finding in session.findings:
        if finding.id == finding_id:
            return finding
    return None


def _resolve_source_root(session: ScanSessionEntity) -> Path:
    source_path = Path(session.source_path).expanduser().resolve()
    return source_path if source_path.is_dir() else source_path.parent


def _resolve_path_artifact(session: ScanSessionEntity, finding: FindingEntity) -> dict[str, Any]:
    raw_inventory = session.path_inventory or {}
    raw_paths = raw_inventory.get("paths") if isinstance(raw_inventory, dict) else []
    if not isinstance(raw_paths, list):
        return {}

    for item in raw_paths:
        if not isinstance(item, dict):
            continue
        sink = item.get("sink", {})
        if not isinstance(sink, dict):
            continue
        if str(sink.get("file", "")) == finding.file and int(sink.get("line", 0) or 0) == finding.line:
            return {
                "path_hint": str(item.get("path_hint", "")),
                "path_type": str(item.get("path_type", "")),
                "source_hint": _location_to_hint(item.get("source")),
                "sink_hint": _location_to_hint(item.get("sink")),
                "line_sequence": [int(line) for line in item.get("line_sequence", []) if int(line) > 0],
            }

    return {
        "path_hint": finding.attack_execution,
        "source_hint": "",
        "sink_hint": f"{finding.file}:{finding.line}",
        "line_sequence": [],
    }


def _location_to_hint(location: Any) -> str:
    if not isinstance(location, dict):
        return ""
    file_path = str(location.get("file", "")).strip()
    line = int(location.get("line", 0) or 0)
    if not file_path or line <= 0:
        return ""
    return f"{file_path}:{line}"


def _parse_location_hint(value: str) -> tuple[str, int] | None:
    if not value or ":" not in value:
        return None
    parts = value.rsplit(":", 1)
    file_path = parts[0].strip()
    try:
        line = int(parts[1].strip())
    except ValueError:
        return None
    if not file_path or line <= 0:
        return None
    return (file_path, line)


def _extract_window(path: Path, line_start: int, line_end: int, radius: int = 8) -> dict[str, Any]:
    if not path.exists():
        return {"snippet": "", "line_start": line_start, "line_end": line_end}
    return extract_evidence(path, line_start, line_end, radius=radius)


def _extract_hint_window(source_root: Path, location: tuple[str, int] | None) -> dict[str, Any] | None:
    if location is None:
        return None
    file_path, line = location
    path = (source_root / file_path).resolve()
    if not path.exists():
        return None
    evidence = extract_evidence(path, line, line, radius=4)
    return {
        "file": file_path,
        "line_start": evidence["line_start"],
        "line_end": evidence["line_end"],
        "snippet": evidence["snippet"],
    }
