from __future__ import annotations

from app.domain.entities.scan import ScanSessionEntity


def build_workflow_repo_hotspots(session: ScanSessionEntity) -> list[dict]:
    hotspots: list[dict] = []
    segmentation = session.segmentation_summary or {}
    registry = session.security_registry or {}
    graph = session.graph_summary or {}

    identity_count = count_value(segmentation.get("identity_surfaces")) + count_value(registry.get("auth_components"))
    if identity_count > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "identity-zone", "priority": "critical" if identity_count >= 3 else "high", "label": "Identity surfaces"})

    exposure_count = count_value(graph.get("external_surfaces")) + count_value(graph.get("trust_boundaries")) + count_value(registry.get("network_boundaries"))
    if exposure_count > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "exposure-zone", "priority": "critical" if exposure_count >= 4 else "high", "label": "Exposure boundaries"})

    data_count = count_value(registry.get("data_sinks")) + count_value(registry.get("user_inputs"))
    if data_count > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "data-zone", "priority": "high" if data_count >= 5 else "normal", "label": "Input and sink pressure"})

    if session.coverage_percent < 100 or session.skipped_files_count > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "coverage-zone", "priority": "high" if session.coverage_percent < 85 else "normal", "label": "Coverage gaps"})

    return sorted(hotspots, key=lambda item: (-priority_weight(item["priority"]), item["label"]))


def summarize_workflow_repo_hotspots(sessions: list[ScanSessionEntity], hotspots: list[dict]) -> dict:
    top_hotspot = hotspots[0] if hotspots else None
    repo_counts: dict[str, int] = {}
    for item in hotspots:
        repo_counts[item["repo"]] = repo_counts.get(item["repo"], 0) + 1
    return {
        "session_count": len(sessions),
        "hotspot_count": len(hotspots),
        "critical_hotspots": sum(1 for item in hotspots if item["priority"] == "critical"),
        "identity_zones": sum(1 for item in hotspots if item["hotspot_class"] == "identity-zone"),
        "exposure_zones": sum(1 for item in hotspots if item["hotspot_class"] == "exposure-zone"),
        "data_zones": sum(1 for item in hotspots if item["hotspot_class"] == "data-zone"),
        "coverage_zones": sum(1 for item in hotspots if item["hotspot_class"] == "coverage-zone"),
        "top_hotspot_label": f"{top_hotspot['priority']} - {top_hotspot['label']}" if top_hotspot else "No repository hotspot",
        "top_repositories": repo_counts,
    }


def count_value(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, str) and value.strip():
        return 1
    return 0


def priority_weight(value: str) -> int:
    return {"critical": 3, "high": 2, "normal": 1}.get(value, 0)
