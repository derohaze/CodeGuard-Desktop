import type { ScanSessionDetail } from "@/shared/api/security";
import type { OperationsAutonomySignal } from "./operations-autonomy";
import type { OperationsControlDecision } from "./operations-controls";

export interface ContinuousRemediationItem {
  workflowClass: "policy-held" | "verification-held" | "recovery-held" | "eligible-window";
  priority: "critical" | "high" | "normal";
  label: string;
  workflowState: "held" | "recover" | "eligible";
  reason: string;
  nextAction: string;
}

export interface ContinuousRemediationSummary {
  workflowCount: number;
  criticalWorkflows: number;
  heldWorkflows: number;
  recoveryWorkflows: number;
  eligibleWorkflows: number;
  topWorkflowLabel: string;
}

export function buildContinuousRemediationItems(
  session: ScanSessionDetail,
  autonomySignals: OperationsAutonomySignal[],
  controlDecisions: OperationsControlDecision[],
): ContinuousRemediationItem[] {
  const workflow = session.session.workflowSummary;
  if (!workflow) return [];

  const items: ContinuousRemediationItem[] = [];
  const findings = session.findings;
  const recovery = workflow.recoveryExecution;
  const requiresHumanControl = Boolean(workflow.workflowClosure?.requiresHumanControl);
  const approvalHeldCount = findings.filter((finding) =>
    ["pending", "escalated", "rejected"].includes(finding.approvalStatus),
  ).length;
  const verificationHeldCount = findings.filter((finding) =>
    ["validation_failed", "verified_partial"].includes(finding.remediationStatus) || finding.remediationNotes.length > 0,
  ).length;
  const autonomousReady = autonomySignals.some((item) => item.signalClass === "autonomous-ready");
  const advanceWindow = controlDecisions.some((item) => item.controlClass === "autonomous-window");
  const activeReviewCandidates = findings.filter((finding) =>
    ["patch_generated", "patch_selected", "approved"].includes(finding.remediationStatus),
  ).length;

  if (requiresHumanControl || approvalHeldCount > 0) {
    items.push({
      workflowClass: "policy-held",
      priority: requiresHumanControl ? "critical" : "high",
      label: "Policy gate blocks continuous remediation",
      workflowState: "held",
      reason: requiresHumanControl
        ? workflow.workflowClosure?.closureReason ?? "Human control is still required before autonomous progression."
        : `${approvalHeldCount} finding(s) still require approval-aware handling before continuous execution.`,
      nextAction: requiresHumanControl
        ? `Resolve ${workflow.workflowClosure?.nextClosureStep ?? "the active approval gate"} before opening any autonomous workflow window.`
        : "Clear the remaining approval path before enabling continuous remediation.",
    });
  }

  if (recovery && recovery.executionState !== "closed") {
    items.push({
      workflowClass: "recovery-held",
      priority: recovery.executionState === "stalled" ? "critical" : "high",
      label: "Recovery lane still owns execution",
      workflowState: "recover",
      reason: recovery.pathReason,
      nextAction: recovery.reenteredPlanner
        ? "Finish planner re-entry before starting another continuous remediation pass."
        : "Resolve the active recovery lane before scheduling additional autonomous remediation.",
    });
  }

  if (verificationHeldCount > 0) {
    items.push({
      workflowClass: "verification-held",
      priority: findings.some((finding) => finding.remediationStatus === "validation_failed") ? "critical" : "high",
      label: "Verification gate still blocks the next pass",
      workflowState: "held",
      reason: `${verificationHeldCount} finding(s) still carry residual validation or verification work.`,
      nextAction: "Close residual verification notes before opening a continuous remediation loop.",
    });
  }

  if (
    items.length === 0 &&
    autonomousReady &&
    advanceWindow &&
    (activeReviewCandidates > 0 || findings.some((finding) => finding.remediationStatus === "verified_fixed"))
  ) {
    items.push({
      workflowClass: "eligible-window",
      priority: "normal",
      label: "Low-risk continuous window is open",
      workflowState: "eligible",
      reason:
        activeReviewCandidates > 0
          ? `${activeReviewCandidates} low-risk finding(s) are ready for the next controlled remediation pass.`
          : "The session already contains a verified-safe remediation path that can seed the next autonomous pass.",
      nextAction: "Run the next low-risk remediation cycle while preserving policy and verification gates.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeContinuousRemediationItems(
  items: ContinuousRemediationItem[],
): ContinuousRemediationSummary {
  const criticalWorkflows = items.filter((item) => item.priority === "critical").length;
  const heldWorkflows = items.filter((item) => item.workflowState === "held").length;
  const recoveryWorkflows = items.filter((item) => item.workflowState === "recover").length;
  const eligibleWorkflows = items.filter((item) => item.workflowState === "eligible").length;
  const topWorkflow = items[0] ?? null;

  return {
    workflowCount: items.length,
    criticalWorkflows,
    heldWorkflows,
    recoveryWorkflows,
    eligibleWorkflows,
    topWorkflowLabel: topWorkflow ? `${topWorkflow.priority} - ${topWorkflow.label}` : "No continuous remediation workflow is active",
  };
}

function priorityWeight(value: ContinuousRemediationItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
