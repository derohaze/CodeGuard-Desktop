import type { Session } from "@/entities/session/model/types";

export interface TeamPostureHotspot {
  session: Session;
  hotspotClass: "control-drag" | "risk-drag" | "coverage-drag" | "throughput-drag";
  priority: "critical" | "high" | "normal";
  nextAction: string;
}

export interface TeamPostureSummary {
  hotspotCount: number;
  criticalHotspots: number;
  controlDrag: number;
  riskDrag: number;
  coverageDrag: number;
  throughputDrag: number;
  topHotspotLabel: string;
}

export function buildTeamPostureHotspots(sessions: Session[]): TeamPostureHotspot[] {
  return sessions
    .map((session) => {
      const hotspotClass = classifyHotspot(session);
      if (!hotspotClass) {
        return null;
      }

      return {
        session,
        hotspotClass,
        priority: classifyPriority(session, hotspotClass),
        nextAction: buildNextAction(session, hotspotClass),
      } satisfies TeamPostureHotspot;
    })
    .filter((item): item is TeamPostureHotspot => item !== null)
    .sort((left, right) => {
      const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
      if (priorityDelta !== 0) {
        return priorityDelta;
      }

      const criticalDelta = right.session.criticalCount - left.session.criticalCount;
      if (criticalDelta !== 0) {
        return criticalDelta;
      }

      return left.session.repo.localeCompare(right.session.repo);
    });
}

export function summarizeTeamPostureHotspots(hotspots: TeamPostureHotspot[]): TeamPostureSummary {
  const criticalHotspots = hotspots.filter((item) => item.priority === "critical").length;
  const controlDrag = hotspots.filter((item) => item.hotspotClass === "control-drag").length;
  const riskDrag = hotspots.filter((item) => item.hotspotClass === "risk-drag").length;
  const coverageDrag = hotspots.filter((item) => item.hotspotClass === "coverage-drag").length;
  const throughputDrag = hotspots.filter((item) => item.hotspotClass === "throughput-drag").length;
  const topHotspot = hotspots[0] ?? null;

  return {
    hotspotCount: hotspots.length,
    criticalHotspots,
    controlDrag,
    riskDrag,
    coverageDrag,
    throughputDrag,
    topHotspotLabel: topHotspot ? `${topHotspot.priority} - ${topHotspot.session.repo}` : "No active team hotspot",
  };
}

function classifyHotspot(session: Session): TeamPostureHotspot["hotspotClass"] | null {
  if (session.status === "failed" || session.status === "queued" || session.status === "scanning") {
    return "throughput-drag";
  }
  if (session.workflowSummary?.workflowClosure?.requiresHumanControl || session.workflowSummary?.state === "approval-control") {
    return "control-drag";
  }
  if (session.criticalCount > 0 || (typeof session.securityScore === "number" && session.securityScore <= 75)) {
    return "risk-drag";
  }
  if (session.coveragePercent < 90 || session.skippedFilesCount > 0 || session.candidateFindingsCount > 0) {
    return "coverage-drag";
  }

  return null;
}

function classifyPriority(
  session: Session,
  hotspotClass: TeamPostureHotspot["hotspotClass"],
): TeamPostureHotspot["priority"] {
  if (
    session.status === "failed" ||
    hotspotClass === "control-drag" ||
    session.criticalCount > 0 ||
    (typeof session.securityScore === "number" && session.securityScore <= 70)
  ) {
    return "critical";
  }
  if (hotspotClass === "throughput-drag" || hotspotClass === "risk-drag" || session.coveragePercent < 85) {
    return "high";
  }
  return "normal";
}

function buildNextAction(
  session: Session,
  hotspotClass: TeamPostureHotspot["hotspotClass"],
) {
  if (hotspotClass === "throughput-drag") {
    return session.status === "failed"
      ? "Recover the failed session before treating workspace posture as stable."
      : "Let the active scan finish before rolling posture conclusions up across the workspace.";
  }
  if (hotspotClass === "control-drag") {
    return "Resolve approval or manual-control pressure before reducing governance attention.";
  }
  if (hotspotClass === "risk-drag") {
    return "Reduce critical findings or raise repository score before expanding autonomous trust.";
  }
  return "Close coverage gaps and candidate pressure before treating the workspace as broadly safe.";
}

function priorityWeight(value: TeamPostureHotspot["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
