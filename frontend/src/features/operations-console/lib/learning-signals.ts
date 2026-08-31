import type { Finding } from "@/entities/finding/model/types";

export interface LearningSignal {
  finding: Finding;
  signalClass: "reuse-signal" | "suppression-signal" | "approval-pattern" | "verification-pattern";
  priority: "critical" | "high" | "normal";
  label: string;
  note: string;
  nextAction: string;
}

export interface LearningSignalSummary {
  signalCount: number;
  criticalSignals: number;
  reuseSignals: number;
  suppressionSignals: number;
  approvalPatterns: number;
  verificationPatterns: number;
  topSignalLabel: string;
}

export function buildLearningSignals(findings: Finding[]): LearningSignal[] {
  return findings
    .map((finding) => {
      const signalClass = classifySignal(finding);
      if (!signalClass) {
        return null;
      }

      return {
        finding,
        signalClass,
        priority: classifyPriority(finding, signalClass),
        label: buildLabel(finding, signalClass),
        note: buildNote(finding, signalClass),
        nextAction: buildNextAction(finding, signalClass),
      } satisfies LearningSignal;
    })
    .filter((item): item is LearningSignal => item !== null)
    .sort((left, right) => {
      const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
      if (priorityDelta !== 0) return priorityDelta;
      return left.finding.title.localeCompare(right.finding.title);
    });
}

export function summarizeLearningSignals(signals: LearningSignal[]): LearningSignalSummary {
  const criticalSignals = signals.filter((item) => item.priority === "critical").length;
  const reuseSignals = signals.filter((item) => item.signalClass === "reuse-signal").length;
  const suppressionSignals = signals.filter((item) => item.signalClass === "suppression-signal").length;
  const approvalPatterns = signals.filter((item) => item.signalClass === "approval-pattern").length;
  const verificationPatterns = signals.filter((item) => item.signalClass === "verification-pattern").length;
  const topSignal = signals[0] ?? null;

  return {
    signalCount: signals.length,
    criticalSignals,
    reuseSignals,
    suppressionSignals,
    approvalPatterns,
    verificationPatterns,
    topSignalLabel: topSignal ? `${topSignal.priority} - ${topSignal.label}` : "No active learning signal",
  };
}

function classifySignal(finding: Finding): LearningSignal["signalClass"] | null {
  if (finding.remediationStatus === "verified_fixed" && finding.appliedStrategyId) {
    return "reuse-signal";
  }
  if (["validation_failed", "rejected", "rolled_back"].includes(finding.remediationStatus) || finding.attemptedStrategyIds.length > 1) {
    return "suppression-signal";
  }
  if (finding.approvalStatus === "escalated" || finding.approvalStatus === "rejected") {
    return "approval-pattern";
  }
  if (finding.remediationStatus === "verified_partial" || finding.remediationNotes.length > 0) {
    return "verification-pattern";
  }
  return null;
}

function classifyPriority(
  finding: Finding,
  signalClass: LearningSignal["signalClass"],
): LearningSignal["priority"] {
  if (
    signalClass === "suppression-signal" ||
    signalClass === "approval-pattern" ||
    finding.remediationStatus === "verified_partial"
  ) {
    return "critical";
  }
  if (signalClass === "verification-pattern" || finding.attemptedStrategyIds.length > 0) {
    return "high";
  }
  return "normal";
}

function buildLabel(finding: Finding, signalClass: LearningSignal["signalClass"]) {
  if (signalClass === "reuse-signal") return "Reusable remediation path";
  if (signalClass === "suppression-signal") return "Suppress weak strategy path";
  if (signalClass === "approval-pattern") return "Approval escalation pattern";
  return "Verification follow-up pattern";
}

function buildNote(finding: Finding, signalClass: LearningSignal["signalClass"]) {
  if (signalClass === "reuse-signal") {
    return `Strategy ${finding.appliedStrategyId} produced a verified fix for this finding.`;
  }
  if (signalClass === "suppression-signal") {
    return `${finding.attemptedStrategyIds.length || 1} weak or failed strategy path(s) were recorded for this finding.`;
  }
  if (signalClass === "approval-pattern") {
    return `Approval status is ${finding.approvalStatus} with ${finding.approvalHistory.length} approval event(s).`;
  }
  return finding.remediationNotes[0] ?? "Verification remains incomplete for this finding.";
}

function buildNextAction(finding: Finding, signalClass: LearningSignal["signalClass"]) {
  if (signalClass === "reuse-signal") {
    return "Reuse this strategy pattern only when future findings match the same sink and control boundary.";
  }
  if (signalClass === "suppression-signal") {
    return "Suppress or deprioritize previously weak strategy paths before generating the next remediation.";
  }
  if (signalClass === "approval-pattern") {
    return "Capture the escalation pattern so future high-risk findings enter the correct approval path earlier.";
  }
  return "Feed the verification notes back into the next remediation or verification attempt before closure.";
}

function priorityWeight(value: LearningSignal["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
