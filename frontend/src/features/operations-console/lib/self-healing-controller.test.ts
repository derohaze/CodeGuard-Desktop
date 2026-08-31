import { describe, expect, it } from "vitest";
import { buildSelfHealingControllerSignals, summarizeSelfHealingControllerSignals } from "./self-healing-controller";

describe("self-healing controller", () => {
  it("classifies policy, approval, verification, recovery, and ready signals", () => {
    const signals = buildSelfHealingControllerSignals(buildSession() as never);
    const summary = summarizeSelfHealingControllerSignals(signals);

    expect(summary.policyBlockSignals).toBe(1);
    expect(summary.approvalHoldSignals).toBe(1);
    expect(summary.verificationHoldSignals).toBe(1);
    expect(summary.recoveryHoldSignals).toBe(1);
    expect(summary.autoHealSignals).toBe(0);
    expect(summary.criticalSignals).toBeGreaterThan(0);
  });
});

function buildSession() {
  return {
    session: {
      workflowSummary: {
        blockingItems: 2,
        workflowClosure: {
          autonomousReady: false,
        },
        recoverySummary: {
          retryAvailable: false,
          retryableFindings: 0,
          attemptedStrategies: 3,
          latestFailureReason: "Recovery requires manual review.",
          lastVerificationStatus: "manual_review_required",
          recoveryState: "manual-fallback",
          nextTransition: "review-failure",
          controllerStatus: "manual-review-required",
          plannerReentryReady: false,
        },
      },
    },
    findings: [
      {
        approvalStatus: "pending",
        remediationStatus: "validation_failed",
        decisionSummary: { policyOutcome: "blocked-by-policy" },
      },
    ],
  };
}
