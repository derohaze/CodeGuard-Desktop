import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { ApprovalQueueScreen } from "./ApprovalQueueScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

describe("ApprovalQueueScreen", () => {
  it("shows an empty state when no analyst session is open", () => {
    render(
      <ApprovalQueueScreen
        session={null}
        onSelectFinding={vi.fn()}
        onOpenResults={vi.fn()}
      />,
    );

    expect(screen.getByText(/no analyst session is open/i)).toBeInTheDocument();
  });

  it("opens the selected finding from the queued items", () => {
    const finding = {
      id: "finding-1",
      severity: "high" as const,
      title: "Session token is not rotated after login",
      file: "src/auth/session.ts",
      line: 22,
      lineEnd: 23,
      category: "Session misuse",
      confidence: 84,
      summary: "summary",
      impact: "impact",
      explanation: "explanation",
      evidence: "session.id = existingId",
      attackSimulation: { input: "input", execution: "execution", result: "result" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "verified_partial" as const,
      approvalStatus: "not_required" as const,
      approvalHistory: [],
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
      decisionSummary: {
        validationLabel: "Validated finding",
        validationNote: "Validated note",
        riskScore: 86,
        riskLabel: "Immediate attention",
        triageBand: "Review before closure",
        triageRank: 2,
        executionDisposition: "Do not auto-close; verification follow-up required",
        approvalState: "Approval required",
        policyOutcome: "review-required",
        policyReason: "Policy requires human review before closure.",
        stopState: "hold-for-review",
        applyReadiness: "approval-required-before-apply",
        escalationState: "required",
        policySummary: {
          posture: "review",
          label: "Review-controlled path",
          summary: "Policy allows remediation only through review.",
          autoPathState: "gated",
          humanPathState: "approval-required",
          nextControl: "collect-approval",
        },
        residualRiskState: "Residual risk remains until follow-up verification closes the path",
        recommendedAction: "Keep the finding open until follow-up verification.",
        fixRecommendation: "Rotate the session.",
        approvalPath: "Human approval is required.",
        approvalAuditSummary: {
          status: "not_required",
          label: "No approval gate",
          summary: "No stored approval decision is required.",
          note: "No approval note is required for the current remediation path.",
          timestamp: null,
          resolutionCategory: "not-required",
          source: "policy-default",
        },
        riskFactors: [],
      },
    };
    const onSelectFinding = vi.fn();

    render(
      <ApprovalQueueScreen
        session={{
          session: {
            id: "session-1",
            title: "Auth analyst run",
            repo: "backend",
            time: "2026-04-11 03:26 UTC",
            unread: false,
            status: "completed",
            preview: "preview",
            scanMode: "deep",
            criticalCount: 0,
            warningCount: 1,
            findingsCount: 1,
            candidateFindingsCount: 0,
            progress: 100,
            phaseProgress: 100,
            progressMessage: "Completed",
            currentPhase: "Done",
            elapsedSeconds: 16,
            progressLogs: [],
            progressCounters: null,
            runtimeMetrics: null,
            scanPlan: null,
            repositorySummary: null,
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
            coverageSummary: null,
            coveragePercent: 100,
            reviewedFilesCount: 1,
            eligibleFilesCount: 1,
            reviewedBlocksCount: 1,
            totalBlocksCount: 1,
            reviewedLinesCount: 10,
            totalLinesCount: 10,
            tracedPathsCount: 1,
            totalPathsCount: 1,
            skippedFilesCount: 0,
            highRiskFilesCount: 1,
            isSafe: false,
            securityScore: 61,
            scoreRationale: null,
            targetType: "folder",
            sourcePath: "D:/repo",
            preset: "balanced",
            lastVerification: null,
            createdAt: "2026-04-11T00:00:00Z",
            updatedAt: "2026-04-11T00:00:00Z",
          },
          verdict: "issues_found",
          issues: {
            critical: 0,
            high: 1,
            medium: 0,
            low: 0,
          },
          findings: [finding],
          candidateFindings: [],
          errorMessage: null,
        }}
        onSelectFinding={onSelectFinding}
        onOpenResults={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /session token is not rotated after login/i }));

    expect(onSelectFinding).toHaveBeenCalledWith(finding);
    expect(screen.getByText(/open verification/i)).toBeInTheDocument();
    expect(screen.getByText(/review before closure - risk 86\/100/i)).toBeInTheDocument();
  });

  it("shows escalated review items distinctly", () => {
    render(
      <ApprovalQueueScreen
        session={{
          session: {
            id: "session-2",
            title: "Escalated analyst run",
            repo: "backend",
            time: "2026-04-11 03:26 UTC",
            unread: false,
            status: "completed",
            preview: "preview",
            scanMode: "deep",
            criticalCount: 1,
            warningCount: 0,
            findingsCount: 1,
            candidateFindingsCount: 0,
            progress: 100,
            phaseProgress: 100,
            progressMessage: "Completed",
            currentPhase: "Done",
            elapsedSeconds: 20,
            progressLogs: [],
            progressCounters: null,
            runtimeMetrics: null,
            scanPlan: null,
            repositorySummary: null,
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
            coverageSummary: null,
            coveragePercent: 100,
            reviewedFilesCount: 1,
            eligibleFilesCount: 1,
            reviewedBlocksCount: 1,
            totalBlocksCount: 1,
            reviewedLinesCount: 10,
            totalLinesCount: 10,
            tracedPathsCount: 1,
            totalPathsCount: 1,
            skippedFilesCount: 0,
            highRiskFilesCount: 1,
            isSafe: false,
            securityScore: 44,
            scoreRationale: null,
            targetType: "folder",
            sourcePath: "D:/repo",
            preset: "balanced",
            lastVerification: null,
            createdAt: "2026-04-11T00:00:00Z",
            updatedAt: "2026-04-11T00:00:00Z",
          },
          verdict: "issues_found",
          issues: {
            critical: 1,
            high: 0,
            medium: 0,
            low: 0,
          },
          findings: [{
            id: "finding-2",
            severity: "critical" as const,
            title: "Authorization flow can be bypassed",
            file: "src/auth/guard.ts",
            line: 10,
            lineEnd: 12,
            category: "Authorization bypass",
            confidence: 92,
            summary: "summary",
            impact: "impact",
            explanation: "explanation",
            evidence: "if (isAdmin || req.user.id === id)",
            attackSimulation: { input: "input", execution: "execution", result: "result" },
            auditLog: [],
            fixSuggestions: [],
            remediationStatus: "patch_generated" as const,
            approvalStatus: "escalated" as const,
            approvalHistory: [
              {
                status: "escalated" as const,
                note: "Escalated for additional approval review.",
                timestamp: "2026-04-12T00:00:00Z",
              },
            ],
            appliedStrategyId: null,
            remediationNotes: [],
            attemptedStrategyIds: [],
            decisionSummary: {
              validationLabel: "Validated finding",
              validationNote: "Validated note",
              riskScore: 93,
              riskLabel: "Immediate attention",
              triageBand: "Priority 1",
              triageRank: 2,
              executionDisposition: "Review patch before any apply",
              approvalState: "Escalated for review",
              policyOutcome: "review-required",
              policyReason: "This remediation path was escalated for additional review.",
              stopState: "hold-for-review",
              applyReadiness: "approval-required-before-apply",
              escalationState: "already-escalated",
              policySummary: {
                posture: "review",
                label: "Escalated policy review",
                summary: "Escalated review remains active.",
                autoPathState: "gated",
                humanPathState: "escalated-review",
                nextControl: "resolve-escalation",
              },
              residualRiskState: "Risk remains active until a verified remediation is applied",
              recommendedAction: "Keep the finding in review.",
              fixRecommendation: "Structural authorization fix.",
              approvalPath: "This remediation path is escalated for additional review before any workspace apply or rollout.",
              approvalAuditSummary: {
                status: "escalated",
                label: "Escalated review",
                summary: "This remediation path is held in escalated review.",
                note: "Escalated for additional approval review.",
                timestamp: "2026-04-12T00:00:00Z",
                resolutionCategory: "held",
                source: "approval-controller",
              },
              riskFactors: [],
            },
          }],
          candidateFindings: [],
          errorMessage: null,
        }}
        onSelectFinding={vi.fn()}
        onOpenResults={vi.fn()}
      />,
    );

    expect(screen.getByText(/escalated review/i)).toBeInTheDocument();
    expect(screen.getByText(/additional review before any workspace apply/i)).toBeInTheDocument();
  });
});
