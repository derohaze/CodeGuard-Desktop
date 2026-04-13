import { describe, expect, it } from "vitest";
import { buildMemoryCarryForwardItems, summarizeMemoryCarryForwardItems } from "./memory-carry-forward";

describe("memory carry-forward", () => {
  it("builds carry-forward memory items from an active memory summary", () => {
    const items = buildMemoryCarryForwardItems(buildMemoryHeavySession() as never);

    expect(items.map((item) => item.memoryClass)).toEqual([
      "suppression-memory",
      "escalation-memory",
      "constraint-memory",
      "reuse-memory",
    ]);
  });

  it("summarizes carry-forward pressure correctly", () => {
    const summary = summarizeMemoryCarryForwardItems(
      buildMemoryCarryForwardItems(buildMemoryHeavySession() as never),
    );

    expect(summary.itemCount).toBe(4);
    expect(summary.criticalItems).toBe(1);
    expect(summary.reuseItems).toBe(1);
    expect(summary.suppressionItems).toBe(1);
    expect(summary.escalationItems).toBe(1);
    expect(summary.constraintItems).toBe(1);
  });
});

function buildMemoryHeavySession() {
  return {
    session: {
      workflowSummary: {
        memorySummary: {
          attemptedStrategyCount: 4,
          rejectedPathCount: 2,
          escalatedPathCount: 1,
          knownStrategyIds: ["strict-escape", "bounded-query"],
          suppressedStrategyCount: 2,
          suppressionState: "active",
          nextMemoryAction: "generate-materially-different-patch",
          recentConstraint: "Previous query guard left residual risk open around the auth boundary.",
        },
      },
    },
  };
}
