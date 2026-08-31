import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { VerificationScreen } from "./VerificationScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

vi.mock("@/shared/ui/Loader", () => ({
  Loader: () => <span>loading</span>,
}));

describe("VerificationScreen", () => {
  const finding = {
    id: "finding-1",
    severity: "high" as const,
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "SQL injection",
    confidence: 84,
    summary: "summary",
    impact: "impact",
    explanation: "explanation",
    evidence: "evidence",
    attackSimulation: { input: "input", execution: "execution", result: "result" },
    auditLog: [],
    fixSuggestions: [],
    remediationStatus: "verified_fixed" as const,
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };

  it("shows a recovery state instead of rendering blank when verification data is missing", () => {
    const onOpenResults = vi.fn();
    render(
      <VerificationScreen
        finding={null}
        action={null}
        onRollback={vi.fn(async () => null)}
        onOpenExportPatch={vi.fn()}
        onOpenResults={onOpenResults}
        onOpenApprovalQueue={vi.fn()}
      />,
    );

    expect(screen.getByText(/verification context is no longer available/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /view updated results/i }));
    expect(onOpenResults).toHaveBeenCalledTimes(1);
  });

  it("renders verification outcome details", () => {
    render(
      <VerificationScreen
        finding={finding}
        action={{
          findingId: "finding-1",
          status: "applied",
          file: "app/features/login/router.py",
          appliedStrategyId: "parameterized-query",
          fixType: "full_fix",
          validationNotes: [],
          manualEditApplied: false,
          checkpointId: "cp-1",
          rollbackAvailable: true,
          verificationStatus: "verified",
          verificationNotes: ["Parameterized query found in patched file."],
          verificationConfidence: 92,
          verificationConfidenceValid: true,
          approvalGateOutcome: "auto-approved",
          approvalGateReason: "The applied patch remains eligible for the normal low-risk remediation flow.",
          writeScope: "app/features/login/router.py",
          networkPolicy: "Patch apply and rollback do not call external services.",
        }}
        onRollback={vi.fn(async () => null)}
        onOpenExportPatch={vi.fn()}
        onOpenResults={vi.fn()}
        onOpenApprovalQueue={vi.fn()}
      />,
    );

    expect(screen.getByText(/deterministic verification passed/i)).toBeInTheDocument();
    expect(screen.getByText(/parameterized query found in patched file/i)).toBeInTheDocument();
  });

  it("opens the approval queue for manual review outcomes", () => {
    const onOpenApprovalQueue = vi.fn();
    render(
      <VerificationScreen
        finding={finding}
        action={{
          findingId: "finding-1",
          status: "applied",
          file: "app/features/login/router.py",
          appliedStrategyId: "parameterized-query",
          fixType: "full_fix",
          validationNotes: [],
          manualEditApplied: false,
          checkpointId: "cp-1",
          rollbackAvailable: true,
          verificationStatus: "manual_review_required",
          verificationNotes: ["Destination validation still requires manual review."],
          verificationConfidence: null,
          verificationConfidenceValid: false,
          approvalGateOutcome: "review-required",
          approvalGateReason: "The local patch was applied, but deterministic verification still requires human review before closure.",
          writeScope: "app/features/login/router.py",
          networkPolicy: "Patch apply and rollback do not call external services.",
        }}
        onRollback={vi.fn(async () => null)}
        onOpenExportPatch={vi.fn()}
        onOpenResults={vi.fn()}
        onOpenApprovalQueue={onOpenApprovalQueue}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /open approval queue/i }));

    expect(onOpenApprovalQueue).toHaveBeenCalledTimes(1);
  });

  it("opens the export workflow for an applied patch", () => {
    const onOpenExportPatch = vi.fn();
    render(
      <VerificationScreen
        finding={finding}
        action={{
          findingId: "finding-1",
          status: "applied",
          file: "app/features/login/router.py",
          appliedStrategyId: "parameterized-query",
          fixType: "full_fix",
          validationNotes: [],
          manualEditApplied: false,
          checkpointId: "cp-1",
          rollbackAvailable: true,
          verificationStatus: "verified",
          verificationNotes: ["Parameterized query found in patched file."],
          verificationConfidence: 92,
          verificationConfidenceValid: true,
          approvalGateOutcome: "auto-approved",
          approvalGateReason: "The applied patch remains eligible for the normal low-risk remediation flow.",
          writeScope: "app/features/login/router.py",
          networkPolicy: "Patch apply and rollback do not call external services.",
        }}
        onRollback={vi.fn(async () => null)}
        onOpenExportPatch={onOpenExportPatch}
        onOpenResults={vi.fn()}
        onOpenApprovalQueue={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /export patch/i }));

    expect(onOpenExportPatch).toHaveBeenCalledTimes(1);
  });
});
