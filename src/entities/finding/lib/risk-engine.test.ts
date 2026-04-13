import { describe, expect, it } from "vitest";
import type { Finding } from "@/entities/finding/model/types";
import { calculateFindingRiskScore, calculatePatchRiskScore } from "@/entities/finding/lib/risk-engine";

function buildFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "finding-1",
    severity: "high",
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "SQL injection",
    confidence: 70,
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

describe("calculateFindingRiskScore", () => {
  it("adds identity and remediation pressure to the base severity score", () => {
    const baseline = calculateFindingRiskScore(buildFinding({ severity: "high" }), false);
    const elevated = calculateFindingRiskScore(buildFinding({ severity: "high", remediationStatus: "verified_partial" }), true);

    expect(elevated).toBeGreaterThan(baseline);
    expect(baseline).toBe(78);
  });

  it("clamps scores when the remediation state reduces pressure below zero", () => {
    const score = calculateFindingRiskScore(buildFinding({ severity: "low", confidence: 0, remediationStatus: "verified_fixed" }), false);
    expect(score).toBe(0);
  });
});

describe("calculatePatchRiskScore", () => {
  it("raises scores for non-compliant, manual review, and batch patches", () => {
    const score = calculatePatchRiskScore({
      severity: "medium",
      confidence: 70,
      touchesIdentity: true,
      selectedStrategy: {
        id: "guard",
        label: "Guard",
        kind: "guard",
        confidence: 70,
        impact: "medium",
        effort: "low",
        summary: "summary",
        rationale: "rationale",
        diff: "diff",
        recommended: false,
        fixType: "risky_workaround",
        securityStrength: "low",
        regressionRisk: "high",
        selectionReason: "",
        nonSelectionReason: "",
        residualRisks: [],
        policyCompliant: false,
        policyViolations: [],
      },
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "summary",
        diff: "diff",
        validationNotes: [],
        beforeSnippet: "before",
        afterSnippet: "after",
        fixType: "risky_workaround",
        rationale: "rationale",
        residualRisks: [],
        manualReviewRequired: true,
      },
      mode: "batch",
    });

    expect(score).toBeGreaterThan(70);
  });
});
