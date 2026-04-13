import type { ScanSessionDetail } from "@/shared/api/security";

export interface RecoveryPlaybookItem {
  recoveryClass: "retry-ready" | "planner-reentry" | "manual-review" | "terminal-failure";
  priority: "critical" | "high" | "normal";
  label: string;
  reason: string;
  nextAction: string;
  laneSummary: string;
  controllerStatus: string;
}

export interface RecoveryPlaybookSummary {
  itemCount: number;
  criticalItems: number;
  retryItems: number;
  plannerItems: number;
  manualItems: number;
  terminalItems: number;
  topItemLabel: string;
}

export function buildRecoveryPlaybookItems(session: ScanSessionDetail): RecoveryPlaybookItem[] {
  const workflow = session.session.workflowSummary;
  const recoverySummary = workflow?.recoverySummary;
  if (!workflow || !recoverySummary) return [];

  const recoveryExecution = workflow.recoveryExecution;
  const laneSummary = recoveryExecution
    ? `${recoveryExecution.executionLane} - ${recoveryExecution.executionState}`
    : "none";
  const controllerStatus = recoverySummary.controllerStatus;
  const items: RecoveryPlaybookItem[] = [];

  if (recoverySummary.recoveryState === "terminal-failure") {
    items.push({
      recoveryClass: "terminal-failure",
      priority: "critical",
      label: "Terminal recovery failure",
      reason: recoverySummary.latestFailureReason || "Recovery controller reported a terminal failure.",
      nextAction: "Escalate to manual remediation and capture the failure in the audit trail.",
      laneSummary,
      controllerStatus,
    });
  }

  if (recoverySummary.recoveryState === "manual-fallback" || controllerStatus === "manual-review-required") {
    items.push({
      recoveryClass: "manual-review",
      priority: "critical",
      label: "Manual recovery required",
      reason: recoverySummary.latestFailureReason || "Recovery requires manual review before automation can resume.",
      nextAction: "Hold automation and request a manual remediation decision.",
      laneSummary,
      controllerStatus,
    });
  }

  if (recoverySummary.plannerReentryReady || recoverySummary.recoveryState === "planner-reentry") {
    items.push({
      recoveryClass: "planner-reentry",
      priority: "high",
      label: "Planner re-entry ready",
      reason: "Recovery has requested a planner re-entry with updated constraints.",
      nextAction: "Re-enter planning with the blocked strategies and verification notes applied.",
      laneSummary,
      controllerStatus,
    });
  }

  if (recoverySummary.retryAvailable) {
    items.push({
      recoveryClass: "retry-ready",
      priority: recoverySummary.recoveryState === "retry-ready" ? "high" : "normal",
      label: "Guarded retry available",
      reason: recoverySummary.latestFailureReason || "A retryable remediation path is available.",
      nextAction:
        recoverySummary.nextTransition === "retry-remediation"
          ? "Generate a materially different patch and re-run verification."
          : "Review the recovery plan before triggering another retry.",
      laneSummary,
      controllerStatus,
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeRecoveryPlaybookItems(items: RecoveryPlaybookItem[]): RecoveryPlaybookSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const retryItems = items.filter((item) => item.recoveryClass === "retry-ready").length;
  const plannerItems = items.filter((item) => item.recoveryClass === "planner-reentry").length;
  const manualItems = items.filter((item) => item.recoveryClass === "manual-review").length;
  const terminalItems = items.filter((item) => item.recoveryClass === "terminal-failure").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    retryItems,
    plannerItems,
    manualItems,
    terminalItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No active recovery playbook",
  };
}

function priorityWeight(value: RecoveryPlaybookItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
