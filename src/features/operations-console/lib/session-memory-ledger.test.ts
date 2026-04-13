import { describe, expect, it } from "vitest";
import { buildSessionMemoryLedger, summarizeSessionMemoryLedger } from "./session-memory-ledger";

describe("session memory ledger", () => {
  it("summarizes suppression and escalation memory", () => {
    const session = buildSession();
    const items = buildSessionMemoryLedger(session as never);
    const summary = summarizeSessionMemoryLedger(items);

    expect(summary.itemCount).toBeGreaterThan(0);
    expect(summary.suppressionItems).toBe(1);
    expect(summary.escalationItems).toBe(1);
    expect(summary.criticalItems).toBe(1);
  });
});

function buildSession() {
  return {
    session: {
      workflowSummary: {
        memorySummary: {
          attemptedStrategyCount: 4,
          rejectedPathCount: 2,
          escalatedPathCount: 1,
          knownStrategyIds: ["strict-escape", "legacy-guard"],
          suppressedStrategyCount: 2,
          suppressionState: "active",
          nextMemoryAction: "generate-materially-different-patch",
          recentConstraint: "Previous query guard left residual risk open around the auth boundary.",
        },
      },
    },
    findings: [],
  };
}
