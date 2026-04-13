import { describe, expect, it } from "vitest";
import type { Session } from "@/entities/session/model/types";
import { buildTeamPostureHotspots, summarizeTeamPostureHotspots } from "./team-posture-intelligence";

describe("team-posture-intelligence", () => {
  it("classifies workspace hotspots by control, risk, coverage, and throughput pressure", () => {
    const hotspots = buildTeamPostureHotspots([
      buildSession({
        id: "session-control",
        repo: "auth-service",
        workflowSummary: {
          state: "approval-control",
          label: "Approval hold",
          summary: "Waiting for approval",
          nextAction: "Collect approval",
          activeController: "approval-controller",
          blockingItems: 1,
          workflowClosure: {
            closureState: "human-controlled",
            closureLabel: "Human-controlled",
            closureReason: "Approval is still required.",
            autonomousReady: false,
            requiresHumanControl: true,
            nextClosureStep: "collect approval",
          },
        },
      }),
      buildSession({
        id: "session-risk",
        repo: "payments-api",
        criticalCount: 2,
        securityScore: 68,
      }),
      buildSession({
        id: "session-coverage",
        repo: "reporting-worker",
        coveragePercent: 82,
        skippedFilesCount: 3,
      }),
      buildSession({
        id: "session-throughput",
        repo: "gateway",
        status: "failed",
      }),
    ]);

    expect(hotspots).toHaveLength(4);
    expect(hotspots.some((item) => item.hotspotClass === "control-drag")).toBe(true);
    expect(hotspots.some((item) => item.hotspotClass === "risk-drag")).toBe(true);
    expect(hotspots.some((item) => item.hotspotClass === "coverage-drag")).toBe(true);
    expect(hotspots.some((item) => item.hotspotClass === "throughput-drag")).toBe(true);
  });

  it("summarizes workspace hotspot pressure and top priority session", () => {
    const summary = summarizeTeamPostureHotspots(
      buildTeamPostureHotspots([
        buildSession({
          id: "session-control",
          repo: "auth-service",
          workflowSummary: {
            state: "approval-control",
            label: "Approval hold",
            summary: "Waiting for approval",
            nextAction: "Collect approval",
            activeController: "approval-controller",
            blockingItems: 1,
            workflowClosure: {
              closureState: "human-controlled",
              closureLabel: "Human-controlled",
              closureReason: "Approval is still required.",
              autonomousReady: false,
              requiresHumanControl: true,
              nextClosureStep: "collect approval",
            },
          },
        }),
        buildSession({
          id: "session-throughput",
          repo: "gateway",
          status: "failed",
        }),
      ]),
    );

    expect(summary.hotspotCount).toBe(2);
    expect(summary.criticalHotspots).toBe(2);
    expect(summary.controlDrag).toBe(1);
    expect(summary.throughputDrag).toBe(1);
    expect(summary.topHotspotLabel).toContain("auth-service");
  });
});

function buildSession(overrides: Partial<Session>): Session {
  return {
    id: "session-1",
    title: "Workspace session",
    repo: "secure-scan-studio-main",
    time: "10m ago",
    unread: false,
    status: "completed",
    preview: "Workspace posture preview",
    scanMode: "deep",
    criticalCount: 0,
    warningCount: 1,
    findingsCount: 2,
    candidateFindingsCount: 1,
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
    coveragePercent: 94,
    reviewedFilesCount: 10,
    eligibleFilesCount: 12,
    reviewedBlocksCount: 30,
    totalBlocksCount: 36,
    reviewedLinesCount: 240,
    totalLinesCount: 300,
    tracedPathsCount: 5,
    totalPathsCount: 6,
    skippedFilesCount: 0,
    highRiskFilesCount: 1,
    isSafe: false,
    securityScore: 84,
    scoreRationale: null,
    targetType: "folder",
    sourcePath: "D:\\HAZE\\projects\\secure-scan-studio-main",
    preset: "balanced",
    lastVerification: null,
    workflowSummary: null,
    createdAt: "2026-04-12T02:00:00Z",
    updatedAt: "2026-04-12T03:00:00Z",
    ...overrides,
  };
}
