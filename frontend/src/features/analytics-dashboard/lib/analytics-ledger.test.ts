import { describe, expect, it } from "vitest";
import { buildAnalyticsLedger, summarizeAnalyticsLedger } from "./analytics-ledger";

describe("analytics ledger", () => {
  it("summarizes approval, policy, and verification pressure", () => {
    const items = buildAnalyticsLedger(buildFindings() as never);
    const summary = summarizeAnalyticsLedger(items);

    expect(summary.itemCount).toBeGreaterThan(0);
    expect(summary.approvalItems).toBeGreaterThan(0);
    expect(summary.policyItems).toBeGreaterThan(0);
    expect(summary.verificationItems).toBeGreaterThan(0);
  });
});

function buildFindings() {
  return [
    {
      id: "finding-1",
      severity: "high",
      title: "Dynamic query construction may allow injection",
      file: "app/features/login/router.py",
      line: 43,
      lineEnd: 44,
      category: "SQL injection",
      confidence: 84,
      summary: "",
      impact: "",
      explanation: "",
      evidence: "",
      attackSimulation: { input: "", execution: "", result: "" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "validation_failed",
      approvalStatus: "pending",
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
    {
      id: "finding-2",
      severity: "critical",
      title: "Privilege escalation risk",
      file: "app/auth/guards.py",
      line: 10,
      lineEnd: 11,
      category: "Authorization bypass",
      confidence: 90,
      summary: "",
      impact: "",
      explanation: "",
      evidence: "",
      attackSimulation: { input: "", execution: "", result: "" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "patch_generated",
      approvalStatus: "escalated",
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
  ];
}
