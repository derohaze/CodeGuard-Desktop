import type { Finding } from "@/entities/finding/model/types";
import type { FindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { PreMergeGuidanceItem } from "./pre-merge-guidance";

export interface PreventionLedgerItem {
  ledgerClass: "pre-merge" | "approval-safety" | "verification-guard" | "policy-boundary";
  priority: "critical" | "high" | "normal";
  label: string;
  evidence: string;
  nextAction: string;
}

export interface PreventionLedgerSummary {
  itemCount: number;
  criticalItems: number;
  preMergeItems: number;
  approvalItems: number;
  verificationItems: number;
  policyItems: number;
  topItemLabel: string;
}

export function buildPreventionLedger({
  finding,
  decision,
  preMergeGuidance,
}: {
  finding: Finding;
  decision: FindingDecisionSummary;
  preMergeGuidance: PreMergeGuidanceItem[];
}): PreventionLedgerItem[] {
  const items: PreventionLedgerItem[] = [];

  if (decision.policyOutcome === "blocked-by-policy" || decision.stopState === "stop-and-regenerate") {
    items.push({
      ledgerClass: "policy-boundary",
      priority: "critical",
      label: "Policy boundary blocks prevention",
      evidence: decision.policyReason,
      nextAction: "Regenerate a safer remediation path before any preventive automation is allowed.",
    });
  }

  if (decision.approvalState === "Approval required" || decision.escalationState !== "none") {
    items.push({
      ledgerClass: "approval-safety",
      priority: decision.escalationState === "required" || decision.escalationState === "already-escalated" ? "critical" : "high",
      label: "Approval safety gate active",
      evidence: decision.approvalPath,
      nextAction: "Resolve approval gating before enabling preventive automation.",
    });
  }

  if (finding.remediationStatus === "verified_partial" || finding.remediationStatus === "validation_failed" || decision.residualRiskState.includes("verification")) {
    items.push({
      ledgerClass: "verification-guard",
      priority: finding.remediationStatus === "verified_partial" ? "critical" : "high",
      label: "Verification guard remains open",
      evidence: decision.residualRiskState,
      nextAction: "Re-run verification and confirm closure before rolling prevention forward.",
    });
  }

  if (preMergeGuidance.length > 0) {
    items.push({
      ledgerClass: "pre-merge",
      priority: preMergeGuidance.some((item) => item.priority === "critical") ? "high" : "normal",
      label: "Pre-merge prevention guidance",
      evidence: `${preMergeGuidance.length} guidance item(s) shape the prevention posture for this finding.`,
      nextAction: preMergeGuidance[0]?.mergeCondition ?? "Apply pre-merge guidance before releasing the patch.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizePreventionLedger(items: PreventionLedgerItem[]): PreventionLedgerSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const preMergeItems = items.filter((item) => item.ledgerClass === "pre-merge").length;
  const approvalItems = items.filter((item) => item.ledgerClass === "approval-safety").length;
  const verificationItems = items.filter((item) => item.ledgerClass === "verification-guard").length;
  const policyItems = items.filter((item) => item.ledgerClass === "policy-boundary").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    preMergeItems,
    approvalItems,
    verificationItems,
    policyItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No prevention ledger entries",
  };
}

function priorityWeight(value: PreventionLedgerItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
