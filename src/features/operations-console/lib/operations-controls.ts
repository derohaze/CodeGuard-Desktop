import type { ScanSessionDetail } from "@/shared/api/security";
import type { OperationsAutonomySignal } from "./operations-autonomy";
import type { LearningSignal } from "./learning-signals";

export interface OperationsControlDecision {
  controlClass: "human-hold" | "recovery-control" | "learning-control" | "autonomous-window";
  priority: "critical" | "high" | "normal";
  label: string;
  controlMode: "hold" | "recover" | "stabilize" | "advance";
  reason: string;
  nextAction: string;
}

export interface OperationsControlSummary {
  decisionCount: number;
  criticalDecisions: number;
  holdDecisions: number;
  recoverDecisions: number;
  stabilizeDecisions: number;
  advanceDecisions: number;
  topDecisionLabel: string;
}

export function buildOperationsControlDecisions(
  session: ScanSessionDetail,
  autonomySignals: OperationsAutonomySignal[],
  learningSignals: LearningSignal[],
): OperationsControlDecision[] {
  const workflow = session.session.workflowSummary;
  if (!workflow) return [];

  const decisions: OperationsControlDecision[] = [];
  const closure = workflow.workflowClosure;
  const recovery = workflow.recoveryExecution;
  const hasSuppression = learningSignals.some((item) => item.signalClass === "suppression-signal");
  const hasVerificationPattern = learningSignals.some((item) => item.signalClass === "verification-pattern");
  const hasReuseSignal = learningSignals.some((item) => item.signalClass === "reuse-signal");

  if (closure?.requiresHumanControl) {
    decisions.push({
      controlClass: "human-hold",
      priority: "critical",
      label: "Human hold remains primary",
      controlMode: "hold",
      reason: closure.closureReason,
      nextAction: `Keep automation paused until ${closure.nextClosureStep}.`,
    });
  }

  if (recovery && recovery.executionState !== "closed") {
    decisions.push({
      controlClass: "recovery-control",
      priority: recovery.executionState === "stalled" ? "critical" : "high",
      label: "Recovery control required",
      controlMode: "recover",
      reason: recovery.pathReason,
      nextAction: recovery.reenteredPlanner
        ? "Finish planner re-entry before opening an autonomous window."
        : "Resolve the active recovery lane before any broader automation step.",
    });
  }

  if (hasSuppression || hasVerificationPattern) {
    decisions.push({
      controlClass: "learning-control",
      priority: hasSuppression ? "high" : "normal",
      label: "Learning stabilization required",
      controlMode: "stabilize",
      reason: hasSuppression
        ? "Weak strategy paths still need suppression before the next autonomous iteration."
        : "Verification patterns still need to be folded into the next remediation cycle.",
      nextAction: hasSuppression
        ? "Stabilize the strategy set and avoid retrying weak paths automatically."
        : "Feed verification notes into the next remediation attempt before expanding automation.",
    });
  }

  if (!closure?.requiresHumanControl && (!recovery || recovery.executionState === "closed") && hasReuseSignal && autonomySignals.some((item) => item.signalClass === "autonomous-ready")) {
    decisions.push({
      controlClass: "autonomous-window",
      priority: "normal",
      label: "Low-risk autonomous window",
      controlMode: "advance",
      reason: "The workflow is autonomous-ready and the session contains at least one reusable successful remediation pattern.",
      nextAction: "Advance with a low-risk autonomous step while preserving policy and verification gates.",
    });
  }

  return decisions.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeOperationsControlDecisions(
  decisions: OperationsControlDecision[],
): OperationsControlSummary {
  const criticalDecisions = decisions.filter((item) => item.priority === "critical").length;
  const holdDecisions = decisions.filter((item) => item.controlMode === "hold").length;
  const recoverDecisions = decisions.filter((item) => item.controlMode === "recover").length;
  const stabilizeDecisions = decisions.filter((item) => item.controlMode === "stabilize").length;
  const advanceDecisions = decisions.filter((item) => item.controlMode === "advance").length;
  const topDecision = decisions[0] ?? null;

  return {
    decisionCount: decisions.length,
    criticalDecisions,
    holdDecisions,
    recoverDecisions,
    stabilizeDecisions,
    advanceDecisions,
    topDecisionLabel: topDecision ? `${topDecision.priority} - ${topDecision.label}` : "No active control decision",
  };
}

function priorityWeight(value: OperationsControlDecision["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
