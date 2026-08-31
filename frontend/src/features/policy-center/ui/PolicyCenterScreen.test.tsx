import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { PolicyCenterScreen } from "./PolicyCenterScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

describe("PolicyCenterScreen", () => {
  const finding = {
    id: "finding-1",
    severity: "high" as const,
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
    attackSimulation: {
      input: "POST /login",
      execution: "router -> service -> query builder",
      result: "Authentication bypass",
    },
    auditLog: [],
    fixSuggestions: [],
    remediationStatus: "open" as const,
    approvalStatus: "escalated" as const,
    approvalHistory: [
      {
        status: "escalated" as const,
        note: "Security lead requested an additional review before local apply.",
        timestamp: "2026-04-12T00:00:00Z",
      },
    ],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };

  it("renders policy posture and control details", () => {
    render(<PolicyCenterScreen finding={finding} onBack={vi.fn()} onSuggestFix={vi.fn()} />);

    expect(screen.getByText(/policy center/i)).toBeInTheDocument();
    expect(screen.getByText(/policy summary/i)).toBeInTheDocument();
    expect(screen.getByText(/auto path/i)).toBeInTheDocument();
    expect(screen.getByText(/human path/i)).toBeInTheDocument();
    expect(screen.getByText(/next control/i)).toBeInTheDocument();
    expect(screen.getByText(/policy controls/i)).toBeInTheDocument();
    expect(screen.getByText(/approval audit/i)).toBeInTheDocument();
    expect(screen.getAllByText(/pre-merge guidance/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/prevention ledger/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/merge blockers/i)).toBeInTheDocument();
  });

  it("forwards back and suggest fix actions", () => {
    const onBack = vi.fn();
    const onSuggestFix = vi.fn();
    render(<PolicyCenterScreen finding={finding} onBack={onBack} onSuggestFix={onSuggestFix} />);

    fireEvent.click(screen.getByRole("button", { name: /^back$/i }));
    fireEvent.click(screen.getByRole("button", { name: /suggest fix/i }));

    expect(onBack).toHaveBeenCalledTimes(1);
    expect(onSuggestFix).toHaveBeenCalledTimes(1);
  });
});
