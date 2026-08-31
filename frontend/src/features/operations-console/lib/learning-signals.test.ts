import { describe, expect, it } from "vitest";
import type { Finding } from "@/entities/finding/model/types";
import { buildLearningSignals, summarizeLearningSignals } from "./learning-signals";

describe("learning-signals", () => {
  it("classifies reuse, suppression, approval, and verification learning patterns", () => {
    const signals = buildLearningSignals([
      buildFinding({
        id: "reuse",
        remediationStatus: "verified_fixed",
        appliedStrategyId: "parameterize-query",
      }),
      buildFinding({
        id: "suppression",
        remediationStatus: "validation_failed",
        attemptedStrategyIds: ["guard-input", "sanitize-query"],
      }),
      buildFinding({
        id: "approval",
        approvalStatus: "escalated",
        approvalHistory: [{ status: "escalated", note: "Needs extra review", timestamp: "2026-04-12T00:00:00Z" }],
      }),
      buildFinding({
        id: "verification",
        remediationStatus: "verified_partial",
        remediationNotes: ["Verification left residual risk open."],
      }),
    ]);

    expect(signals.some((item) => item.signalClass === "reuse-signal")).toBe(true);
    expect(signals.some((item) => item.signalClass === "suppression-signal")).toBe(true);
    expect(signals.some((item) => item.signalClass === "approval-pattern")).toBe(true);
    expect(signals.some((item) => item.signalClass === "verification-pattern")).toBe(true);
  });

  it("summarizes learning-loop pressure correctly", () => {
    const summary = summarizeLearningSignals(
      buildLearningSignals([
        buildFinding({
          id: "suppression",
          remediationStatus: "validation_failed",
          attemptedStrategyIds: ["guard-input", "sanitize-query"],
        }),
        buildFinding({
          id: "verification",
          remediationStatus: "verified_partial",
          remediationNotes: ["Verification left residual risk open."],
        }),
      ]),
    );

    expect(summary.signalCount).toBe(2);
    expect(summary.criticalSignals).toBe(2);
    expect(summary.suppressionSignals).toBe(1);
    expect(summary.verificationPatterns).toBe(1);
  });
});

function buildFinding(overrides: Partial<Finding>): Finding {
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
    attackSimulation: { input: "", execution: "", result: "" },
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
