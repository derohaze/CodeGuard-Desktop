import type { Finding } from "@/entities/finding/model/types";
import type { ScanSessionDetail } from "@/shared/api/security";

export interface ContinuousExecutionCandidate {
  finding: Finding;
  priority: "critical" | "high" | "normal";
  label: string;
  reason: string;
  nextAction: string;
  excludedStrategyIds: string[];
  attemptedStrategyIds: string[];
}

export function buildContinuousExecutionCandidates(session: ScanSessionDetail): ContinuousExecutionCandidate[] {
  const workflow = session.session.workflowSummary;
  const retryAvailable = Boolean(workflow?.recoverySummary?.retryAvailable);
  const requiresHumanControl = Boolean(workflow?.workflowClosure?.requiresHumanControl);

  if (!retryAvailable || requiresHumanControl) {
    return [];
  }

  return session.findings
    .filter((finding) => {
      const approvalSafe = ["approved", "not_required"].includes(finding.approvalStatus);
      const remediationRetryable = ["validation_failed", "verified_partial"].includes(finding.remediationStatus);
      const hasAttemptHistory = finding.attemptedStrategyIds.length > 0;
      const notBlocked = finding.decisionSummary?.applyReadiness !== "blocked-before-apply";

      return approvalSafe && remediationRetryable && hasAttemptHistory && notBlocked;
    })
    .map((finding) => ({
      finding,
      priority: finding.remediationStatus === "validation_failed" ? "critical" : "high",
      label: `Guarded retry for ${finding.title}`,
      reason:
        finding.remediationNotes[0]
        ?? `Previous remediation for ${finding.title} still needs a materially different retry path.`,
      nextAction: "Generate a materially different patch while preserving policy and verification gates.",
      excludedStrategyIds: finding.attemptedStrategyIds,
      attemptedStrategyIds: finding.attemptedStrategyIds,
    }))
    .sort((left, right) => {
      const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
      if (priorityDelta !== 0) return priorityDelta;
      return left.finding.title.localeCompare(right.finding.title);
    });
}

function priorityWeight(value: ContinuousExecutionCandidate["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
