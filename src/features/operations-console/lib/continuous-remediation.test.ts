import { describe, expect, it } from "vitest";
import { buildContinuousRemediationItems, summarizeContinuousRemediationItems } from "./continuous-remediation";
import { buildOperationsAutonomySignals } from "./operations-autonomy";
import { buildLearningSignals } from "./learning-signals";
import { buildOperationsControlDecisions } from "./operations-controls";

describe("continuous remediation workflow", () => {
  it("holds continuous remediation when policy, recovery, and verification pressure remain active", () => {
    const session = buildBlockedSession();
    const autonomySignals = buildOperationsAutonomySignals(session as never);
    const learningSignals = buildLearningSignals(session.findings as never);
    const controlDecisions = buildOperationsControlDecisions(session as never, autonomySignals, learningSignals);
    const items = buildContinuousRemediationItems(session as never, autonomySignals, controlDecisions);
    const summary = summarizeContinuousRemediationItems(items);

    expect(items.map((item) => item.workflowClass)).toEqual([
      "policy-held",
      "recovery-held",
      "verification-held",
    ]);
    expect(summary.criticalWorkflows).toBe(3);
    expect(summary.heldWorkflows).toBe(2);
    expect(summary.recoveryWorkflows).toBe(1);
    expect(summary.eligibleWorkflows).toBe(0);
  });

  it("opens a low-risk continuous remediation window when policy and recovery gates are clear", () => {
    const session = buildEligibleSession();
    const autonomySignals = buildOperationsAutonomySignals(session as never);
    const learningSignals = buildLearningSignals(session.findings as never);
    const controlDecisions = buildOperationsControlDecisions(session as never, autonomySignals, learningSignals);
    const items = buildContinuousRemediationItems(session as never, autonomySignals, controlDecisions);
    const summary = summarizeContinuousRemediationItems(items);

    expect(items).toHaveLength(1);
    expect(items[0]?.workflowClass).toBe("eligible-window");
    expect(items[0]?.workflowState).toBe("eligible");
    expect(summary.eligibleWorkflows).toBe(1);
    expect(summary.topWorkflowLabel).toMatch(/low-risk continuous window is open/i);
  });
});

function buildBlockedSession() {
  return {
    session: {
      workflowSummary: {
        recoveryExecution: {
          selectedPath: "manual-review",
          executionState: "stalled",
          executionLane: "manual-lane",
          reenteredPlanner: false,
          pathReason: "Recovery is waiting for manual review.",
        },
        workflowClosure: {
          closureReason: "Approval and escalation remain open.",
          autonomousReady: false,
          requiresHumanControl: true,
          nextClosureStep: "collect approval",
        },
      },
    },
    findings: [
      {
        id: "finding-1",
        title: "Dynamic query construction may allow injection",
        remediationStatus: "validation_failed",
        approvalStatus: "escalated",
        remediationNotes: ["Verification left residual risk open."],
        attemptedStrategyIds: ["guard-input", "sanitize-query"],
        approvalHistory: [{ status: "escalated" }],
        appliedStrategyId: null,
      },
    ],
  };
}

function buildEligibleSession() {
  return {
    session: {
      workflowSummary: {
        recoveryExecution: {
          selectedPath: "closed-path",
          executionState: "closed",
          executionLane: "autonomous-lane",
          reenteredPlanner: false,
          pathReason: "Recovery is closed.",
        },
        workflowClosure: {
          closureReason: "Low-risk remediation can proceed under policy control.",
          autonomousReady: true,
          requiresHumanControl: false,
          nextClosureStep: "advance autonomous pass",
        },
      },
    },
    findings: [
      {
        id: "finding-2",
        title: "Escaped command execution path",
        remediationStatus: "verified_fixed",
        approvalStatus: "approved",
        remediationNotes: [],
        attemptedStrategyIds: ["strict-escape"],
        approvalHistory: [{ status: "approved" }],
        appliedStrategyId: "strict-escape",
      },
    ],
  };
}
