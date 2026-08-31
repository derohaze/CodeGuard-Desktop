import { describe, expect, it } from "vitest";
import type { Finding } from "@/entities/finding/model/types";
import { buildFindingDecisionSummary, buildPatchDecisionSummary } from "@/entities/finding/lib/decision-center";

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

describe("buildFindingDecisionSummary", () => {
  it("marks identity categories as approval-required", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        category: "Session misuse",
        remediationStatus: "verified_partial",
      }),
    );

    expect(summary.approvalPath.toLowerCase()).toContain("human approval");
    expect(summary.riskScore).toBeGreaterThanOrEqual(80);
    expect(summary.recommendedAction.toLowerCase()).toContain("keep the finding open");
    expect(summary.triageBand).toBe("Review before closure");
    expect(summary.triageRank).toBe(2);
    expect(summary.approvalState).toBe("Approval required");
    expect(summary.policyOutcome).toBe("review-required");
  });

  it("treats verified fixes as lower residual decision pressure", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        remediationStatus: "verified_fixed",
      }),
    );

    expect(summary.riskScore).toBeLessThan(78);
    expect(summary.recommendedAction.toLowerCase()).toContain("re-run the broader analysis");
    expect(summary.executionDisposition).toBe("Re-scan before repository closure");
    expect(summary.residualRiskState.toLowerCase()).toContain("reduced");
  });

  it("produces category-specific fix guidance for ssrf", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        category: "Server-side request forgery",
      }),
    );

    expect(summary.fixRecommendation.toLowerCase()).toContain("destination validation");
  });

  it("marks blocked remediation attempts as blocked triage", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        remediationStatus: "validation_failed",
      }),
    );

    expect(summary.triageBand).toBe("Blocked remediation");
    expect(summary.triageRank).toBe(1);
    expect(summary.policyOutcome).toBe("blocked-by-policy");
    expect(summary.executionDisposition).toBe("Blocked pending stronger patch");
    expect(summary.residualRiskState).toContain("Risk unchanged");
  });

  it("keeps low-pressure findings auto-eligible", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        severity: "low",
        confidence: 62,
      }),
    );

    expect(summary.policyOutcome).toBe("auto-eligible");
  });

  it("builds a normalized approval audit summary from the finding state", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        approvalStatus: "escalated",
        approvalHistory: [
          {
            status: "escalated",
            note: "Security lead requested an additional review before local apply.",
            timestamp: "2026-04-12T00:00:00Z",
          },
        ],
      }),
    );

    expect(summary.approvalAuditSummary.label).toBe("Escalated review");
    expect(summary.approvalAuditSummary.resolutionCategory).toBe("held");
    expect(summary.approvalAuditSummary.note).toContain("additional review");
  });

  it("builds a normalized policy summary from the finding state", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        remediationStatus: "validation_failed",
      }),
    );

    expect(summary.policySummary.posture).toBe("block");
    expect(summary.policySummary.autoPathState).toBe("forbidden");
    expect(summary.policySummary.nextControl).toBe("generate-a-stronger-patch");
  });

  it("keeps approved high-pressure findings on a human-controlled path", () => {
    const summary = buildFindingDecisionSummary(
      buildFinding({
        category: "Session misuse",
        remediationStatus: "patch_generated",
        approvalStatus: "approved",
        approvalHistory: [
          {
            status: "approved",
            note: "Approved for local apply only.",
            timestamp: "2026-04-12T00:00:00Z",
          },
        ],
      }),
    );

    expect(summary.policyOutcome).toBe("review-required");
    expect(summary.applyReadiness).toBe("local-apply-eligible");
    expect(summary.policySummary.posture).toBe("review");
    expect(summary.policySummary.autoPathState).toBe("gated");
    expect(summary.policySummary.humanPathState).toBe("approved-review-cycle");
  });
});

describe("buildPatchDecisionSummary", () => {
  it("marks non-compliant strategies as approval-sensitive", () => {
    const summary = buildPatchDecisionSummary({
      finding: buildFinding(),
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
        regressionRisk: "low",
        selectionReason: "",
        nonSelectionReason: "",
        residualRisks: [],
        policyCompliant: false,
        policyViolations: [],
      },
      mode: "single",
    });

    expect(summary.decisionStatus.toLowerCase()).toContain("below enforced policy");
    expect(summary.approvalPath.toLowerCase()).toContain("human review");
    expect(summary.riskScore).toBeGreaterThanOrEqual(85);
    expect(summary.policySummary.posture).toBe("review");
  });

  it("keeps recommended compliant strategies eligible for workspace apply", () => {
    const summary = buildPatchDecisionSummary({
      finding: buildFinding({
        severity: "low",
        confidence: 62,
      }),
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "summary",
        diff: "diff",
        validationNotes: [],
        beforeSnippet: "before",
        afterSnippet: "after",
        fixType: "full_fix",
        rationale: "rationale",
        residualRisks: [],
        manualReviewRequired: false,
      },
      selectedStrategy: {
        id: "refactor",
        label: "Parameterized query",
        kind: "refactor",
        confidence: 90,
        impact: "high",
        effort: "medium",
        summary: "summary",
        rationale: "rationale",
        diff: "diff",
        recommended: true,
        fixType: "full_fix",
        securityStrength: "high",
        regressionRisk: "low",
        selectionReason: "",
        nonSelectionReason: "",
        residualRisks: [],
        policyCompliant: true,
        policyViolations: [],
      },
      mode: "single",
    });

    expect(summary.decisionStatus).toBe("Eligible for workspace apply");
    expect(summary.recommendedAction.toLowerCase()).toContain("approve this patch");
    expect(summary.policySummary.posture).toBe("allow");
  });

  it("inherits review-required policy from the finding even when the strategy is compliant", () => {
    const finding = buildFinding({
      category: "Session misuse",
      remediationStatus: "verified_partial",
    });

    const summary = buildPatchDecisionSummary({
      finding,
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "summary",
        diff: "diff",
        validationNotes: [],
        beforeSnippet: "before",
        afterSnippet: "after",
        fixType: "full_fix",
        rationale: "rationale",
        residualRisks: [],
        manualReviewRequired: false,
      },
      selectedStrategy: {
        id: "refactor",
        label: "Parameterized query",
        kind: "refactor",
        confidence: 90,
        impact: "high",
        effort: "medium",
        summary: "summary",
        rationale: "rationale",
        diff: "diff",
        recommended: true,
        fixType: "full_fix",
        securityStrength: "high",
        regressionRisk: "low",
        selectionReason: "",
        nonSelectionReason: "",
        residualRisks: [],
        policyCompliant: true,
        policyViolations: [],
      },
      mode: "single",
    });

    expect(summary.policyOutcome).toBe("review-required");
    expect(summary.approvalState).toBe("Approval required");
    expect(summary.decisionStatus).toBe("Finding requires approval review");
    expect(summary.approvalPath).toBe(buildFindingDecisionSummary(finding).approvalPath);
    expect(summary.approvalAuditSummary.label).toBe("No approval gate");
    expect(summary.policySummary.humanPathState).toBe("approval-required");
  });
});
