import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { Finding } from "@/entities/finding/model/types";

export interface GovernanceLedgerItem {
  ledgerClass: "approval" | "policy" | "escalation" | "risk" | "control";
  priority: "critical" | "high" | "normal";
  label: string;
  evidence: string;
  nextAction: string;
}

export interface GovernanceLedgerSummary {
  itemCount: number;
  criticalItems: number;
  approvalItems: number;
  policyItems: number;
  escalationItems: number;
  riskItems: number;
  controlItems: number;
  topItemLabel: string;
}

export function buildGovernanceLedger(findings: Finding[]): GovernanceLedgerItem[] {
  const decisions = findings.map((finding) => ({
    finding,
    decision: buildFindingDecisionSummary(finding),
  }));

  const approvalCounts = countBy(decisions.map(({ finding }) => finding.approvalStatus));
  const policyCounts = countBy(decisions.map(({ decision }) => decision.policyOutcome));
  const escalationCounts = countBy(decisions.map(({ decision }) => decision.escalationState));
  const highRiskCount = decisions.filter(({ decision }) => decision.riskScore >= 85).length;
  const humanControlCount = decisions.filter(({ decision }) => decision.policySummary.autoPathState !== "eligible").length;

  const items: GovernanceLedgerItem[] = [];

  if ((approvalCounts.pending ?? 0) > 0 || (approvalCounts.escalated ?? 0) > 0) {
    items.push({
      ledgerClass: "approval",
      priority: (approvalCounts.escalated ?? 0) > 0 ? "critical" : "high",
      label: "Approval queue pressure",
      evidence: `${approvalCounts.pending ?? 0} pending and ${approvalCounts.escalated ?? 0} escalated approvals remain open.`,
      nextAction: "Resolve approvals before closing governance gates.",
    });
  }

  if ((policyCounts["blocked-by-policy"] ?? 0) > 0) {
    items.push({
      ledgerClass: "policy",
      priority: "critical",
      label: "Policy blocks active",
      evidence: `${policyCounts["blocked-by-policy"]} finding(s) remain blocked by policy.`,
      nextAction: "Regenerate safer remediation paths before the next governance cycle.",
    });
  }

  if ((escalationCounts.required ?? 0) > 0 || (escalationCounts["already-escalated"] ?? 0) > 0) {
    items.push({
      ledgerClass: "escalation",
      priority: "critical",
      label: "Escalation backlog",
      evidence: `${(escalationCounts.required ?? 0) + (escalationCounts["already-escalated"] ?? 0)} escalated path(s) remain unresolved.`,
      nextAction: "Assign escalation owners and close the approval path before resuming automation.",
    });
  }

  if (highRiskCount > 0) {
    items.push({
      ledgerClass: "risk",
      priority: "high",
      label: "High-risk findings remain",
      evidence: `${highRiskCount} finding(s) are above the risk 85 threshold.`,
      nextAction: "Keep governance review active until the highest-risk findings are resolved.",
    });
  }

  if (humanControlCount > 0) {
    items.push({
      ledgerClass: "control",
      priority: "normal",
      label: "Human control still required",
      evidence: `${humanControlCount} finding(s) remain in a human-controlled posture.`,
      nextAction: "Review control posture before reopening autonomous execution lanes.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeGovernanceLedger(items: GovernanceLedgerItem[]): GovernanceLedgerSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const approvalItems = items.filter((item) => item.ledgerClass === "approval").length;
  const policyItems = items.filter((item) => item.ledgerClass === "policy").length;
  const escalationItems = items.filter((item) => item.ledgerClass === "escalation").length;
  const riskItems = items.filter((item) => item.ledgerClass === "risk").length;
  const controlItems = items.filter((item) => item.ledgerClass === "control").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    approvalItems,
    policyItems,
    escalationItems,
    riskItems,
    controlItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No governance ledger entries",
  };
}

function countBy(values: Array<string | null | undefined>) {
  return values.reduce<Record<string, number>>((acc, value) => {
    const key = value ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}

function priorityWeight(value: GovernanceLedgerItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
