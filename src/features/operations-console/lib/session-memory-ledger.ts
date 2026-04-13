import type { ScanSessionDetail } from "@/shared/api/security";

export interface SessionMemoryLedgerItem {
  memoryClass: "attempt-history" | "suppression-state" | "escalation-history" | "strategy-memory" | "constraint-memory";
  priority: "critical" | "high" | "normal";
  label: string;
  reason: string;
  nextAction: string;
}

export interface SessionMemoryLedgerSummary {
  itemCount: number;
  criticalItems: number;
  attemptItems: number;
  suppressionItems: number;
  escalationItems: number;
  strategyItems: number;
  constraintItems: number;
  topItemLabel: string;
}

export function buildSessionMemoryLedger(session: ScanSessionDetail): SessionMemoryLedgerItem[] {
  const memory = session.session.workflowSummary?.memorySummary;
  if (!memory) return [];

  const items: SessionMemoryLedgerItem[] = [];

  if (memory.attemptedStrategyCount > 0 || memory.rejectedPathCount > 0) {
    items.push({
      memoryClass: "attempt-history",
      priority: memory.rejectedPathCount > 0 ? "high" : "normal",
      label: "Attempt history recorded",
      reason: `${memory.attemptedStrategyCount} strategy attempt(s) and ${memory.rejectedPathCount} rejected path(s) are stored in memory.`,
      nextAction: "Use the attempt history to avoid repeating failed strategies on the next remediation cycle.",
    });
  }

  if (memory.suppressionState === "active" || memory.suppressedStrategyCount > 0) {
    items.push({
      memoryClass: "suppression-state",
      priority: memory.suppressionState === "active" ? "critical" : "high",
      label: "Suppression state remains active",
      reason: `${memory.suppressedStrategyCount} suppressed strategy(ies) remain in session memory.`,
      nextAction: "Keep suppressed strategies out of the next automated remediation path.",
    });
  }

  if (memory.escalatedPathCount > 0) {
    items.push({
      memoryClass: "escalation-history",
      priority: "high",
      label: "Escalation history preserved",
      reason: `${memory.escalatedPathCount} escalated path(s) must remain tied to approval-aware routing.`,
      nextAction: "Preserve escalation routing until the approval gate is resolved.",
    });
  }

  if (memory.knownStrategyIds.length > 0) {
    items.push({
      memoryClass: "strategy-memory",
      priority: "normal",
      label: "Reusable strategy memory available",
      reason: `${memory.knownStrategyIds.length} known strategy id(s) can seed low-risk remediation attempts.`,
      nextAction: "Reuse known strategy IDs only when the sink and control boundary match the stored context.",
    });
  }

  if (memory.recentConstraint.trim().length > 0) {
    items.push({
      memoryClass: "constraint-memory",
      priority: memory.nextMemoryAction === "generate-materially-different-patch" ? "high" : "normal",
      label: "Recent constraint recorded",
      reason: memory.recentConstraint,
      nextAction:
        memory.nextMemoryAction === "generate-materially-different-patch"
          ? "Apply the recorded constraint before generating the next strategy set."
          : "Keep the recorded constraint visible during the next remediation step.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeSessionMemoryLedger(items: SessionMemoryLedgerItem[]): SessionMemoryLedgerSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const attemptItems = items.filter((item) => item.memoryClass === "attempt-history").length;
  const suppressionItems = items.filter((item) => item.memoryClass === "suppression-state").length;
  const escalationItems = items.filter((item) => item.memoryClass === "escalation-history").length;
  const strategyItems = items.filter((item) => item.memoryClass === "strategy-memory").length;
  const constraintItems = items.filter((item) => item.memoryClass === "constraint-memory").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    attemptItems,
    suppressionItems,
    escalationItems,
    strategyItems,
    constraintItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No session memory ledger entries",
  };
}

function priorityWeight(value: SessionMemoryLedgerItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
