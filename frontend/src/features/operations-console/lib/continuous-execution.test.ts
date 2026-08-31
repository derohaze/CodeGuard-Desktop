import { describe, expect, it } from "vitest";
import { buildContinuousExecutionCandidates } from "./continuous-execution";

describe("continuous execution", () => {
  it("builds guarded retry candidates only for approval-safe retryable findings", () => {
    const candidates = buildContinuousExecutionCandidates(buildSession() as never);

    expect(candidates).toHaveLength(1);
    expect(candidates[0]?.finding.id).toBe("finding-1");
    expect(candidates[0]?.excludedStrategyIds).toEqual(["legacy-guard", "sanitize-query"]);
  });
});

function buildSession() {
  return {
    session: {
      workflowSummary: {
        recoverySummary: {
          retryAvailable: true,
        },
        workflowClosure: {
          requiresHumanControl: false,
        },
      },
    },
    findings: [
      {
        id: "finding-1",
        title: "Dynamic query construction may allow injection",
        remediationStatus: "validation_failed",
        approvalStatus: "approved",
        attemptedStrategyIds: ["legacy-guard", "sanitize-query"],
        remediationNotes: ["Previous remediation left residual sink risk open."],
        decisionSummary: {
          applyReadiness: "approval-required-before-apply",
        },
      },
      {
        id: "finding-2",
        title: "Rejected path",
        remediationStatus: "validation_failed",
        approvalStatus: "escalated",
        attemptedStrategyIds: ["guard-input"],
        remediationNotes: [],
        decisionSummary: {
          applyReadiness: "approval-required-before-apply",
        },
      },
    ],
  };
}
