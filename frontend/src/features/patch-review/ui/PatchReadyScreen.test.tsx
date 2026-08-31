import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { PatchReadyScreen } from "./PatchReadyScreen";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: { children?: ReactNode }) => <span {...props}>{children}</span>,
  },
}));

vi.mock("@/components/ui/tooltip", () => ({
  Tooltip: ({ children }: { children?: ReactNode }) => <>{children}</>,
  TooltipTrigger: ({ children }: { children?: ReactNode }) => <>{children}</>,
  TooltipContent: ({ children }: { children?: ReactNode }) => <>{children}</>,
}));

describe("PatchReadyScreen", () => {
  const finding = {
    id: "finding-1",
    severity: "high" as const,
    title: "Dynamic query construction may allow injection",
    file: "app/features/login/router.py",
    line: 43,
    lineEnd: 44,
    category: "SQL injection",
    confidence: 81,
    summary: "summary",
    impact: "impact",
    explanation: "explanation",
    evidence: "query = f\"...\"",
    attackSimulation: { input: "input", execution: "execution", result: "result" },
    auditLog: [],
    fixSuggestions: [],
    remediationStatus: "open" as const,
    approvalStatus: "not_required" as const,
    approvalHistory: [],
    appliedStrategyId: null,
    remediationNotes: [],
    attemptedStrategyIds: [],
    decisionSummary: null,
  };

  const plan = {
    mode: "single" as const,
    findingIds: ["finding-1"],
    reviewSummary: "Prepared a review-ready patch.",
    explanation: null,
    strategies: [
      {
        id: "parameterized-query",
        label: "Parameterized query",
        kind: "refactor" as const,
        confidence: 92,
        impact: "high",
        effort: "medium",
        summary: "Replace interpolation with a parameterized query.",
        rationale: "Derived from the traced path.",
        diff: "--- a/router.py\n+++ b/router.py\n@@\n-query = f\"SELECT * FROM users WHERE email = '{email}'\"\n+query = \"SELECT * FROM users WHERE email = %s\"\n+cursor.execute(query, (email,))",
        recommended: true,
        fixType: "full_fix" as const,
        securityStrength: "high" as const,
        regressionRisk: "low" as const,
        selectionReason: "Strongest safe option.",
        nonSelectionReason: "",
        residualRisks: [],
        policyCompliant: true,
        policyViolations: [],
      },
      {
        id: "allowlist-guard",
        label: "Allowlist guard",
        kind: "guard" as const,
        confidence: 74,
        impact: "medium",
        effort: "low",
        summary: "Reject suspicious payloads before the sink.",
        rationale: "Fast mitigation.",
        diff: "--- a/router.py\n+++ b/router.py\n@@\n+if \"'\" in email:\n+    raise ValueError(\"invalid email\")",
        recommended: false,
        fixType: "risky_workaround" as const,
        securityStrength: "low" as const,
        regressionRisk: "low" as const,
        selectionReason: "",
        nonSelectionReason: "Not selected because it is weaker than the recommended sink fix.",
        residualRisks: ["The sink still deserves parameterization at the query execution layer."],
        policyCompliant: false,
        policyViolations: ["The fix must eliminate the injection vector at the sink instead of screening input earlier in the path."],
      },
    ],
    recommendedStrategyId: "parameterized-query",
    patch: {
      file: "app/features/login/router.py",
      language: "python",
      summary: "Parameterize the login query.",
      diff: "--- a/router.py\n+++ b/router.py",
      validationNotes: ["The patch modifies the traced sink."],
      beforeSnippet: "query = f\"SELECT * FROM users WHERE email = '{email}'\"",
      afterSnippet: "query = \"SELECT * FROM users WHERE email = %s\"\ncursor.execute(query, (email,))",
      fixType: "full_fix" as const,
      rationale: "Protect the sink.",
      residualRisks: [],
      manualReviewRequired: false,
    },
    steps: [],
    metrics: null,
    score: {
      total: 88,
      strategyQuality: 91,
      fixCompleteness: 87,
      sinkAlignment: 96,
      residualRisk: 74,
      confidence: 92,
      rationale: ["Looks good."],
    },
  };

  it("updates the draft when a different strategy is selected", async () => {
    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={vi.fn(async () => null)}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /allowlist guard/i }));
    fireEvent.click(screen.getByRole("button", { name: /edit manually/i }));

    expect(await screen.findByDisplayValue(/raise ValueError/)).toBeInTheDocument();
  });

  it("sends a live diff from manual edits on approve", async () => {
    const onApprove = vi.fn(async () => ({
      action: {
        findingId: "finding-1",
        status: "applied" as const,
        file: "app/features/login/router.py",
        appliedStrategyId: "parameterized-query",
        fixType: "full_fix" as const,
        validationNotes: [],
        manualEditApplied: true,
        checkpointId: null,
        rollbackAvailable: false,
        verificationStatus: "not_run" as const,
        verificationNotes: [],
        verificationConfidence: null,
        verificationConfidenceValid: false,
        approvalGateOutcome: "auto-approved" as const,
        approvalGateReason: "The applied patch remains eligible for the normal low-risk remediation flow.",
        writeScope: "app/features/login/router.py",
        networkPolicy: "Patch apply and rollback do not call external services.",
      },
      session: {
        id: "session-1",
        title: "Scan backend",
        repo: "backend",
        time: "2026-04-11 03:26 UTC",
        unread: false,
        status: "completed" as const,
        preview: "preview",
        scanMode: "deep" as const,
        criticalCount: 0,
        warningCount: 0,
        findingsCount: 0,
        candidateFindingsCount: 0,
        progress: 100,
        phaseProgress: 100,
        progressMessage: "Completed",
        currentPhase: "Done",
        elapsedSeconds: 10,
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
        reviewedLinesCount: 1,
        totalLinesCount: 1,
        tracedPathsCount: 1,
        totalPathsCount: 1,
        skippedFilesCount: 0,
        highRiskFilesCount: 1,
        isSafe: true,
        securityScore: 100,
        scoreRationale: null,
        targetType: "folder" as const,
        sourcePath: "D:/repo",
        preset: "balanced" as const,
        createdAt: "2026-04-11T00:00:00Z",
        updatedAt: "2026-04-11T00:00:00Z",
        lastVerification: null,
      },
      findings: [],
      candidateFindings: [],
    }));

    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={onApprove}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /edit manually/i }));
    const editor = await screen.findByDisplayValue(/cursor\.execute/);
    fireEvent.change(editor, {
      target: {
        value: "query = \"SELECT * FROM users WHERE email = %s\"\ncursor.execute(query, (email,))\nlog_security_event(email)",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: /approve fix/i }));

    await waitFor(() => expect(onApprove).toHaveBeenCalledTimes(1));
    expect(onApprove.mock.calls[0][0].manualEdit).toBe(true);
    expect(onApprove.mock.calls[0][0].diff).toContain("+log_security_event(email)");
  });

  it("auto-selects the first compliant strategy when the recommended one is below policy", async () => {
    const onApprove = vi.fn(async () => null);
    const nonCompliantRecommendedPlan = {
      ...plan,
      recommendedStrategyId: "allowlist-guard",
      strategies: [
        { ...plan.strategies[0], recommended: false },
        { ...plan.strategies[1], recommended: true },
      ],
    };

    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={nonCompliantRecommendedPlan}
        onApprove={onApprove}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /approve fix/i }));

    await waitFor(() => expect(onApprove).toHaveBeenCalledTimes(1));
    expect(onApprove.mock.calls[0][0].strategyId).toBe("parameterized-query");
    expect(screen.queryByText(/below the enforced security policy/i)).not.toBeInTheDocument();
  });

  it("allows approve when no compliant strategy exists but keeps the risky-plan warning", async () => {
    const blockedPlan = {
      ...plan,
      recommendedStrategyId: "allowlist-guard",
      strategies: [
        { ...plan.strategies[1], recommended: true },
      ],
    };
    const onApprove = vi.fn(async () => null);

    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={blockedPlan}
        onApprove={onApprove}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/does not currently contain a policy-compliant strategy/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /approve fix/i }));

    await waitFor(() => expect(onApprove).toHaveBeenCalledTimes(1));
    expect(onApprove.mock.calls[0][0].strategyId).toBe("allowlist-guard");
  });

  it("shows finding-level approval and policy state in the patch decision panel", async () => {
    render(
      <PatchReadyScreen
        finding={{
          ...finding,
          category: "Session misuse",
          remediationStatus: "verified_partial",
          approvalStatus: "escalated",
          approvalHistory: [
            {
              status: "escalated",
              note: "Escalated for extra review before local apply.",
              timestamp: "2026-04-12T00:00:00Z",
            },
          ],
        }}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={vi.fn(async () => null)}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    expect(screen.getByText(/approval state/i)).toBeInTheDocument();
    expect(screen.getByText(/approval required/i)).toBeInTheDocument();
    expect(screen.getByText(/policy outcome/i)).toBeInTheDocument();
    expect(screen.getByText(/policy summary/i)).toBeInTheDocument();
    expect(screen.getByText(/policy controls/i)).toBeInTheDocument();
    expect(screen.getByText(/apply readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/^escalation$/i)).toBeInTheDocument();
    expect(screen.getByText(/stop state/i)).toBeInTheDocument();
    expect(screen.getByText(/review-required/i)).toBeInTheDocument();
    expect(screen.getByText(/finding requires approval review/i)).toBeInTheDocument();
    expect(screen.getByText(/approval audit/i)).toBeInTheDocument();
    expect(screen.getByText(/approval audit - escalated review/i)).toBeInTheDocument();
    expect(screen.getByText(/escalated for extra review before local apply/i)).toBeInTheDocument();
  });

  it("opens policy center from patch review", () => {
    const onOpenPolicyCenter = vi.fn();
    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={vi.fn(async () => null)}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={onOpenPolicyCenter}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /open policy center/i }));

    expect(onOpenPolicyCenter).toHaveBeenCalledTimes(1);
  });

  it("recovers from apply failures without leaving the approve action stuck", async () => {
    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={vi.fn(async () => {
          throw new Error("blocked");
        })}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /approve fix/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /approve fix/i })).toBeEnabled();
    });
  });

  it("uses workspace wording in the review flow instead of local-only wording", () => {
    render(
      <PatchReadyScreen
        finding={finding}
        findings={[finding]}
        mode="single"
        plan={plan}
        onApprove={vi.fn(async () => null)}
        onRollback={vi.fn(async () => null)}
        onReject={vi.fn(async () => null)}
        onRetry={vi.fn(async () => null)}
        onViewResults={vi.fn()}
        onOpenPolicyCenter={vi.fn()}
      />,
    );

    expect(screen.getByText(/apply to workspace/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Applied locally$/i)).not.toBeInTheDocument();
  });
});
