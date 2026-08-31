import type { Finding } from "@/entities/finding/model/types";
import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";

export interface ApprovalQueueItem {
  findingId: string;
  title: string;
  file: string;
  severity: Finding["severity"];
  riskScore: number;
  triageBand: string;
  reason: string;
  statusLabel: string;
  nextActionLabel: string;
}

export function buildApprovalQueue(findings: Finding[]): ApprovalQueueItem[] {
  return findings
    .map((finding) => buildApprovalItem(finding))
    .filter((item): item is ApprovalQueueItem => item !== null)
    .sort((left, right) => {
      if (right.riskScore !== left.riskScore) {
        return right.riskScore - left.riskScore;
      }
      return left.title.localeCompare(right.title);
    });
}

function buildApprovalItem(finding: Finding): ApprovalQueueItem | null {
  const summary = buildFindingDecisionSummary(finding);
  const approvalState = String(summary?.approvalState ?? "").toLowerCase();
  const triageBand = summary?.triageBand ?? "Priority 3";
  const riskScore = Number(summary?.riskScore ?? 0);
  const requiresApproval = approvalState.includes("approval required");
  const requiresHumanReview = approvalState.includes("human review");
  const requiresVerificationReview = approvalState.includes("verification review");
  const isEscalated = approvalState.includes("escalated");
  const isApproved = approvalState.includes("approved for workspace apply");
  const isRejected = approvalState.includes("rejected");

  if (finding.remediationStatus === "patch_generated" && isApproved) {
    return null;
  }

  if (finding.remediationStatus === "patch_generated") {
    return {
      findingId: finding.id,
      title: finding.title,
      file: finding.file,
      severity: finding.severity,
      riskScore,
      triageBand,
      reason: isRejected
        ? "This remediation path was rejected during approval review and now needs another patch or a renewed review."
        : isEscalated
        ? "This remediation path was escalated for additional review before any workspace apply can proceed."
        : requiresApproval
        ? "Patch review is pending and the current decision state requires explicit approval before workspace apply."
        : requiresHumanReview
          ? "A review-ready remediation plan is waiting for human review before broader rollout."
          : "A review-ready remediation plan is waiting for approval before workspace apply.",
      statusLabel: isRejected ? "Approval rejected" : isEscalated ? "Escalated review" : requiresApproval ? "Approval required" : "Ready for approval",
      nextActionLabel: "Resume patch review",
    };
  }

  if (finding.remediationStatus === "verified_partial") {
    return {
      findingId: finding.id,
      title: finding.title,
      file: finding.file,
      severity: finding.severity,
      riskScore,
      triageBand,
      reason: "A patch was applied, but the decision state still requires verification review before closure.",
      statusLabel: "Verification review",
      nextActionLabel: "Open verification",
    };
  }

  if (finding.remediationStatus === "validation_failed") {
    return {
      findingId: finding.id,
      title: finding.title,
      file: finding.file,
      severity: finding.severity,
      riskScore,
      triageBand,
      reason: "The last remediation apply attempt was blocked safely and now sits in a blocked remediation decision state.",
      statusLabel: "Blocked patch",
      nextActionLabel: "Resume patch review",
    };
  }

  if ((isRejected || isEscalated || requiresApproval || requiresHumanReview || requiresVerificationReview) && finding.remediationStatus === "open") {
    return {
      findingId: finding.id,
      title: finding.title,
      file: finding.file,
      severity: finding.severity,
      riskScore,
      triageBand,
      reason: isRejected
        ? "The last approval review rejected this remediation path, so the finding stays queued until a different patch or a renewed review is chosen."
        : isEscalated
        ? "The current decision state escalated this finding for additional review before remediation can proceed."
        : requiresApproval
        ? "The current decision state requires approval before this finding can move through remediation."
        : "The current decision state requires human review before remediation can be closed.",
      statusLabel: isRejected ? "Approval rejected" : isEscalated ? "Escalated review" : requiresApproval ? "Approval required" : "Human review",
      nextActionLabel: "Open finding",
    };
  }

  return null;
}
