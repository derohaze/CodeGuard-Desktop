import { describe, expect, it } from "vitest";
import { buildRecommendationReuseItems, summarizeRecommendationReuseItems } from "./recommendation-reuse";

describe("recommendation reuse", () => {
  it("builds ready, guarded, and suppressed reuse signals from memory and finding history", () => {
    const items = buildRecommendationReuseItems(buildReuseSession() as never);

    expect(items.map((item) => item.reuseClass)).toEqual([
      "suppressed-reuse",
      "guarded-reuse",
      "ready-reuse",
    ]);
  });

  it("summarizes reuse pressure correctly", () => {
    const summary = summarizeRecommendationReuseItems(buildRecommendationReuseItems(buildReuseSession() as never));

    expect(summary.itemCount).toBe(3);
    expect(summary.criticalItems).toBe(1);
    expect(summary.readyReuseItems).toBe(1);
    expect(summary.guardedReuseItems).toBe(1);
    expect(summary.suppressedReuseItems).toBe(1);
  });
});

function buildReuseSession() {
  return {
    session: {
      workflowSummary: {
        memorySummary: {
          attemptedStrategyCount: 5,
          rejectedPathCount: 1,
          escalatedPathCount: 1,
          knownStrategyIds: ["strict-escape", "bounded-query", "legacy-guard"],
          suppressedStrategyCount: 1,
          suppressionState: "active",
          nextMemoryAction: "generate-materially-different-patch",
          recentConstraint: "Legacy guard left residual risk open.",
        },
      },
    },
    findings: [
      {
        id: "finding-1",
        remediationStatus: "verified_fixed",
        appliedStrategyId: "strict-escape",
        attemptedStrategyIds: ["strict-escape"],
      },
      {
        id: "finding-2",
        remediationStatus: "validation_failed",
        appliedStrategyId: null,
        attemptedStrategyIds: ["legacy-guard"],
      },
    ],
  };
}
