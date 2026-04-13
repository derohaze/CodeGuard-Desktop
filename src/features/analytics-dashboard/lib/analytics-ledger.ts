import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { Finding } from "@/entities/finding/model/types";

export interface AnalyticsLedgerItem {
  ledgerClass: "throughput" | "approval" | "policy" | "verification" | "risk";
  priority: "critical" | "high" | "normal";
  label: string;
  evidence: string;
  nextAction: string;
}

export interface AnalyticsLedgerSummary {
  itemCount: number;
  criticalItems: number;
  throughputItems: number;
  approvalItems: number;
  policyItems: number;
  verificationItems: number;
  riskItems: number;
  topItemLabel: string;
}

export function buildAnalyticsLedger(findings: Finding[]): AnalyticsLedgerItem[] {
  const decisions = findings.map((finding) => ({
    finding,
    decision: buildFindingDecisionSummary(finding),
  }));

  const remediationCounts = countBy(decisions.map(({ finding }) => finding.remediationStatus));
  const approvalCounts = countBy(decisions.map(({ finding }) => finding.approvalStatus));
  const policyCounts = countBy(decisions.map(({ decision }) => decision.policyOutcome));
  const highRiskCount = decisions.filter(({ decision }) => decision.riskScore >= 85).length;
  const reviewRiskCount = decisions.filter(({ decision }) => decision.riskScore >= 65 && decision.riskScore < 85).length;

  const items: AnalyticsLedgerItem[] = [];

  if ((remediationCounts.verified_fixed ?? 0) === 0 && findings.length > 0) {
    items.push({
      ledgerClass: "throughput",
      priority: "high",
      label: "Verification throughput stalled",
      evidence: "No findings have reached verified-fixed status yet.",
      nextAction: "Confirm the strongest remediation path and re-run verification on the highest-risk finding.",
    });
  } else if ((remediationCounts.verified_fixed ?? 0) > 0) {
    items.push({
      ledgerClass: "throughput",
      priority: "normal",
      label: "Verified fixes recorded",
      evidence: `${remediationCounts.verified_fixed} finding(s) are verified fixed in the current run.`,
      nextAction: "Scale verified remediation patterns to similar findings where safe.",
    });
  }

  if ((approvalCounts.pending ?? 0) > 0 || (approvalCounts.escalated ?? 0) > 0) {
    items.push({
      ledgerClass: "approval",
      priority: (approvalCounts.escalated ?? 0) > 0 ? "critical" : "high",
      label: "Approval pressure remains",
      evidence: `${approvalCounts.pending ?? 0} pending and ${approvalCounts.escalated ?? 0} escalated approval(s) remain open.`,
      nextAction: "Resolve approvals before expanding automation into sensitive paths.",
    });
  }

  if ((policyCounts["blocked-by-policy"] ?? 0) > 0) {
    items.push({
      ledgerClass: "policy",
      priority: "critical",
      label: "Policy blocks remain active",
      evidence: `${policyCounts["blocked-by-policy"]} finding(s) are blocked by policy.`,
      nextAction: "Generate stronger patches or reroute the remediation strategy for blocked findings.",
    });
  }

  if ((remediationCounts.verified_partial ?? 0) > 0 || (remediationCounts.validation_failed ?? 0) > 0) {
    items.push({
      ledgerClass: "verification",
      priority: "high",
      label: "Verification drag remains",
      evidence: `${remediationCounts.verified_partial ?? 0} partial and ${remediationCounts.validation_failed ?? 0} failed verification(s) recorded.`,
      nextAction: "Retry remediation on partial/failed findings with stronger guardrails.",
    });
  }

  if (highRiskCount > 0 || reviewRiskCount > 0) {
    items.push({
      ledgerClass: "risk",
      priority: highRiskCount > 0 ? "critical" : "high",
      label: "Risk concentration remains high",
      evidence: `${highRiskCount} high-risk and ${reviewRiskCount} review-risk finding(s) remain in the queue.`,
      nextAction: "Reduce risk concentration before treating the run as stable.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeAnalyticsLedger(items: AnalyticsLedgerItem[]): AnalyticsLedgerSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const throughputItems = items.filter((item) => item.ledgerClass === "throughput").length;
  const approvalItems = items.filter((item) => item.ledgerClass === "approval").length;
  const policyItems = items.filter((item) => item.ledgerClass === "policy").length;
  const verificationItems = items.filter((item) => item.ledgerClass === "verification").length;
  const riskItems = items.filter((item) => item.ledgerClass === "risk").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    throughputItems,
    approvalItems,
    policyItems,
    verificationItems,
    riskItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No analytics ledger entries",
  };
}

function countBy(values: Array<string | null | undefined>) {
  return values.reduce<Record<string, number>>((acc, value) => {
    const key = value ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}

function priorityWeight(value: AnalyticsLedgerItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
