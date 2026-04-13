import { describe, expect, it } from "vitest";
import { buildFindingDecisionSummary } from "@/entities/finding/lib/decision-center";
import { buildPreMergeGuidance } from "./pre-merge-guidance";
import { buildPreventionLedger, summarizePreventionLedger } from "./prevention-ledger";

describe("prevention ledger", () => {
  it("summarizes approval and verification prevention gates", () => {
    const finding = buildFinding();
    const decision = buildFindingDecisionSummary(finding);
    const guidance = buildPreMergeGuidance(finding);
    const items = buildPreventionLedger({ finding, decision, preMergeGuidance: guidance });
    const summary = summarizePreventionLedger(items);

    expect(summary.itemCount).toBeGreaterThan(0);
    expect(summary.approvalItems).toBeGreaterThan(0);
    expect(summary.verificationItems).toBeGreaterThan(0);
  });
});

function buildFinding() {
  return {
    id: "finding-1",
    severity: "high",
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "Session misuse",
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
    remediationStatus: "verified_partial",
    approvalStatus: "pending",
    approvalHistory: [],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };
}
