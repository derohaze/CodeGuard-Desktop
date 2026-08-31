import type { ScanSessionDetail } from "@/shared/api/security";

export interface OperationsAutonomySignal {
  signalClass: "autonomous-ready" | "human-control" | "handoff-drag" | "recovery-drag";
  priority: "critical" | "high" | "normal";
  label: string;
  note: string;
  nextAction: string;
}

export interface OperationsAutonomySummary {
  signalCount: number;
  criticalSignals: number;
  autonomousReadySignals: number;
  humanControlSignals: number;
  handoffDragSignals: number;
  recoveryDragSignals: number;
  topSignalLabel: string;
}

export function buildOperationsAutonomySignals(session: ScanSessionDetail): OperationsAutonomySignal[] {
  const workflow = session.session.workflowSummary;
  if (!workflow) return [];

  const signals: OperationsAutonomySignal[] = [];
  const closure = workflow.workflowClosure;
  const execution = workflow.operationsExecution;
  const operations = workflow.operationsSummary;
  const recovery = workflow.recoveryExecution;

  if (closure?.autonomousReady) {
    signals.push({
      signalClass: "autonomous-ready",
      priority: "normal",
      label: "Autonomous-ready closure",
      note: closure.closureReason,
      nextAction: `Advance with ${closure.nextClosureStep}.`,
    });
  }

  if (closure?.requiresHumanControl) {
    signals.push({
      signalClass: "human-control",
      priority: "critical",
      label: "Human control required",
      note: closure.closureReason,
      nextAction: `Resolve human-control gating by ${closure.nextClosureStep}.`,
    });
  }

  if (operations?.pendingHandoff || execution?.handoffStatus === "pending" || execution?.handoffStatus === "blocked") {
    signals.push({
      signalClass: "handoff-drag",
      priority: execution?.handoffStatus === "blocked" ? "critical" : "high",
      label: "Workflow handoff pressure",
      note: execution?.pendingExecutionStep ?? operations?.handoffReason ?? "A workflow handoff is still pending.",
      nextAction: "Clear the pending handoff before treating the run as operationally stable.",
    });
  }

  if (recovery && recovery.executionState !== "closed") {
    signals.push({
      signalClass: "recovery-drag",
      priority: recovery.executionState === "stalled" ? "critical" : "high",
      label: "Recovery path remains active",
      note: recovery.pathReason,
      nextAction: recovery.reenteredPlanner
        ? "Finish planner re-entry before closing the autonomous workflow."
        : "Resolve the active recovery lane before treating the run as autonomous-ready.",
    });
  }

  return signals.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeOperationsAutonomySignals(signals: OperationsAutonomySignal[]): OperationsAutonomySummary {
  const criticalSignals = signals.filter((item) => item.priority === "critical").length;
  const autonomousReadySignals = signals.filter((item) => item.signalClass === "autonomous-ready").length;
  const humanControlSignals = signals.filter((item) => item.signalClass === "human-control").length;
  const handoffDragSignals = signals.filter((item) => item.signalClass === "handoff-drag").length;
  const recoveryDragSignals = signals.filter((item) => item.signalClass === "recovery-drag").length;
  const topSignal = signals[0] ?? null;

  return {
    signalCount: signals.length,
    criticalSignals,
    autonomousReadySignals,
    humanControlSignals,
    handoffDragSignals,
    recoveryDragSignals,
    topSignalLabel: topSignal ? `${topSignal.priority} - ${topSignal.label}` : "No active autonomy signal",
  };
}

function priorityWeight(value: OperationsAutonomySignal["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
