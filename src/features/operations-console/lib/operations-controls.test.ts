import { describe, expect, it } from "vitest";
import type { ScanSessionDetail } from "@/shared/api/security";
import { buildLearningSignals } from "./learning-signals";
import { buildOperationsAutonomySignals } from "./operations-autonomy";
import { buildOperationsControlDecisions, summarizeOperationsControlDecisions } from "./operations-controls";

describe("operations-controls", () => {
  it("classifies hold, recovery, and stabilization controls from current workflow state", () => {
    const session = buildSessionDetail();
    const decisions = buildOperationsControlDecisions(
      session,
      buildOperationsAutonomySignals(session),
      buildLearningSignals(session.findings),
    );

    expect(decisions.some((item) => item.controlMode === "hold")).toBe(true);
    expect(decisions.some((item) => item.controlMode === "recover")).toBe(true);
    expect(decisions.some((item) => item.controlMode === "stabilize")).toBe(true);
  });

  it("summarizes control-plan pressure correctly", () => {
    const session = buildSessionDetail();
    const summary = summarizeOperationsControlDecisions(
      buildOperationsControlDecisions(
        session,
        buildOperationsAutonomySignals(session),
        buildLearningSignals(session.findings),
      ),
    );

    expect(summary.decisionCount).toBe(3);
    expect(summary.criticalDecisions).toBeGreaterThan(0);
    expect(summary.holdDecisions).toBe(1);
    expect(summary.recoverDecisions).toBe(1);
    expect(summary.stabilizeDecisions).toBe(1);
  });
});

function buildSessionDetail(): ScanSessionDetail {
  return {
    session: {
      id: "session-1",
      title: "April Security Run",
      repo: "secure-scan-studio-main",
      time: "10m ago",
      unread: false,
      status: "completed",
      preview: "Workflow closure is human-controlled while approval pressure remains open.",
      scanMode: "deep",
      criticalCount: 1,
      warningCount: 2,
      findingsCount: 1,
      candidateFindingsCount: 0,
      progress: 100,
      phaseProgress: 100,
      progressMessage: "Completed",
      currentPhase: "Completed",
      elapsedSeconds: 120,
      progressLogs: [],
      progressCounters: null,
      runtimeMetrics: null,
      scanPlan: null,
      repositorySummary: "Repository summary",
      repositoryInventory: null,
      frameworkProfile: null,
      repositoryGraph: null,
      graphSummary: null,
      securityRegistry: null,
      segmentationSummary: null,
      pathInventory: null,
      pathSummary: null,
      reviewQueueSummary: null,
      annotations: [],
      annotationSummary: null,
      coverageSnapshot: null,
      coverageSummary: "Coverage summary",
      coveragePercent: 88,
      reviewedFilesCount: 12,
      eligibleFilesCount: 14,
      reviewedBlocksCount: 50,
      totalBlocksCount: 60,
      reviewedLinesCount: 400,
      totalLinesCount: 450,
      tracedPathsCount: 8,
      totalPathsCount: 10,
      skippedFilesCount: 2,
      highRiskFilesCount: 3,
      isSafe: false,
      securityScore: 76,
      scoreRationale: null,
      targetType: "folder",
      sourcePath: "D:\\HAZE\\projects\\secure-scan-studio-main",
      preset: "balanced",
      lastVerification: null,
      workflowSummary: {
        state: "approval-control",
        label: "Approval hold",
        summary: "Approval is still required before local apply.",
        nextAction: "Collect approval",
        activeController: "approval-controller",
        plannerStage: "apply-ready",
        recoverySummary: null,
        recoveryExecution: {
          selectedPath: "manual-review",
          executionState: "stalled",
          executionLane: "manual-lane",
          reenteredPlanner: false,
          pathReason: "Recovery is waiting for manual review.",
        },
        memorySummary: null,
        operationsSummary: {
          currentLane: "approval-lane",
          nextLane: "closure-lane",
          pendingHandoff: true,
          handoffReason: "Approval is still pending.",
          activeItemCount: 2,
        },
        operationsExecution: {
          currentHandoff: "decision -> approval",
          handoffStatus: "blocked",
          owningController: "approval-controller",
          pendingExecutionStep: "Collect reviewer input",
          stepCompletionState: "waiting",
        },
        workflowClosure: {
          closureState: "human-controlled",
          closureLabel: "Human-controlled",
          closureReason: "Approval and escalation remain open.",
          autonomousReady: false,
          requiresHumanControl: true,
          nextClosureStep: "collect approval",
        },
        blockingItems: 2,
      },
      createdAt: "2026-04-12T02:00:00Z",
      updatedAt: "2026-04-12T03:00:00Z",
    },
    issues: { critical: 1, high: 1, medium: 0, low: 0 },
    findings: [
      {
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
        remediationStatus: "validation_failed",
        approvalStatus: "escalated",
        approvalHistory: [{ status: "escalated", note: "Needs extra review", timestamp: "2026-04-12T00:00:00Z" }],
        appliedStrategyId: null,
        remediationNotes: ["Verification left residual risk open."],
        attemptedStrategyIds: ["guard-input", "sanitize-query"],
        decisionSummary: null,
      },
    ],
    candidateFindings: [],
    verdict: "issues_found",
    completedAt: "2026-04-12T03:00:00Z",
    errorMessage: null,
  };
}
