from __future__ import annotations

from app.domain.entities.scan import ScanSessionEntity


def build_workflow_service_exposure_hotspots(session: ScanSessionEntity) -> list[dict]:
    graph = session.graph_summary or {}
    repository_graph = session.repository_graph or {}
    registry = session.security_registry or {}
    path_summary = session.path_summary or {}
    hotspots: list[dict] = []

    boundary_signals = count_value(graph.get("trust_boundaries")) + count_value(repository_graph.get("service_boundaries"))
    if boundary_signals > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "boundary-drag", "priority": "critical" if boundary_signals >= 4 else "high", "label": "Trust boundary drag"})

    network_signals = count_value(registry.get("network_boundaries")) + count_value(repository_graph.get("external_calls"))
    if network_signals > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "network-drag", "priority": "high" if network_signals >= 3 else "normal", "label": "Network drag"})

    path_signals = max(session.traced_paths_count, count_value(path_summary))
    if path_signals > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "path-drag", "priority": "high" if path_signals >= 8 else "normal", "label": "Path concentration"})

    entrypoint_signals = count_value(graph.get("external_surfaces")) + count_value(repository_graph.get("public_entrypoints"))
    if entrypoint_signals > 0:
        hotspots.append({"session_id": session.id, "repo": session.repo, "hotspot_class": "entrypoint-drag", "priority": "critical" if entrypoint_signals >= 3 else "high", "label": "Entrypoint exposure"})

    return sorted(hotspots, key=lambda item: (-priority_weight(item["priority"]), item["label"]))


def summarize_workflow_service_exposure_hotspots(sessions: list[ScanSessionEntity], hotspots: list[dict]) -> dict:
    top_hotspot = hotspots[0] if hotspots else None
    service_counts: dict[str, int] = {}
    for item in hotspots:
        service_counts[item["repo"]] = service_counts.get(item["repo"], 0) + 1
    return {
        "session_count": len(sessions),
        "hotspot_count": len(hotspots),
        "critical_hotspots": sum(1 for item in hotspots if item["priority"] == "critical"),
        "boundary_drag": sum(1 for item in hotspots if item["hotspot_class"] == "boundary-drag"),
        "network_drag": sum(1 for item in hotspots if item["hotspot_class"] == "network-drag"),
        "path_drag": sum(1 for item in hotspots if item["hotspot_class"] == "path-drag"),
        "entrypoint_drag": sum(1 for item in hotspots if item["hotspot_class"] == "entrypoint-drag"),
        "top_hotspot_label": f"{top_hotspot['priority']} - {top_hotspot['label']}" if top_hotspot else "No exposure hotspot",
        "top_services": service_counts,
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
