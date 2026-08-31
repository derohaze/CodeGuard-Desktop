import type { ScanSessionDetail } from "@/shared/api/security";

export interface ExposureHotspot {
  id: string;
  label: string;
  hotspotClass: "boundary-drag" | "network-drag" | "path-drag" | "entrypoint-drag";
  priority: "critical" | "high" | "normal";
  evidence: string;
  nextAction: string;
}

export interface ExposureHotspotSummary {
  hotspotCount: number;
  criticalHotspots: number;
  boundaryDrag: number;
  networkDrag: number;
  pathDrag: number;
  entrypointDrag: number;
  topHotspotLabel: string;
}

export function buildExposureHotspots(session: ScanSessionDetail): ExposureHotspot[] {
  const graph = session.session.graphSummary;
  const repositoryGraph = session.session.repositoryGraph;
  const registry = session.session.securityRegistry;
  const pathSummary = session.session.pathSummary;
  const hotspots: ExposureHotspot[] = [];

  const boundarySignals = countValue(graph?.trust_boundaries) + countValue(repositoryGraph?.service_boundaries);
  if (boundarySignals > 0) {
    hotspots.push({
      id: "boundary-drag",
      label: "Trust boundary drag",
      hotspotClass: "boundary-drag",
      priority: boundarySignals >= 4 ? "critical" : "high",
      evidence: `${boundarySignals} trust-boundary and service-boundary signal(s) are active in the current run.`,
      nextAction: "Review trust boundaries before reducing repository-level review pressure.",
    });
  }

  const networkSignals = countValue(registry?.network_boundaries) + countValue(repositoryGraph?.external_calls);
  if (networkSignals > 0) {
    hotspots.push({
      id: "network-drag",
      label: "Network drag",
      hotspotClass: "network-drag",
      priority: networkSignals >= 3 ? "high" : "normal",
      evidence: `${networkSignals} network and external-call signal(s) remain exposed in the current registry.`,
      nextAction: "Validate outbound and inbound network surfaces before treating exposure posture as stable.",
    });
  }

  const pathSignals = Math.max(session.session.tracedPathsCount, countValue(pathSummary));
  if (pathSignals > 0) {
    hotspots.push({
      id: "path-drag",
      label: "Path concentration",
      hotspotClass: "path-drag",
      priority: pathSignals >= 8 ? "high" : "normal",
      evidence: `${session.session.tracedPathsCount}/${session.session.totalPathsCount || session.session.tracedPathsCount} traced path(s) remain active in the current run.`,
      nextAction: "Correlate dominant paths with exposed services before relaxing investigation depth.",
    });
  }

  const entrypointSignals = countValue(graph?.external_surfaces) + countValue(repositoryGraph?.public_entrypoints);
  if (entrypointSignals > 0) {
    hotspots.push({
      id: "entrypoint-drag",
      label: "Entrypoint exposure",
      hotspotClass: "entrypoint-drag",
      priority: entrypointSignals >= 3 ? "critical" : "high",
      evidence: `${entrypointSignals} public-entry or external-surface signal(s) remain active in the current graph.`,
      nextAction: "Review exposed entrypoints before expanding autonomous handling across services.",
    });
  }

  return hotspots.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }

    return left.label.localeCompare(right.label);
  });
}

export function summarizeExposureHotspots(hotspots: ExposureHotspot[]): ExposureHotspotSummary {
  const criticalHotspots = hotspots.filter((item) => item.priority === "critical").length;
  const boundaryDrag = hotspots.filter((item) => item.hotspotClass === "boundary-drag").length;
  const networkDrag = hotspots.filter((item) => item.hotspotClass === "network-drag").length;
  const pathDrag = hotspots.filter((item) => item.hotspotClass === "path-drag").length;
  const entrypointDrag = hotspots.filter((item) => item.hotspotClass === "entrypoint-drag").length;
  const topHotspot = hotspots[0] ?? null;

  return {
    hotspotCount: hotspots.length,
    criticalHotspots,
    boundaryDrag,
    networkDrag,
    pathDrag,
    entrypointDrag,
    topHotspotLabel: topHotspot ? `${topHotspot.priority} - ${topHotspot.label}` : "No exposure hotspot",
  };
}

function countValue(value: unknown) {
  if (Array.isArray(value)) return value.length;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (value && typeof value === "object") return Object.keys(value as Record<string, unknown>).length;
  if (typeof value === "string" && value.trim().length > 0) return 1;
  return 0;
}

function priorityWeight(value: ExposureHotspot["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
