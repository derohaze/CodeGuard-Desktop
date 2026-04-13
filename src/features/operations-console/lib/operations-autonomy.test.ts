import { describe, expect, it } from "vitest";
import type { ScanSessionDetail } from "@/shared/api/security";
import { buildOperationsAutonomySignals, summarizeOperationsAutonomySignals } from "./operations-autonomy";

describe("operations-autonomy", () => {
  it("classifies autonomy signals for human control, handoff pressure, and recovery drag", () => {
    const signals = buildOperationsAutonomySignals(buildSessionDetail());

    expect(signals.some((item) => item.signalClass === "human-control")).toBe(true);
    expect(signals.some((item) => item.signalClass === "handoff-drag")).toBe(true);
    expect(signals.some((item) => item.signalClass === "recovery-drag")).toBe(true);
  });

  it("summarizes autonomy signals and top pressure correctly", () => {
    const summary = summarizeOperationsAutonomySignals(buildOperationsAutonomySignals(buildSessionDetail()));

    expect(summary.signalCount).toBe(3);
    expect(summary.criticalSignals).toBeGreaterThan(0);
    expect(summary.humanControlSignals).toBe(1);
    expect(summary.handoffDragSignals).toBe(1);
    expect(summary.recoveryDragSignals).toBe(1);
    expect(summary.topSignalLabel).toContain("Human control required");
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
      findingsCount: 2,
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
    findings: [],
    candidateFindings: [],
    verdict: "issues_found",
    completedAt: "2026-04-12T03:00:00Z",
    errorMessage: null,
  };
}
