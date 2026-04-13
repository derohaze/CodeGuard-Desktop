import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { SuggestFixScreen } from "./SuggestFixScreen";
import type { ReactNode } from "react";

const generateFix = vi.fn();
const generateBatchRemediation = vi.fn();

vi.mock("@/shared/api/security", () => ({
  generateFix: (...args: unknown[]) => generateFix(...args),
  generateBatchRemediation: (...args: unknown[]) => generateBatchRemediation(...args),
}));

vi.mock("@/components/ui/sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("@/components/ui/shiny-text", () => ({
  ShinyText: ({ text, className }: { text: string; className?: string }) => <span className={className}>{text}</span>,
}));

vi.mock("framer-motion", () => ({
  AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: { children?: ReactNode }) => <span {...props}>{children}</span>,
  },
}));

describe("SuggestFixScreen", () => {
  beforeEach(() => {
    generateFix.mockReset();
    generateBatchRemediation.mockReset();
    vi.useRealTimers();
  });

  it("does not advance to patch review until the user confirms", async () => {
    const plan = {
      mode: "single",
      findingIds: ["finding-1"],
      reviewSummary: "Prepared a review-ready patch.",
      explanation: null,
      strategies: [
        {
          id: "parameterized-query",
          label: "Parameterized query",
          kind: "refactor",
          confidence: 92,
          impact: "high",
          effort: "medium",
          summary: "Replace interpolation with a parameterized query.",
          rationale: "Derived from the traced path.",
          diff: "--- a/router.py\n+++ b/router.py",
          recommended: true,
          fixType: "full_fix",
          securityStrength: "high",
          regressionRisk: "low",
          selectionReason: "Strongest safe option.",
          nonSelectionReason: "",
          residualRisks: [],
          policyCompliant: true,
          policyViolations: [],
        },
      ],
      recommendedStrategyId: "parameterized-query",
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "Parameterize the login query.",
        diff: "--- a/router.py\n+++ b/router.py",
        validationNotes: [],
        beforeSnippet: "query = f\"...\"",
        afterSnippet: "query = \"SELECT ... WHERE email = %s\"",
        fixType: "full_fix",
        rationale: "Protect the sink.",
        residualRisks: [],
        manualReviewRequired: false,
      },
      steps: [
        { id: "context_shape", title: "Building remediation context", status: "done", agent: "context_agent", details: ["Loaded evidence."] },
        { id: "final_patch", title: "Preparing review-ready patch", status: "done", agent: "fix_agent", details: ["Prepared a patch."] },
      ],
      metrics: {
        file: "app/features/login/router.py",
        vulnerabilityType: "SQL injection",
        remediationMode: "single",
        analyzedLines: 2,
        pathSteps: 6,
        evidenceLocation: "app/features/login/router.py:43-44",
      },
      score: {
        total: 88,
        strategyQuality: 90,
        fixCompleteness: 86,
        sinkAlignment: 91,
        residualRisk: 20,
        confidence: 89,
        rationale: ["Looks good."],
      },
    };
    generateFix.mockResolvedValue(plan);
    const onComplete = vi.fn();

    render(
      <SuggestFixScreen
        onComplete={onComplete}
        sessionId="session-1"
        mode="single"
        finding={{
          id: "finding-1",
          severity: "high",
          title: "Dynamic query construction may allow injection",
          file: "app/features/login/router.py",
          line: 43,
          lineEnd: 44,
          category: "SQL injection",
          confidence: 80,
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
        }}
      />,
    );

    await waitFor(() => expect(generateFix).toHaveBeenCalledTimes(1));
    await screen.findByRole("button", { name: "Continue to patch review" });
    expect(onComplete).not.toHaveBeenCalled();
    expect(screen.getByText(/No workspace file changes have been applied yet/i)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Continue to patch review" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "View plan details" })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Try another fix" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Continue to patch review" }));

    expect(onComplete).toHaveBeenCalledWith(plan);
  });

  it("keeps the user on the remediation timeline while the plan is still running", async () => {
    let resolvePlan: ((value: unknown) => void) | null = null;
    generateFix.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePlan = resolve;
        }),
    );

    render(
      <SuggestFixScreen
        onComplete={vi.fn()}
        sessionId="session-1"
        mode="single"
        finding={{
          id: "finding-1",
          severity: "high",
          title: "Dynamic query construction may allow injection",
          file: "app/features/login/router.py",
          line: 43,
          lineEnd: 44,
          category: "SQL injection",
          confidence: 80,
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
        }}
      />,
    );

    expect(await screen.findByText(/context agent/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Try another fix" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Continue to patch review" })).not.toBeInTheDocument();
    expect(screen.queryByText("Remediation agents are running")).not.toBeInTheDocument();
    expect(screen.queryByText(/No file writes yet/i)).not.toBeInTheDocument();

    resolvePlan?.({
      mode: "single",
      findingIds: ["finding-1"],
      reviewSummary: "Prepared a review-ready patch.",
      explanation: null,
      strategies: [
        {
          id: "parameterized-query",
          label: "Parameterized query",
          kind: "refactor",
          confidence: 92,
          impact: "high",
          effort: "medium",
          summary: "Replace interpolation with a parameterized query.",
          rationale: "Derived from the traced path.",
          diff: "--- a/router.py\n+++ b/router.py",
          recommended: true,
          fixType: "full_fix",
          securityStrength: "high",
          regressionRisk: "low",
          selectionReason: "Strongest safe option.",
          nonSelectionReason: "",
          residualRisks: [],
          policyCompliant: true,
          policyViolations: [],
        },
      ],
      recommendedStrategyId: "parameterized-query",
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "Parameterize the login query.",
        diff: "--- a/router.py\n+++ b/router.py",
        validationNotes: [],
        beforeSnippet: "query = f\"...\"",
        afterSnippet: "query = \"SELECT ... WHERE email = %s\"",
        fixType: "full_fix",
        rationale: "Protect the sink.",
        residualRisks: [],
        manualReviewRequired: false,
      },
      steps: [
        { id: "context_shape", title: "Building remediation context", status: "done", agent: "context_agent", details: ["Loaded evidence."] },
        { id: "final_patch", title: "Preparing review-ready patch", status: "done", agent: "fix_agent", details: ["Prepared a patch."] },
      ],
      metrics: {
        file: "app/features/login/router.py",
        vulnerabilityType: "SQL injection",
        remediationMode: "single",
        analyzedLines: 2,
        pathSteps: 6,
        evidenceLocation: "app/features/login/router.py:43-44",
      },
      score: {
        total: 88,
        strategyQuality: 90,
        fixCompleteness: 86,
        sinkAlignment: 91,
        residualRisk: 20,
        confidence: 89,
        rationale: ["Looks good."],
      },
    });

    expect(await screen.findByRole("button", { name: "Continue to patch review" })).toBeInTheDocument();
  });

  it("refreshes results when remediation preflight invalidates a stale finding", async () => {
    const onInvalidatedFinding = vi.fn();
    generateFix.mockRejectedValue(new Error("This finding was invalidated during remediation preflight. The stored cross-file sink evidence no longer matches the vulnerability category."));

    render(
      <SuggestFixScreen
        onComplete={vi.fn()}
        onInvalidatedFinding={onInvalidatedFinding}
        sessionId="session-1"
        mode="single"
        finding={{
          id: "finding-1",
          severity: "high",
          title: "Cross-file request input reaches query execution",
          file: "src/App.tsx",
          line: 17,
          lineEnd: 17,
          category: "SQL injection",
          confidence: 86,
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
        }}
      />,
    );

    await waitFor(() => expect(onInvalidatedFinding).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(/No remediation strategy was produced/i)).not.toBeInTheDocument();
  });

  it("renders repeated plan details without duplicate React keys", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    generateFix.mockResolvedValue({
      mode: "single",
      findingIds: ["finding-1"],
      reviewSummary: "Prepared a review-ready patch.",
      explanation: null,
      strategies: [
        {
          id: "parameterized-query",
          label: "Parameterized query",
          kind: "refactor",
          confidence: 92,
          impact: "high",
          effort: "medium",
          summary: "Replace interpolation with a parameterized query.",
          rationale: "Derived from the traced path.",
          diff: "--- a/router.py\n+++ b/router.py",
          recommended: true,
          fixType: "full_fix",
          securityStrength: "high",
          regressionRisk: "low",
          selectionReason: "Strongest safe option.",
          nonSelectionReason: "",
          residualRisks: [],
          policyCompliant: true,
          policyViolations: [],
        },
      ],
      recommendedStrategyId: "parameterized-query",
      patch: {
        file: "app/features/login/router.py",
        language: "python",
        summary: "Parameterize the login query.",
        diff: "--- a/router.py\n+++ b/router.py",
        validationNotes: [],
        beforeSnippet: "query = f\"...\"",
        afterSnippet: "query = \"SELECT ... WHERE email = %s\"",
        fixType: "full_fix",
        rationale: "Protect the sink.",
        residualRisks: [],
        manualReviewRequired: false,
      },
      steps: [
        {
          id: "context_shape",
          title: "Building remediation context",
          status: "done",
          agent: "context_agent",
          details: [
            "Loaded evidence from app/features/chat/service.py:16-16",
            "Loaded evidence from app/features/chat/service.py:16-16",
          ],
        },
      ],
      metrics: null,
      score: null,
    });

    render(
      <SuggestFixScreen
        onComplete={vi.fn()}
        sessionId="session-1"
        mode="single"
        finding={{
          id: "finding-1",
          severity: "high",
          title: "Dynamic query construction may allow injection",
          file: "app/features/login/router.py",
          line: 43,
          lineEnd: 44,
          category: "SQL injection",
          confidence: 80,
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
        }}
      />,
    );

    await screen.findByRole("button", { name: "View plan details" });
    fireEvent.click(screen.getByRole("button", { name: "View plan details" }));
    expect(await screen.findAllByText("Loaded evidence from app/features/chat/service.py:16-16")).toHaveLength(2);
    const duplicateKeyCalls = consoleError.mock.calls.filter((call) =>
      String(call[0] ?? "").includes("Encountered two children with the same key"),
    );
    expect(duplicateKeyCalls).toHaveLength(0);
    consoleError.mockRestore();
  });
});
