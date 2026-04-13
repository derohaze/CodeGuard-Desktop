from __future__ import annotations

from app.domain.entities.scan import ScanSessionEntity
from app.infrastructure.services.workflow_summary import build_workflow_summary


def build_workflow_team_posture_hotspots(sessions: list[ScanSessionEntity]) -> list[dict]:
    hotspots: list[dict] = []
    for session in sessions:
        workflow = build_workflow_summary(session)
        hotspot_class = classify_hotspot(session, workflow)
        if hotspot_class is None:
            continue
        hotspots.append(
            {
                "session_id": session.id,
                "repo": session.repo,
                "status": session.status,
                "hotspot_class": hotspot_class,
                "priority": classify_priority(session, hotspot_class),
                "finding_count": len(session.findings),
                "coverage_percent": session.coverage_percent,
            }
        )
    return sorted(hotspots, key=lambda item: (-priority_weight(item["priority"]), item["repo"]))


def summarize_workflow_team_posture_hotspots(sessions: list[ScanSessionEntity], hotspots: list[dict]) -> dict:
    top_hotspot = hotspots[0] if hotspots else None
    return {
        "session_count": len(sessions),
        "hotspot_count": len(hotspots),
        "critical_hotspots": sum(1 for item in hotspots if item["priority"] == "critical"),
        "control_drag": sum(1 for item in hotspots if item["hotspot_class"] == "control-drag"),
        "risk_drag": sum(1 for item in hotspots if item["hotspot_class"] == "risk-drag"),
        "coverage_drag": sum(1 for item in hotspots if item["hotspot_class"] == "coverage-drag"),
        "throughput_drag": sum(1 for item in hotspots if item["hotspot_class"] == "throughput-drag"),
        "top_hotspot_label": f"{top_hotspot['priority']} - {top_hotspot['repo']}" if top_hotspot else "No active team hotspot",
    }


def classify_hotspot(session: ScanSessionEntity, workflow: dict | None) -> str | None:
    if session.status in {"failed", "queued", "scanning"}:
        return "throughput-drag"
    if (workflow or {}).get("workflow_closure", {}).get("requires_human_control") or (workflow or {}).get("state") == "approval-control":
        return "control-drag"
    if sum(1 for item in session.findings if item.severity == "critical") > 0 or (session.security_score is not None and session.security_score <= 75):
        return "risk-drag"
    if session.coverage_percent < 90 or session.skipped_files_count > 0 or len(session.candidate_findings) > 0:
        return "coverage-drag"
    return None


def classify_priority(session: ScanSessionEntity, hotspot_class: str) -> str:
    if session.status == "failed" or hotspot_class == "control-drag" or sum(1 for item in session.findings if item.severity == "critical") > 0 or (session.security_score is not None and session.security_score <= 70):
        return "critical"
    if hotspot_class in {"throughput-drag", "risk-drag"} or session.coverage_percent < 85:
        return "high"
    return "normal"


def priority_weight(value: str) -> int:
    return {"critical": 3, "high": 2, "normal": 1}.get(value, 0)
