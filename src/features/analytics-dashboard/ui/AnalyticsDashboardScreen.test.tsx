import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { AnalyticsDashboardScreen } from "./AnalyticsDashboardScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

describe("AnalyticsDashboardScreen", () => {
  const session = {
    session: {
      repo: "secure-scan-studio-main",
    },
    findings: [
      {
        id: "finding-1",
        severity: "high" as const,
        title: "Dynamic query construction may allow injection",
        file: "app/features/login/router.py",
        line: 43,
        lineEnd: 44,
        category: "SQL injection",
        confidence: 84,
        summary: "",
        impact: "",
        explanation: "",
        evidence: "",
        attackSimulation: { input: "", execution: "", result: "" },
        auditLog: [],
        fixSuggestions: [],
        remediationStatus: "patch_generated" as const,
        approvalStatus: "pending" as const,
        approvalHistory: [],
        appliedStrategyId: null,
        remediationNotes: [],
        attemptedStrategyIds: [],
        decisionSummary: null,
      },
      {
        id: "finding-2",
        severity: "medium" as const,
        title: "Unvalidated redirect parameter",
        file: "app/routes/redirect.ts",
        line: 12,
        lineEnd: 12,
        category: "Open redirect",
        confidence: 72,
        summary: "",
        impact: "",
        explanation: "",
        evidence: "",
        attackSimulation: { input: "", execution: "", result: "" },
        auditLog: [],
        fixSuggestions: [],
        remediationStatus: "verified_fixed" as const,
        approvalStatus: "approved" as const,
        approvalHistory: [],
        appliedStrategyId: null,
        remediationNotes: [],
        attemptedStrategyIds: [],
        decisionSummary: null,
      },
    ],
  };

  it("renders analytics summaries and distributions", () => {
    render(<AnalyticsDashboardScreen session={session as never} onBack={vi.fn()} onOpenRepoOverview={vi.fn()} />);

    expect(screen.getByText(/analytics dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/remediation outcomes/i)).toBeInTheDocument();
    expect(screen.getByText(/approval distribution/i)).toBeInTheDocument();
    expect(screen.getAllByText(/risk distribution/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/policy pressure/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/hotspot queue/i)).toBeInTheDocument();
    expect(screen.getAllByText(/analytics ledger/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/analytics hotspots/i)).toBeInTheDocument();
    expect(screen.getAllByText(/dynamic query construction may allow injection/i).length).toBeGreaterThan(0);
  });

  it("supports back navigation", () => {
    const onBack = vi.fn();
    const onOpenRepoOverview = vi.fn();
    render(<AnalyticsDashboardScreen session={session as never} onBack={onBack} onOpenRepoOverview={onOpenRepoOverview} />);

    fireEvent.click(screen.getByRole("button", { name: /open repo overview/i }));
    fireEvent.click(screen.getByRole("button", { name: /^back$/i }));

    expect(onOpenRepoOverview).toHaveBeenCalledTimes(1);
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
