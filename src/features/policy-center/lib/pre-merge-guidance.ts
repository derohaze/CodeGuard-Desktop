import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { Finding } from "@/entities/finding/model/types";

export interface PreMergeGuidanceItem {
  guidanceClass: "merge-blocker" | "review-gate" | "verification-gate" | "hardening-followup";
  priority: "critical" | "high" | "normal";
  label: string;
  guidance: string;
  mergeCondition: string;
}

export interface PreMergeGuidanceSummary {
  guidanceCount: number;
  criticalGuidance: number;
  mergeBlockers: number;
  reviewGates: number;
  verificationGates: number;
  hardeningFollowups: number;
  topGuidanceLabel: string;
}

export function buildPreMergeGuidance(finding: Finding): PreMergeGuidanceItem[] {
  const decision = buildFindingDecisionSummary(finding);
  const items: PreMergeGuidanceItem[] = [];

  if (decision.policyOutcome === "blocked-by-policy" || decision.stopState === "stop-and-regenerate") {
    items.push({
      guidanceClass: "merge-blocker",
      priority: "critical",
      label: "Patch path is blocked before merge",
      guidance: "Do not merge the current path. The remediation still violates policy or failed a safety boundary.",
      mergeCondition: "Generate a materially stronger patch and re-run verification before any merge path is reopened.",
    });
  }

  if (decision.approvalPath.includes("Human approval") || decision.approvalState === "Approval required") {
    items.push({
      guidanceClass: "review-gate",
      priority: decision.escalationState === "required" || decision.escalationState === "already-escalated" ? "critical" : "high",
      label: "Merge requires review control",
      guidance: "This finding still sits on a human-controlled path because of approval, identity pressure, or escalation.",
      mergeCondition: "Resolve the approval path and capture the reviewer decision before merging.",
    });
  }

  if (decision.residualRiskState.includes("verification") || decision.applyReadiness === "approval-required-before-apply") {
    items.push({
      guidanceClass: "verification-gate",
      priority: finding.remediationStatus === "verified_partial" ? "critical" : "high",
      label: "Verification gate remains open",
      guidance: "The current remediation state is not strong enough to treat the finding as merge-safe yet.",
      mergeCondition: "Re-run verification and confirm the vulnerable path is fully closed before merge.",
    });
  }

  if (decision.policyOutcome !== "blocked-by-policy" && decision.stopState !== "stop-and-regenerate") {
    items.push({
      guidanceClass: "hardening-followup",
      priority: "normal",
      label: "Preserve the fix at merge time",
      guidance: "Keep the final diff aligned with the traced sink and avoid weakening the boundary while resolving review comments.",
      mergeCondition: "Retain sink-level remediation and avoid fallback workarounds during code review cleanup.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizePreMergeGuidance(items: PreMergeGuidanceItem[]): PreMergeGuidanceSummary {
  const criticalGuidance = items.filter((item) => item.priority === "critical").length;
  const mergeBlockers = items.filter((item) => item.guidanceClass === "merge-blocker").length;
  const reviewGates = items.filter((item) => item.guidanceClass === "review-gate").length;
  const verificationGates = items.filter((item) => item.guidanceClass === "verification-gate").length;
  const hardeningFollowups = items.filter((item) => item.guidanceClass === "hardening-followup").length;
  const topGuidance = items[0] ?? null;

  return {
    guidanceCount: items.length,
    criticalGuidance,
    mergeBlockers,
    reviewGates,
    verificationGates,
    hardeningFollowups,
    topGuidanceLabel: topGuidance ? `${topGuidance.priority} - ${topGuidance.label}` : "No active pre-merge guidance",
  };
}

function priorityWeight(value: PreMergeGuidanceItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
