import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { DecisionCenterScreen } from "./DecisionCenterScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
  },
}));

describe("DecisionCenterScreen", () => {
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
    approvalStatus: "not_required" as const,
    approvalHistory: [],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
  };

  it("renders finding decision details", () => {
    render(<DecisionCenterScreen finding={finding} onBack={vi.fn()} onSuggestFix={vi.fn()} onOpenPolicyCenter={vi.fn()} />);

    expect(screen.getByText(/decision center/i)).toBeInTheDocument();
    expect(screen.getByText(/recommended action/i)).toBeInTheDocument();
    expect(screen.getByText(/triage band/i)).toBeInTheDocument();
    expect(screen.getByText(/execution disposition/i)).toBeInTheDocument();
    expect(screen.getByText(/policy outcome/i)).toBeInTheDocument();
    expect(screen.getByText(/policy summary/i)).toBeInTheDocument();
    expect(screen.getByText(/policy controls/i)).toBeInTheDocument();
    expect(screen.getByText(/stop state/i)).toBeInTheDocument();
    expect(screen.getByText(/apply readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/escalation/i)).toBeInTheDocument();
    expect(screen.getByText(/prefer sink-level parameterization/i)).toBeInTheDocument();
  });

  it("forwards the suggest fix action", () => {
    const onSuggestFix = vi.fn();
    render(<DecisionCenterScreen finding={finding} onBack={vi.fn()} onSuggestFix={onSuggestFix} onOpenPolicyCenter={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: /suggest fix/i }));

    expect(onSuggestFix).toHaveBeenCalledTimes(1);
  });

  it("shows the approval audit summary when present", () => {
    render(
      <DecisionCenterScreen
        finding={{
          ...finding,
          approvalStatus: "escalated",
          approvalHistory: [
            {
              status: "escalated",
              note: "Security lead requested an additional review before local apply.",
              timestamp: "2026-04-12T00:00:00Z",
            },
          ],
        }}
        onBack={vi.fn()}
        onSuggestFix={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    expect(screen.getByText(/approval audit/i)).toBeInTheDocument();
    expect(screen.getByText(/approval audit - escalated review/i)).toBeInTheDocument();
    expect(screen.getByText(/security lead requested an additional review/i)).toBeInTheDocument();
  });

  it("opens policy center from the decision surface", () => {
    const onOpenPolicyCenter = vi.fn();
    render(
      <DecisionCenterScreen
        finding={finding}
        onBack={vi.fn()}
        onSuggestFix={vi.fn()}
        onOpenPolicyCenter={onOpenPolicyCenter}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /open policy center/i }));

    expect(onOpenPolicyCenter).toHaveBeenCalledTimes(1);
  });
});
