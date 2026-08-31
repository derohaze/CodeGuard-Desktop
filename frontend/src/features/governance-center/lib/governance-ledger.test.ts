import { describe, expect, it } from "vitest";
import { buildGovernanceLedger, summarizeGovernanceLedger } from "./governance-ledger";

describe("governance ledger", () => {
  it("summarizes approval, policy, and escalation pressure", () => {
    const items = buildGovernanceLedger(buildFindings() as never);
    const summary = summarizeGovernanceLedger(items);

    expect(summary.itemCount).toBeGreaterThan(0);
    expect(summary.approvalItems).toBeGreaterThan(0);
    expect(summary.policyItems).toBeGreaterThan(0);
    expect(summary.escalationItems).toBeGreaterThan(0);
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
      remediationStatus: "patch_generated",
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
      remediationStatus: "validation_failed",
      approvalStatus: "escalated",
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
  ];
}
