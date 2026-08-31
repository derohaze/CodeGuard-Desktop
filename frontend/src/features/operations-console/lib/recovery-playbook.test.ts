import { describe, expect, it } from "vitest";
import { buildRecoveryPlaybookItems, summarizeRecoveryPlaybookItems } from "./recovery-playbook";

describe("recovery playbook", () => {
  it("builds retry and manual recovery playbook items", () => {
    const session = buildRetrySession();
    const items = buildRecoveryPlaybookItems(session as never);
    const summary = summarizeRecoveryPlaybookItems(items);

    expect(items.map((item) => item.recoveryClass)).toContain("retry-ready");
    expect(items.map((item) => item.recoveryClass)).toContain("manual-review");
    expect(summary.criticalItems).toBe(1);
    expect(summary.retryItems).toBe(1);
    expect(summary.topItemLabel.toLowerCase()).toContain("manual recovery");
  });

  it("returns empty when no recovery summary is present", () => {
    const items = buildRecoveryPlaybookItems({ session: {}, findings: [] } as never);
    expect(items).toHaveLength(0);
  });
});

function buildRetrySession() {
  return {
    session: {
      workflowSummary: {
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
        recoveryExecution: {
          selectedPath: "retry-path",
          executionState: "held",
          executionLane: "retry-lane",
          reenteredPlanner: false,
          pathReason: "Manual review still required before retry.",
        },
      },
    },
    findings: [],
  };
}
