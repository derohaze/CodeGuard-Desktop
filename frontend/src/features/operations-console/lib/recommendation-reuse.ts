import type { ScanSessionDetail } from "@/shared/api/security";

export interface RecommendationReuseItem {
  reuseClass: "ready-reuse" | "guarded-reuse" | "suppressed-reuse";
  priority: "critical" | "high" | "normal";
  label: string;
  reason: string;
  nextAction: string;
}

export interface RecommendationReuseSummary {
  itemCount: number;
  criticalItems: number;
  readyReuseItems: number;
  guardedReuseItems: number;
  suppressedReuseItems: number;
  topItemLabel: string;
}

export function buildRecommendationReuseItems(session: ScanSessionDetail): RecommendationReuseItem[] {
  const memory = session.session.workflowSummary?.memorySummary;
  if (!memory) return [];

  const items: RecommendationReuseItem[] = [];
  const findings = session.findings;
  const verifiedStrategies = Array.from(
    new Set(findings.filter((finding) => finding.remediationStatus === "verified_fixed" && finding.appliedStrategyId).map((finding) => finding.appliedStrategyId as string)),
  );
  const suppressedStrategies = new Set(
    findings
      .filter((finding) => ["validation_failed", "rejected", "rolled_back"].includes(finding.remediationStatus))
      .flatMap((finding) => finding.attemptedStrategyIds),
  );
  const knownStrategies = memory.knownStrategyIds;
  const reusableKnownStrategies = knownStrategies.filter((strategyId) => !suppressedStrategies.has(strategyId));
  const guardedStrategies = reusableKnownStrategies.filter((strategyId) => !verifiedStrategies.includes(strategyId));

  if (verifiedStrategies.length > 0) {
    items.push({
      reuseClass: "ready-reuse",
      priority: "normal",
      label: "Verified strategy reuse is available",
      reason: `${verifiedStrategies.length} verified strategy path(s) are available for matching low-risk findings.`,
      nextAction: "Reuse only when the next finding matches the same vulnerability shape, sink, and control boundary.",
    });
  }

  if (guardedStrategies.length > 0) {
    items.push({
      reuseClass: "guarded-reuse",
      priority: "high",
      label: "Known strategies still require guarded reuse",
      reason: `${guardedStrategies.length} stored strategy id(s) exist without a verified reuse path in the current session.`,
      nextAction: "Treat these strategies as guarded suggestions until a verified-safe path confirms reuse quality.",
    });
  }

  if (suppressedStrategies.size > 0 || memory.suppressionState === "active") {
    items.push({
      reuseClass: "suppressed-reuse",
      priority: "critical",
      label: "Suppressed strategies must not be reused automatically",
      reason: `${suppressedStrategies.size || memory.suppressedStrategyCount} strategy path(s) are currently suppressed or tied to failed remediation attempts.`,
      nextAction:
        memory.nextMemoryAction === "generate-materially-different-patch"
          ? "Block automatic reuse and generate a materially different patch."
          : "Keep suppressed strategies out of the next recommendation set.",
    });
  }

  return items.sort((left, right) => {
    const priorityDelta = priorityWeight(right.priority) - priorityWeight(left.priority);
    if (priorityDelta !== 0) return priorityDelta;
    return left.label.localeCompare(right.label);
  });
}

export function summarizeRecommendationReuseItems(
  items: RecommendationReuseItem[],
): RecommendationReuseSummary {
  const criticalItems = items.filter((item) => item.priority === "critical").length;
  const readyReuseItems = items.filter((item) => item.reuseClass === "ready-reuse").length;
  const guardedReuseItems = items.filter((item) => item.reuseClass === "guarded-reuse").length;
  const suppressedReuseItems = items.filter((item) => item.reuseClass === "suppressed-reuse").length;
  const topItem = items[0] ?? null;

  return {
    itemCount: items.length,
    criticalItems,
    readyReuseItems,
    guardedReuseItems,
    suppressedReuseItems,
    topItemLabel: topItem ? `${topItem.priority} - ${topItem.label}` : "No recommendation reuse signal is active",
  };
}

function priorityWeight(value: RecommendationReuseItem["priority"]) {
  return {
    critical: 3,
    high: 2,
    normal: 1,
  }[value];
}
