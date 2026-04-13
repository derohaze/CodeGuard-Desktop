import type { ScanSessionDetail } from "@/shared/api/security";

export interface SelfHealingControllerSignal {
  signalClass: "auto-heal-ready" | "approval-hold" | "verification-hold" | "recovery-hold" | "policy-block";
  priority: "critical" | "high" | "normal";
  label: string;
  note: string;
  nextAction: string;
}

export interface SelfHealingControllerSummary {
  signalCount: number;
  criticalSignals: number;
  approvalHoldSignals: number;
  verificationHoldSignals: number;
  recoveryHoldSignals: number;
  policyBlockSignals: number;
  autoHealSignals: number;
  topSignalLabel: string;
}

export function buildSelfHealingControllerSignals(session: ScanSessionDetail): SelfHealingControllerSignal[] {
  const workflow = session.session.workflowSummary;
  if (!workflow) return [];

  const approvalHoldCount = session.findings.filter((finding) =>
    ["pending", "escalated", "rejected"].includes(finding.approvalStatus),
  ).length;
  const verificationHoldCount = session.findings.filter((finding) =>
    ["applied", "validation_failed", "verified_partial", "rolled_back"].includes(finding.remediationStatus),
  ).length;
  const policyBlockCount = session.findings.filter(
    (finding) => finding.decisionSummary?.policyOutcome === "blocked-by-policy",
  ).length;

  const recoverySummary = workflow.recoverySummary;
  const recoveryHold =
    Boolean(recoverySummary) &&
    (recoverySummary.recoveryState !== "stable" || recoverySummary.controllerStatus !== "closed");

  const autoHealReady =
    Boolean(workflow.workflowClosure?.autonomousReady) &&
    workflow.blockingItems === 0 &&
    approvalHoldCount === 0 &&
    verificationHoldCount === 0 &&
    policyBlockCount === 0 &&
    !recoveryHold;

  const signals: SelfHealingControllerSignal[] = [];

  if (policyBlockCount > 0) {
    signals.push({
      signalClass: "policy-block",
      priority: "critical",
      label: "Policy gate blocks autonomous remediation",
      note: `${policyBlockCount} finding(s) are blocked by policy gates.`,
      nextAction: "Escalate the blocked findings for manual review before enabling self-healing.",
    });
  }

  if (approvalHoldCount > 0) {
    signals.push({
      signalClass: "approval-hold",
      priority: "critical",
      label: "Approval hold remains active",
      note: `${approvalHoldCount} finding(s) still require approval before self-healing can proceed.`,
      nextAction: "Collect approval decisions or switch to a manual remediation lane.",
    });
  }

  if (verificationHoldCount > 0) {
    signals.push({
      signalClass: "verification-hold",
      priority: "high",
      label: "Verification gaps remain",
      note: `${verificationHoldCount} finding(s) still need verification closure.`,
      nextAction: "Run deterministic verification before resuming autonomous remediation.",
    });
  }

  if (recoveryHold && recoverySummary) {
    signals.push({
      signalClass: "recovery-hold",
      priority: recoverySummary.recoveryState === "terminal-failure" || recoverySummary.recoveryState === "manual-fallback" ? "critical" : "high",
      label: "Recovery controller active",
      note: recoverySummary.latestFailureReason || `Recovery state ${recoverySummary.recoveryState} is active.`,
      nextAction:
        recoverySummary.recoveryState === "retry-ready"
          ? "Execute the guarded retry lane before opening self-healing."
          : "Resolve the recovery lane before resuming autonomous remediation.",
    });
  }

  if (autoHealReady) {
    signals.push({
      signalClass: "auto-heal-ready",
      priority: "normal",
      label: "Self-healing window ready",
      note: "No approval, policy, or verification blocks are currently active.",
      nextAction: "Authorize a low-risk self-healing pass with verification gates enabled.",
    });
  }

  return signals.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeSelfHealingControllerSignals(
  signals: SelfHealingControllerSignal[],
): SelfHealingControllerSummary {
  const criticalSignals = signals.filter((item) => item.priority === "critical").length;
  const approvalHoldSignals = signals.filter((item) => item.signalClass === "approval-hold").length;
  const verificationHoldSignals = signals.filter((item) => item.signalClass === "verification-hold").length;
  const recoveryHoldSignals = signals.filter((item) => item.signalClass === "recovery-hold").length;
  const policyBlockSignals = signals.filter((item) => item.signalClass === "policy-block").length;
  const autoHealSignals = signals.filter((item) => item.signalClass === "auto-heal-ready").length;
  const topSignal = signals[0] ?? null;

  return {
    signalCount: signals.length,
    criticalSignals,
    approvalHoldSignals,
    verificationHoldSignals,
    recoveryHoldSignals,
    policyBlockSignals,
    autoHealSignals,
    topSignalLabel: topSignal ? `${topSignal.priority} - ${topSignal.label}` : "No active self-healing signal",
  };
}

function priorityWeight(value: SelfHealingControllerSignal["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
