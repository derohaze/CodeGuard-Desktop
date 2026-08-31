import type { ScanSessionDetail } from "@/shared/api/security";

export interface MemoryCarryForwardItem {
  memoryClass: "reuse-memory" | "suppression-memory" | "escalation-memory" | "constraint-memory";
  priority: "critical" | "high" | "normal";
  label: string;
  reason: string;
  nextAction: string;
}

export interface MemoryCarryForwardSummary {
  itemCount: number;
  criticalItems: number;
  reuseItems: number;
  suppressionItems: number;
  escalationItems: number;
  constraintItems: number;
  topItemLabel: string;
}

export function buildMemoryCarryForwardItems(session: ScanSessionDetail): MemoryCarryForwardItem[] {
  const memory = session.session.workflowSummary?.memorySummary;
  if (!memory) return [];

  const items: MemoryCarryForwardItem[] = [];

  if (memory.knownStrategyIds.length > 0) {
    items.push({
      memoryClass: "reuse-memory",
      priority: "normal",
      label: "Reusable strategy memory is available",
      reason: `${memory.knownStrategyIds.length} known strategy id(s) can seed the next low-risk remediation pass.`,
      nextAction: "Reuse stored strategies only when the next finding matches the same sink and control boundary.",
    });
  }

  if (memory.suppressionState === "active" || memory.suppressedStrategyCount > 0 || memory.rejectedPathCount > 0) {
    items.push({
      memoryClass: "suppression-memory",
      priority: memory.suppressionState === "active" ? "critical" : "high",
      label: "Suppressed strategy memory must carry forward",
      reason: `${memory.suppressedStrategyCount} suppressed strategy(s) and ${memory.rejectedPathCount} rejected path(s) remain in memory.`,
      nextAction:
        memory.nextMemoryAction === "generate-materially-different-patch"
          ? "Generate a materially different patch before any automated retry."
          : "Keep weak strategies suppressed in the next remediation cycle.",
    });
  }

  if (memory.escalatedPathCount > 0) {
    items.push({
      memoryClass: "escalation-memory",
      priority: "high",
      label: "Escalation memory must be preserved",
      reason: `${memory.escalatedPathCount} escalated path(s) should remain attached to future approval-aware routing.`,
      nextAction: "Carry the escalation pattern into the next approval gate instead of reopening a low-risk path automatically.",
    });
  }

  if (memory.recentConstraint.trim().length > 0) {
    items.push({
      memoryClass: "constraint-memory",
      priority: memory.nextMemoryAction === "generate-materially-different-patch" ? "high" : "normal",
      label: "Recent constraint should shape the next pass",
      reason: memory.recentConstraint,
      nextAction:
        memory.nextMemoryAction === "generate-materially-different-patch"
          ? "Respect the recorded constraint before proposing the next strategy set."
          : "Keep the recorded constraint visible for the next controlled remediation step.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeMemoryCarryForwardItems(
  items: MemoryCarryForwardItem[],
): MemoryCarryForwardSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const reuseItems = items.filter((item) => item.memoryClass === "reuse-memory").length;
  const suppressionItems = items.filter((item) => item.memoryClass === "suppression-memory").length;
  const escalationItems = items.filter((item) => item.memoryClass === "escalation-memory").length;
  const constraintItems = items.filter((item) => item.memoryClass === "constraint-memory").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    reuseItems,
    suppressionItems,
    escalationItems,
    constraintItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No learning memory must carry forward",
  };
}

function priorityWeight(value: MemoryCarryForwardItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
