import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import type { Finding } from "@/entities/finding/model/types";

export interface GovernanceQueueItem {
  finding: Finding;
  decision: ReturnType<typeof buildFindingDecisionSummary>;
  blockerClass: "approval-hold" | "policy-gate" | "escalation-hold";
  queuePriority: "critical" | "high" | "normal";
  owner: "approval-controller" | "policy-controller" | "governance-review";
  nextReviewAction: string;
}

export interface GovernanceQueueSummary {
  queuedFindings: number;
  criticalItems: number;
  approvalHolds: number;
  policyGates: number;
  escalationHolds: number;
  highestPriorityLabel: string;
}

export function buildGovernanceQueue(findings: Finding[]): GovernanceQueueItem[] {
  return findings
    .map((finding) => {
      const decision = buildFindingDecisionSummary(finding);
      const blockerClass = buildBlockerClass(finding, decision);

      if (!blockerClass) {
        return null;
      }

      return {
        finding,
        decision,
        blockerClass,
        queuePriority: buildQueuePriority(decision.riskScore, blockerClass),
        owner: buildOwner(blockerClass),
        nextReviewAction: buildNextReviewAction(blockerClass, decision.policySummary.nextControl),
      } satisfies GovernanceQueueItem;
    })
    .filter((item): item is GovernanceQueueItem => item !== null)
    .sort((left, right) => {
      const priorityDelta = priorityScore(right.queuePriority) - priorityScore(left.queuePriority);
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

export function summarizeGovernanceQueue(queue: GovernanceQueueItem[]): GovernanceQueueSummary {
  const criticalItems = queue.filter((item) => item.queuePriority === "critical").length;
  const approvalHolds = queue.filter((item) => item.blockerClass === "approval-hold").length;
  const policyGates = queue.filter((item) => item.blockerClass === "policy-gate").length;
  const escalationHolds = queue.filter((item) => item.blockerClass === "escalation-hold").length;
  const highestPriorityItem = queue[0] ?? null;

  return {
    queuedFindings: queue.length,
    criticalItems,
    approvalHolds,
    policyGates,
    escalationHolds,
    highestPriorityLabel: highestPriorityItem
      ? `${highestPriorityItem.queuePriority} - ${highestPriorityItem.finding.title}`
      : "No governed findings in queue",
  };
}

function buildBlockerClass(
  finding: Finding,
  decision: ReturnType<typeof buildFindingDecisionSummary>,
): GovernanceQueueItem["blockerClass"] | null {
  if (decision.escalationState !== "none" || finding.approvalStatus === "escalated") {
    return "escalation-hold";
  }
  if (decision.policyOutcome === "blocked-by-policy") {
    return "policy-gate";
  }
  if (finding.approvalStatus !== "not_required" || decision.policyOutcome !== "auto-eligible") {
    return "approval-hold";
  }

  return null;
}

function buildQueuePriority(
  riskScore: number,
  blockerClass: GovernanceQueueItem["blockerClass"],
): GovernanceQueueItem["queuePriority"] {
  if (blockerClass === "escalation-hold" || riskScore >= 85) {
    return "critical";
  }
  if (blockerClass === "policy-gate" || riskScore >= 65) {
    return "high";
  }
  return "normal";
}

function buildOwner(blockerClass: GovernanceQueueItem["blockerClass"]): GovernanceQueueItem["owner"] {
  if (blockerClass === "policy-gate") {
    return "policy-controller";
  }
  if (blockerClass === "escalation-hold") {
    return "governance-review";
  }
  return "approval-controller";
}

function buildNextReviewAction(
  blockerClass: GovernanceQueueItem["blockerClass"],
  nextControl: string,
): string {
  if (blockerClass === "policy-gate") {
    return "Regenerate a safer remediation path before the next review cycle.";
  }
  if (blockerClass === "escalation-hold") {
    return "Resolve escalation ownership and decision pressure before progressing the workflow.";
  }
  return `Collect approval and continue with ${nextControl}.`;
}

function priorityScore(value: GovernanceQueueItem["queuePriority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
