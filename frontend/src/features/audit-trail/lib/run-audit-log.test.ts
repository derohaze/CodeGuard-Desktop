import { describe, expect, it } from "vitest";
import { buildRunAuditLog, summarizeRunAuditLog } from "./run-audit-log";

describe("run audit log", () => {
  it("builds critical run audit entries for recovery and closure", () => {
    const session = buildSession();
    const events = buildRunAuditLog(session as never);
    const summary = summarizeRunAuditLog(events);

    expect(events.length).toBeGreaterThan(0);
    expect(summary.criticalEvents).toBeGreaterThan(0);
    expect(summary.recoveryEvents).toBeGreaterThan(0);
    expect(summary.closureEvents).toBeGreaterThan(0);
  });
});

function buildSession() {
  return {
    session: {
      workflowSummary: {
        state: "approval-control",
        label: "Approval hold",
        summary: "Approval is still required before local apply.",
        nextAction: "Collect approval",
        activeController: "approval-controller",
        workflowClosure: {
          closureLabel: "Human-controlled",
          closureState: "human-controlled",
          closureReason: "Approval is still required before local apply.",
          autonomousReady: false,
          requiresHumanControl: true,
          nextClosureStep: "collect approval",
        },
        recoverySummary: {
          retryAvailable: true,
          retryableFindings: 1,
          attemptedStrategies: 2,
          latestFailureReason: "Previous retry left residual sink risk open.",
          lastVerificationStatus: "manual_review_required",
          recoveryState: "manual-fallback",
          nextTransition: "retry-remediation",
          controllerStatus: "manual-review-required",
          plannerReentryReady: false,
        },
        operationsExecution: {
          currentHandoff: "decision -> approval",
          handoffStatus: "blocked",
          owningController: "approval-controller",
          pendingExecutionStep: "Collect reviewer input",
          stepCompletionState: "waiting",
        },
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
        blockingItems: 2,
      },
    },
    findings: [],
  };
}
