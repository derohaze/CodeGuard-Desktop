import { describe, expect, it } from "vitest";
import {
  resolveApprovalQueueFindingRoute,
  resolveFindingDismissScreen,
  resolvePostApplyRoute,
  resolvePostRejectScreen,
  resolvePostRollbackScreen,
  resolveReviewEntryRoute,
  resolveSessionOpenScreen,
  shouldRetainFindingContext,
  shouldRetainReviewContext,
} from "./remediation-workflow";

describe("remediation workflow", () => {
  it("keeps the approval queue open when switching completed sessions inside that workflow", () => {
    const queuedFinding = {
      id: "finding-1",
      severity: "high" as const,
      title: "Session token is not rotated",
      file: "src/auth/session.ts",
      line: 10,
      lineEnd: 11,
      category: "Session misuse",
      confidence: 81,
      summary: "summary",
      impact: "impact",
      explanation: "explanation",
      evidence: "evidence",
      attackSimulation: { input: "input", execution: "execution", result: "result" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "patch_generated" as const,
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
    };

    expect(
      resolveSessionOpenScreen({
        currentScreen: "approval-queue",
        sessionStatus: "completed",
        findings: [queuedFinding],
      }),
    ).toBe("approval-queue");
    expect(
      resolveSessionOpenScreen({
        currentScreen: "approval-queue",
        sessionStatus: "scanning",
        findings: [queuedFinding],
      }),
    ).toBe("scan-progress");
  });

  it("reopens completed sessions in the approval queue when switching from an approval workflow screen", () => {
    const queuedFinding = {
      id: "finding-1",
      severity: "high" as const,
      title: "Session token is not rotated",
      file: "src/auth/session.ts",
      line: 10,
      lineEnd: 11,
      category: "Session misuse",
      confidence: 81,
      summary: "summary",
      impact: "impact",
      explanation: "explanation",
      evidence: "evidence",
      attackSimulation: { input: "input", execution: "execution", result: "result" },
      auditLog: [],
      fixSuggestions: [],
      remediationStatus: "verified_partial" as const,
      appliedStrategyId: null,
      remediationNotes: [],
      attemptedStrategyIds: [],
    };

    expect(
      resolveSessionOpenScreen({
        currentScreen: "verification",
        sessionStatus: "completed",
        findings: [queuedFinding],
      }),
    ).toBe("approval-queue");

    expect(
      resolveSessionOpenScreen({
        currentScreen: "finding-detail",
        sessionStatus: "completed",
        findings: [queuedFinding],
        findingOriginScreen: "approval-queue",
      }),
    ).toBe("approval-queue");

    expect(
      resolveSessionOpenScreen({
        currentScreen: "patch-ready",
        sessionStatus: "completed",
        findings: [],
      }),
    ).toBe("scan-completed");
  });

  it("routes partial or blocked remediation outcomes into the approval queue", () => {
    expect(
      resolvePostApplyRoute({
        findingId: "finding-1",
        status: "validation_failed",
        file: "src/auth/session.ts",
        appliedStrategyId: null,
        fixType: "partial_mitigation",
        validationNotes: [],
        manualEditApplied: false,
        checkpointId: null,
        rollbackAvailable: false,
        verificationStatus: "not_run",
        verificationNotes: [],
        verificationConfidence: null,
        verificationConfidenceValid: false,
        writeScope: "src/auth/session.ts",
        networkPolicy: "none",
      }).screen,
    ).toBe("approval-queue");

    expect(
      resolvePostApplyRoute({
        findingId: "finding-1",
        status: "applied",
        file: "src/auth/session.ts",
        appliedStrategyId: "rotate-session",
        fixType: "full_fix",
        validationNotes: [],
        manualEditApplied: false,
        checkpointId: "cp-1",
        rollbackAvailable: true,
        verificationStatus: "manual_review_required",
        verificationNotes: [],
        verificationConfidence: null,
        verificationConfidenceValid: false,
        writeScope: "src/auth/session.ts",
        networkPolicy: "none",
      }).screen,
    ).toBe("verification");
  });

  it("returns to results after a successful rollback", () => {
    expect(
      resolvePostRollbackScreen({
        findingId: "finding-1",
        status: "rolled_back",
        file: "src/auth/session.ts",
        appliedStrategyId: null,
        fixType: "temporary_guard",
        validationNotes: [],
        manualEditApplied: false,
        checkpointId: "cp-1",
        rollbackAvailable: false,
        verificationStatus: "rolled_back",
        verificationNotes: [],
        verificationConfidence: null,
        verificationConfidenceValid: false,
        writeScope: "src/auth/session.ts",
        networkPolicy: "none",
      }),
    ).toBe("scan-completed");
  });

  it("returns finding detail back to the approval queue when opened from there", () => {
    expect(resolveFindingDismissScreen("approval-queue")).toBe("approval-queue");
    expect(resolveFindingDismissScreen("scan-completed")).toBe("scan-completed");
    expect(resolveFindingDismissScreen(null)).toBe("scan-completed");
  });

  it("returns rejected approval-sensitive findings to the approval queue", () => {
    expect(
      resolvePostRejectScreen(
        [
          {
            id: "finding-1",
            severity: "high",
            title: "Session token is not rotated",
            file: "src/auth/session.ts",
            line: 10,
            lineEnd: 11,
            category: "Session misuse",
            confidence: 81,
            summary: "summary",
            impact: "impact",
            explanation: "explanation",
            evidence: "evidence",
            attackSimulation: { input: "input", execution: "execution", result: "result" },
            auditLog: [],
            fixSuggestions: [],
            remediationStatus: "open",
            appliedStrategyId: null,
            remediationNotes: [],
            attemptedStrategyIds: [],
          },
        ],
        "finding-1",
      ),
    ).toBe("approval-queue");

    expect(
      resolvePostRejectScreen(
        [
          {
            id: "finding-2",
            severity: "medium",
            title: "Unsafe redirect",
            file: "src/http/redirect.ts",
            line: 4,
            lineEnd: 4,
            category: "Open redirect",
            confidence: 72,
            summary: "summary",
            impact: "impact",
            explanation: "explanation",
            evidence: "evidence",
            attackSimulation: { input: "input", execution: "execution", result: "result" },
            auditLog: [],
            fixSuggestions: [],
            remediationStatus: "open",
            appliedStrategyId: null,
            remediationNotes: [],
            attemptedStrategyIds: [],
          },
        ],
        "finding-2",
      ),
    ).toBe("scan-completed");
  });

  it("re-enters the best approval workflow for queued findings when cached context exists", () => {
    expect(
      resolveApprovalQueueFindingRoute({
        finding: {
          id: "finding-1",
          severity: "high",
          title: "Session token is not rotated",
          file: "src/auth/session.ts",
          line: 10,
          lineEnd: 11,
          category: "Session misuse",
          confidence: 81,
          summary: "summary",
          impact: "impact",
          explanation: "explanation",
          evidence: "evidence",
          attackSimulation: { input: "input", execution: "execution", result: "result" },
          auditLog: [],
          fixSuggestions: [],
          remediationStatus: "patch_generated",
          appliedStrategyId: null,
          remediationNotes: [],
          attemptedStrategyIds: [],
        },
        hasPlan: true,
        hasExecution: false,
      }),
    ).toBe("patch-ready");

    expect(
      resolveApprovalQueueFindingRoute({
        finding: {
          id: "finding-2",
          severity: "high",
          title: "Session token is not rotated",
          file: "src/auth/session.ts",
          line: 10,
          lineEnd: 11,
          category: "Session misuse",
          confidence: 81,
          summary: "summary",
          impact: "impact",
          explanation: "explanation",
          evidence: "evidence",
          attackSimulation: { input: "input", execution: "execution", result: "result" },
          auditLog: [],
          fixSuggestions: [],
          remediationStatus: "verified_partial",
          appliedStrategyId: null,
          remediationNotes: [],
          attemptedStrategyIds: [],
        },
        hasPlan: false,
        hasExecution: true,
      }),
    ).toBe("verification");

    expect(
      resolveApprovalQueueFindingRoute({
        finding: {
          id: "finding-3",
          severity: "medium",
          title: "Unsafe redirect",
          file: "src/http/redirect.ts",
          line: 4,
          lineEnd: 4,
          category: "Open redirect",
          confidence: 72,
          summary: "summary",
          impact: "impact",
          explanation: "explanation",
          evidence: "evidence",
          attackSimulation: { input: "input", execution: "execution", result: "result" },
          auditLog: [],
          fixSuggestions: [],
          remediationStatus: "open",
          appliedStrategyId: null,
          remediationNotes: [],
          attemptedStrategyIds: [],
        },
        hasPlan: false,
        hasExecution: false,
      }),
    ).toBe("finding-detail");
  });

  it("retains review context only for the patch review screen", () => {
    expect(shouldRetainReviewContext("patch-ready")).toBe(true);
    expect(shouldRetainReviewContext("approval-queue")).toBe(false);
    expect(shouldRetainReviewContext("scan-completed")).toBe(false);
  });

  it("retains finding context for verification, decision, and export screens", () => {
    expect(shouldRetainFindingContext("verification")).toBe(true);
    expect(shouldRetainFindingContext("decision-center")).toBe(true);
    expect(shouldRetainFindingContext("policy-center")).toBe(true);
    expect(shouldRetainFindingContext("export-patch")).toBe(true);
    expect(shouldRetainFindingContext("patch-ready")).toBe(false);
  });

  it("enters patch review through a single explicit route", () => {
    expect(resolveReviewEntryRoute()).toEqual({
      screen: "patch-ready",
      phase: "review",
    });
  });
});
