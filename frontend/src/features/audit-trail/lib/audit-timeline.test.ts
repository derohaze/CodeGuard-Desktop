import { describe, expect, it } from "vitest";
import { buildAuditTimeline, summarizeAuditTimeline } from "./audit-timeline";

describe("buildAuditTimeline", () => {
  const finding = {
    id: "finding-1",
    severity: "high" as const,
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
    auditLog: [
      "Approval gate held the patch for reviewer confirmation.",
      "Security reviewer asked for stronger sink alignment.",
    ],
    fixSuggestions: [],
    remediationStatus: "validation_failed" as const,
    approvalStatus: "escalated" as const,
    approvalHistory: [
      {
        status: "pending" as const,
        note: "Waiting for the platform owner to approve the patch.",
        timestamp: "2026-04-12T01:10:00Z",
      },
      {
        status: "escalated" as const,
        note: "Security lead escalated the patch for manual review.",
        timestamp: "2026-04-12T03:10:00Z",
      },
    ],
    appliedStrategyId: null,
    remediationNotes: [
      "Patch generated and queued for review.",
      "Initial apply failed validation and returned to review.",
    ],
    attemptedStrategyIds: ["guard-1"],
    decisionSummary: null,
  };

  it("orders approval events by timestamp before fallback notes", () => {
    const timeline = buildAuditTimeline(finding);

    expect(timeline[0].label).toBe("Approval escalated");
    expect(timeline[1].label).toBe("Approval pending");
    expect(timeline.at(-1)?.source).toBe("audit");
  });

  it("summarizes latest signal and event counts", () => {
    const summary = summarizeAuditTimeline(buildAuditTimeline(finding));

    expect(summary.totalEvents).toBe(6);
    expect(summary.approvalEvents).toBe(2);
    expect(summary.remediationEvents).toBe(2);
    expect(summary.auditEvents).toBe(2);
    expect(summary.latestEventLabel).toBe("Approval escalated");
    expect(summary.latestEventDetail).toMatch(/manual review/i);
  });
});
