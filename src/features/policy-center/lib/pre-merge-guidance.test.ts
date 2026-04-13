import { describe, expect, it } from "vitest";
import type { Finding } from "@/entities/finding/model/types";
import { buildPreMergeGuidance, summarizePreMergeGuidance } from "./pre-merge-guidance";

describe("pre-merge-guidance", () => {
  it("classifies merge blockers and review gates for a blocked escalated finding", () => {
    const guidance = buildPreMergeGuidance(buildFinding());

    expect(guidance.some((item) => item.guidanceClass === "merge-blocker")).toBe(true);
    expect(guidance.some((item) => item.guidanceClass === "review-gate")).toBe(true);
    expect(guidance.some((item) => item.guidanceClass === "verification-gate")).toBe(false);
    expect(guidance.some((item) => item.guidanceClass === "hardening-followup")).toBe(false);
  });

  it("summarizes pre-merge pressure correctly", () => {
    const summary = summarizePreMergeGuidance(buildPreMergeGuidance(buildFinding()));

    expect(summary.guidanceCount).toBe(2);
    expect(summary.criticalGuidance).toBeGreaterThan(0);
    expect(summary.mergeBlockers).toBe(1);
    expect(summary.reviewGates).toBe(1);
    expect(summary.verificationGates).toBe(0);
  });
});

function buildFinding(): Finding {
  return {
    id: "finding-1",
    severity: "high",
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "SQL injection auth flow",
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
    remediationStatus: "validation_failed",
    approvalStatus: "escalated",
    approvalHistory: [
      {
        status: "escalated",
        note: "Security lead requested an additional review before local apply.",
        timestamp: "2026-04-12T00:00:00Z",
      },
    ],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };
}
