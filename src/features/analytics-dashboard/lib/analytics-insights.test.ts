import { describe, expect, it } from "vitest";
import { buildAnalyticsHotspots, summarizeAnalyticsHotspots } from "./analytics-insights";

describe("analytics insights", () => {
  const findings = [
    {
      id: "finding-1",
      severity: "critical" as const,
      title: "Escalated session risk hotspot",
      file: "app/auth/session.py",
      line: 10,
      lineEnd: 14,
      category: "session misuse",
      confidence: 90,
      summary: "",
      impact: "Session checks can be bypassed.",
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
      title: "Verification failed on query patch",
      file: "app/db/query.py",
      line: 33,
      lineEnd: 35,
      category: "SQL injection",
      confidence: 82,
      summary: "",
      impact: "User input still reaches the query sink.",
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
      title: "Approval still pending for redirect fix",
      file: "app/routes/redirect.ts",
      line: 12,
      lineEnd: 12,
      category: "Open redirect",
      confidence: 73,
      summary: "",
      impact: "Users can be redirected to attacker-controlled origins.",
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

  it("builds analytics hotspots sorted by pressure priority", () => {
    const hotspots = buildAnalyticsHotspots(findings);

    expect(hotspots).toHaveLength(3);
    expect(hotspots[0].finding.title).toBe("Escalated session risk hotspot");
    expect(hotspots[0].pressureClass).toBe("approval-drag");
    expect(hotspots[0].pressurePriority).toBe("critical");
    expect(hotspots[1].pressureClass).toBe("verification-drag");
    expect(hotspots[2].pressureClass).toBe("approval-drag");
  });

  it("summarizes analytics hotspot pressure", () => {
    const summary = summarizeAnalyticsHotspots(buildAnalyticsHotspots(findings));

    expect(summary.hotspotCount).toBe(3);
    expect(summary.criticalHotspots).toBe(2);
    expect(summary.verificationDrag).toBe(1);
    expect(summary.approvalDrag).toBe(2);
    expect(summary.policyDrag).toBe(0);
    expect(summary.riskDrag).toBe(0);
    expect(summary.topHotspotLabel).toMatch(/critical/i);
    expect(summary.topHotspotLabel).toMatch(/escalated session risk hotspot/i);
  });
});
