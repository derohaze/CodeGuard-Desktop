import { describe, expect, it } from "vitest";
import { buildGovernanceQueue, summarizeGovernanceQueue } from "./governance-queue";

describe("governance queue", () => {
  const findings = [
    {
      id: "finding-1",
      severity: "critical" as const,
      title: "Session token bypass remains escalated",
      file: "app/auth/session.py",
      line: 18,
      lineEnd: 24,
      category: "session misuse",
      confidence: 91,
      summary: "",
      impact: "Privilege checks can be bypassed.",
      explanation: "",
      evidence: "",
      attackSimulation: { input: "", execution: "", result: "" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "patch_generated" as const,
      approvalStatus: "escalated" as const,
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
    {
      id: "finding-2",
      severity: "medium" as const,
      title: "Unsafe query patch failed validation",
      file: "app/db/query.py",
      line: 44,
      lineEnd: 48,
      category: "SQL injection",
      confidence: 82,
      summary: "",
      impact: "User-controlled input reaches the query sink.",
      explanation: "",
      evidence: "",
      attackSimulation: { input: "", execution: "", result: "" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "validation_failed" as const,
      approvalStatus: "not_required" as const,
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
    {
      id: "finding-3",
      severity: "high" as const,
      title: "Login fix awaits approval",
      file: "app/features/login/router.py",
      line: 43,
      lineEnd: 44,
      category: "SQL injection",
      confidence: 84,
      summary: "",
      impact: "Authentication lookups may be bypassed.",
      explanation: "",
      evidence: "",
      attackSimulation: { input: "", execution: "", result: "" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "patch_generated" as const,
      approvalStatus: "pending" as const,
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: null,
    },
  ];

  it("classifies queue items by blocker and sorts by governance priority", () => {
    const queue = buildGovernanceQueue(findings);

    expect(queue).toHaveLength(3);
    expect(queue[0].finding.title).toBe("Session token bypass remains escalated");
    expect(queue[0].blockerClass).toBe("escalation-hold");
    expect(queue[0].queuePriority).toBe("critical");
    expect(queue[1].blockerClass).toBe("approval-hold");
    expect(queue[2].blockerClass).toBe("policy-gate");
    expect(queue[2].owner).toBe("policy-controller");
  });

  it("summarizes governance pressure for the queue", () => {
    const summary = summarizeGovernanceQueue(buildGovernanceQueue(findings));

    expect(summary.queuedFindings).toBe(3);
    expect(summary.criticalItems).toBe(1);
    expect(summary.approvalHolds).toBe(1);
    expect(summary.policyGates).toBe(1);
    expect(summary.escalationHolds).toBe(1);
    expect(summary.highestPriorityLabel).toMatch(/critical/i);
    expect(summary.highestPriorityLabel).toMatch(/session token bypass/i);
  });
});
