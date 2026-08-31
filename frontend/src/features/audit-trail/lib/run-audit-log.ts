import type { ScanSessionDetail } from "@/shared/api/security";

export interface RunAuditLogEvent {
  id: string;
  eventClass: "workflow" | "closure" | "recovery" | "operations" | "memory";
  priority: "critical" | "high" | "normal";
  label: string;
  detail: string;
  context: string;
}

export interface RunAuditLogSummary {
  eventCount: number;
  criticalEvents: number;
  closureEvents: number;
  recoveryEvents: number;
  operationsEvents: number;
  topEventLabel: string;
}

export function buildRunAuditLog(session: ScanSessionDetail): RunAuditLogEvent[] {
  const workflow = session.session.workflowSummary;
  if (!workflow) return [];

  const events: RunAuditLogEvent[] = [];
  const closure = workflow.workflowClosure;
  const recoverySummary = workflow.recoverySummary;
  const operationsExecution = workflow.operationsExecution;
  const memorySummary = workflow.memorySummary;

  events.push({
    id: "workflow-state",
    eventClass: "workflow",
    priority: workflow.state === "failed" ? "critical" : workflow.state === "approval-control" ? "high" : "normal",
    label: `Workflow ${workflow.label}`,
    detail: workflow.summary,
    context: `Owner ${workflow.activeController} - next ${workflow.nextAction}`,
  });

  if (closure) {
    events.push({
      id: "workflow-closure",
      eventClass: "closure",
      priority: closure.requiresHumanControl ? "critical" : closure.autonomousReady ? "normal" : "high",
      label: `Closure ${closure.closureLabel}`,
      detail: closure.closureReason,
      context: `Next ${closure.nextClosureStep}`,
    });
  }

  if (recoverySummary) {
    const recoveryPriority = recoverySummary.recoveryState === "terminal-failure" || recoverySummary.controllerStatus === "manual-review-required"
      ? "critical"
      : recoverySummary.recoveryState === "retry-ready" || recoverySummary.recoveryState === "planner-reentry"
        ? "high"
        : "normal";
    events.push({
      id: "recovery-summary",
      eventClass: "recovery",
      priority: recoveryPriority,
      label: `Recovery ${recoverySummary.recoveryState}`,
      detail: recoverySummary.latestFailureReason || "Recovery controller remains active for this run.",
      context: `${recoverySummary.retryableFindings} retryable finding(s) - ${recoverySummary.controllerStatus}`,
    });
  }

  if (operationsExecution) {
    events.push({
      id: "operations-execution",
      eventClass: "operations",
      priority: operationsExecution.handoffStatus === "blocked" ? "critical" : operationsExecution.handoffStatus === "pending" ? "high" : "normal",
      label: `Operations ${operationsExecution.currentHandoff}`,
      detail: operationsExecution.pendingExecutionStep,
      context: `${operationsExecution.handoffStatus} - owner ${operationsExecution.owningController}`,
    });
  }

  if (memorySummary) {
    events.push({
      id: "memory-summary",
      eventClass: "memory",
      priority: memorySummary.suppressionState === "active" ? "high" : "normal",
      label: `Memory ${memorySummary.suppressionState}`,
      detail: memorySummary.recentConstraint,
      context: `${memorySummary.suppressedStrategyCount} suppressed - ${memorySummary.escalatedPathCount} escalated`,
    });
  }

  return events.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeRunAuditLog(events: RunAuditLogEvent[]): RunAuditLogSummary {
  const criticalEvents = events.filter((event) => event.priority === "critical").length;
  const closureEvents = events.filter((event) => event.eventClass === "closure").length;
  const recoveryEvents = events.filter((event) => event.eventClass === "recovery").length;
  const operationsEvents = events.filter((event) => event.eventClass === "operations").length;
  const topEvent = events[0] ?? null;

  return {
    eventCount: events.length,
    criticalEvents,
    closureEvents,
    recoveryEvents,
    operationsEvents,
    topEventLabel: topEvent ? `${topEvent.priority} - ${topEvent.label}` : "No run audit log available",
  };
}

function priorityWeight(value: RunAuditLogEvent["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
