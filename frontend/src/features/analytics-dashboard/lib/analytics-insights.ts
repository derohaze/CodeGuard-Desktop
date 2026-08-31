import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { Finding } from "@/entities/finding/model/types";

export interface AnalyticsHotspotItem {
  finding: Finding;
  decision: ReturnType<typeof buildFindingDecisionSummary>;
  pressureClass: "verification-drag" | "approval-drag" | "policy-drag" | "risk-drag";
  pressurePriority: "critical" | "high" | "normal";
  nextAction: string;
}

export interface AnalyticsHotspotSummary {
  hotspotCount: number;
  criticalHotspots: number;
  verificationDrag: number;
  approvalDrag: number;
  policyDrag: number;
  riskDrag: number;
  topHotspotLabel: string;
}

export function buildAnalyticsHotspots(findings: Finding[]): AnalyticsHotspotItem[] {
  return findings
    .map((finding) => {
      const decision = buildFindingDecisionSummary(finding);
      const pressureClass = classifyPressure(finding, decision);
      if (!pressureClass) {
        return null;
      }

      return {
        finding,
        decision,
        pressureClass,
        pressurePriority: classifyPriority(finding, decision, pressureClass),
        nextAction: buildNextAction(finding, decision, pressureClass),
      } satisfies AnalyticsHotspotItem;
    })
    .filter((item): item is AnalyticsHotspotItem => item !== null)
    .sort((left, right) => {
      const priorityDelta = priorityWeight(right.pressurePriority) - priorityWeight(left.pressurePriority);
      if (priorityDelta !== 0) {
        return priorityDelta;
      }

      const riskDelta = right.decision.riskScore - left.decision.riskScore;
      if (riskDelta !== 0) {
        return riskDelta;
      }

      return left.finding.title.localeCompare(right.finding.title);
    });
}

export function summarizeAnalyticsHotspots(items: AnalyticsHotspotItem[]): AnalyticsHotspotSummary {
  const criticalHotspots = items.filter((item) => item.pressurePriority === "critical").length;
  const verificationDrag = items.filter((item) => item.pressureClass === "verification-drag").length;
  const approvalDrag = items.filter((item) => item.pressureClass === "approval-drag").length;
  const policyDrag = items.filter((item) => item.pressureClass === "policy-drag").length;
  const riskDrag = items.filter((item) => item.pressureClass === "risk-drag").length;
  const topHotspot = items[0] ?? null;

  return {
    hotspotCount: items.length,
    criticalHotspots,
    verificationDrag,
    approvalDrag,
    policyDrag,
    riskDrag,
    topHotspotLabel: topHotspot ? `${topHotspot.pressurePriority} - ${topHotspot.finding.title}` : "No active analytics hotspot",
  };
}

function classifyPressure(
  finding: Finding,
  decision: ReturnType<typeof buildFindingDecisionSummary>,
): AnalyticsHotspotItem["pressureClass"] | null {
  if (finding.remediationStatus === "validation_failed" || finding.remediationStatus === "verified_partial") {
    return "verification-drag";
  }
  if (decision.policyOutcome === "blocked-by-policy") {
    return "policy-drag";
  }
  if (finding.approvalStatus === "pending" || finding.approvalStatus === "escalated") {
    return "approval-drag";
  }
  if (decision.riskScore >= 85) {
    return "risk-drag";
  }

  return null;
}

function classifyPriority(
  finding: Finding,
  decision: ReturnType<typeof buildFindingDecisionSummary>,
  pressureClass: AnalyticsHotspotItem["pressureClass"],
): AnalyticsHotspotItem["pressurePriority"] {
  if (pressureClass === "verification-drag" || pressureClass === "policy-drag" || finding.approvalStatus === "escalated" || decision.riskScore >= 85) {
    return "critical";
  }
  if (pressureClass === "approval-drag" || decision.riskScore >= 65) {
    return "high";
  }
  return "normal";
}

function buildNextAction(
  finding: Finding,
  decision: ReturnType<typeof buildFindingDecisionSummary>,
  pressureClass: AnalyticsHotspotItem["pressureClass"],
) {
  if (pressureClass === "verification-drag") {
    return "Re-run verification or generate a materially stronger remediation path.";
  }
  if (pressureClass === "policy-drag") {
    return "Replace the current patch path before policy will allow execution to continue.";
  }
  if (pressureClass === "approval-drag") {
    return `Resolve approval gating and continue with ${decision.policySummary.nextControl}.`;
  }
  return "Reduce risk concentration before treating this run as operationally stable.";
}

function priorityWeight(value: AnalyticsHotspotItem["pressurePriority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
