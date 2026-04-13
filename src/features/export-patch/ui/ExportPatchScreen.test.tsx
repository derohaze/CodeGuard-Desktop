import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { ExportPatchScreen } from "./ExportPatchScreen";

const downloadTextFile = vi.fn();
const toastError = vi.fn();
const toastSuccess = vi.fn();

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

vi.mock("@/components/ui/sonner", () => ({
  toast: {
    success: (...args: unknown[]) => toastSuccess(...args),
    error: (...args: unknown[]) => toastError(...args),
  },
}));

vi.mock("@/entities/finding/lib/export-patch", async () => {
  const actual = await vi.importActual<typeof import("@/entities/finding/lib/export-patch")>("@/entities/finding/lib/export-patch");
  return {
    ...actual,
    downloadTextFile: (...args: unknown[]) => downloadTextFile(...args),
  };
});

describe("ExportPatchScreen", () => {
  const finding = {
    id: "finding-1",
    severity: "high" as const,
    title: "Dynamic request URL may allow SSRF",
    file: "src/lib/api/admin/chat.ts",
    line: 22,
    lineEnd: 23,
    category: "SSRF",
    confidence: 81,
    summary: "summary",
    impact: "impact",
    explanation: "explanation",
    evidence: "evidence",
    attackSimulation: { input: "input", execution: "execution", result: "result" },
    auditLog: [],
    fixSuggestions: [],
    remediationStatus: "verified_partial" as const,
    appliedStrategyId: "strategy-1",
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };

  const action = {
    findingId: "finding-1",
    status: "applied" as const,
    file: "src/lib/api/admin/chat.ts",
    appliedStrategyId: "strategy-1",
    fixType: "full_fix" as const,
    validationNotes: [],
    manualEditApplied: false,
    checkpointId: "cp-1",
    rollbackAvailable: true,
    verificationStatus: "manual_review_required" as const,
    verificationNotes: ["Destination validation still requires manual review."],
    verificationConfidence: null,
    verificationConfidenceValid: false,
    approvalGateOutcome: "review-required" as const,
    approvalGateReason: "The local patch was applied, but deterministic verification still requires human review before closure.",
    writeScope: "src/lib/api/admin/chat.ts",
    networkPolicy: "Patch apply and rollback do not call external services.",
  };

  const snapshot = {
    file: "src/lib/api/admin/chat.ts",
    diff: "@@ remediation diff @@\n-old\n+new",
    beforeSnippet: "old",
    afterSnippet: "new",
    strategyId: "strategy-1",
    strategyLabel: "Validate destination host",
    fixType: "full_fix" as const,
    summary: "Move destination validation to the request boundary.",
    rationale: "Trusted host validation is enforced before the outbound request.",
    residualRisks: ["Service allowlisting should still be reviewed."],
    manualEdit: false,
    mode: "single" as const,
  };

  it("shows a recovery state instead of rendering blank when the export snapshot is missing", () => {
    const onBack = vi.fn();
    const onOpenResults = vi.fn();

    render(
      <ExportPatchScreen
        finding={null}
        action={null}
        snapshot={null}
        onBack={onBack}
        onOpenResults={onOpenResults}
      />,
    );

    expect(screen.getByText(/export bundle is no longer available/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^back$/i }));
    expect(onBack).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /view updated results/i }));
    expect(onOpenResults).toHaveBeenCalledTimes(1);
  });

  it("copies the patch diff and remediation summary", async () => {
    vi.stubGlobal("navigator", {
      clipboard: { writeText: vi.fn(async () => undefined) },
    });

    render(
      <ExportPatchScreen
        finding={finding}
        action={action}
        snapshot={snapshot}
        onBack={vi.fn()}
        onOpenResults={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /copy diff/i }));
    await waitFor(() =>
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining("+new"))
    );

    fireEvent.click(screen.getByRole("button", { name: /copy summary/i }));
    await waitFor(() =>
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining("Dynamic request URL may allow SSRF"))
    );
  });

  it("downloads the patch artifact and supports navigation", () => {
    const onBack = vi.fn();
    const onOpenResults = vi.fn();
    render(
      <ExportPatchScreen
        finding={finding}
        action={action}
        snapshot={snapshot}
        onBack={onBack}
        onOpenResults={onOpenResults}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /download \.patch/i }));
    expect(downloadTextFile).toHaveBeenCalledWith(expect.stringContaining(".patch"), expect.stringContaining("+new"));

    fireEvent.click(screen.getByRole("button", { name: /back to verification/i }));
    expect(onBack).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /view updated results/i }));
    expect(onOpenResults).toHaveBeenCalledTimes(1);
  });
});
