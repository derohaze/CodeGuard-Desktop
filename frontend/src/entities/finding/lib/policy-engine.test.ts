import { describe, expect, it } from "vitest";
import type { Finding } from "@/entities/finding/model/types";
import { buildPolicyOutcome, buildPolicyReason, buildPolicySummary } from "@/entities/finding/lib/policy-engine";

function buildFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "finding-1",
    severity: "high",
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "SQL injection",
    confidence: 84,
    summary: "Dynamic query is built from user input.",
    impact: "Authentication lookups may be bypassed.",
    explanation: "User-controlled input reaches the query sink.",
    evidence: "query = f\"SELECT ...\"",
    attackSimulation: {
      input: "POST /login",
      execution: "router -> service -> query builder",
      result: "Authentication bypass",
    },
    auditLog: [],
    fixSuggestions: [],
    remediationStatus: "open",
    approvalStatus: "not_required",
    approvalHistory: [],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
    ...overrides,
  };
}

describe("policy engine", () => {
  it("blocks remediation when validation failed", () => {
    const finding = buildFinding({ remediationStatus: "validation_failed" });

    expect(
      buildPolicyOutcome({
        finding,
        riskScore: 72,
        touchesIdentity: false,
        safeAutoPath: false,
      }),
    ).toBe("blocked-by-policy");
  });

  it("keeps approved paths gated when the auto path is unsafe", () => {
    const finding = buildFinding({
      approvalStatus: "approved",
      remediationStatus: "patch_generated",
    });

    const summary = buildPolicySummary(finding, false, 88, false);
    expect(summary.posture).toBe("review");
    expect(summary.autoPathState).toBe("gated");
  });

  it("emits review-required reasons for identity paths", () => {
    const finding = buildFinding({ category: "Session misuse" });
    const reason = buildPolicyReason({
      finding,
      riskScore: 78,
      touchesIdentity: true,
      safeAutoPath: false,
    });

    expect(reason.toLowerCase()).toContain("identity");
  });
});
