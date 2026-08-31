import type { Finding, RemediationActionResult } from "@/entities/finding/model/types";
import { buildApprovalQueue } from "@/entities/finding/lib/approval-queue";
import type { SessionStatus } from "@/entities/session/model/types";
import type { AppScreen } from "@/shared/types/app";

export type RemediationWorkflowPhase = "idle" | "suggesting" | "review" | "applying" | "rejected";

const APPROVAL_WORKFLOW_SCREENS: AppScreen[] = [
  "approval-queue",
  "patch-ready",
  "verification",
  "export-patch",
  "policy-center",
];

export function resolveSessionOpenScreen(input: {
  currentScreen: AppScreen;
  sessionStatus: SessionStatus;
  findings?: Finding[];
  findingOriginScreen?: AppScreen | null;
}): AppScreen {
  const { currentScreen, sessionStatus, findings = [], findingOriginScreen = null } = input;

  if (sessionStatus === "completed") {
    const hasApprovalQueueItems = buildApprovalQueue(findings).length > 0;
    const isApprovalWorkflowScreen = APPROVAL_WORKFLOW_SCREENS.includes(currentScreen)
      || (currentScreen === "finding-detail" && findingOriginScreen === "approval-queue");

    if (isApprovalWorkflowScreen && hasApprovalQueueItems) {
      return "approval-queue";
    }
  }

  return sessionStatus === "completed" ? "scan-completed" : "scan-progress";
}

export function resolvePostApplyRoute(action: RemediationActionResult): {
  screen: AppScreen;
  phase: RemediationWorkflowPhase;
} {
  if (action.status === "validation_failed") {
    return { screen: "approval-queue", phase: "review" };
  }

  return { screen: "verification", phase: "review" };
}

export function resolvePostRollbackScreen(action: RemediationActionResult): AppScreen {
  return action.status === "rolled_back" ? "scan-completed" : "patch-ready";
}

export function resolveFindingDismissScreen(originScreen: AppScreen | null): AppScreen {
  if (originScreen === "approval-queue") {
    return "approval-queue";
  }

  if (originScreen === "audit-trail") {
    return "audit-trail";
  }

  return "scan-completed";
}

export function resolvePostRejectScreen(findings: Finding[], findingId: string): AppScreen {
  const queuedIds = new Set(buildApprovalQueue(findings).map((item) => item.findingId));
  return queuedIds.has(findingId) ? "approval-queue" : "scan-completed";
}

export function resolveApprovalQueueFindingRoute(input: {
  finding: Finding;
  hasPlan: boolean;
  hasExecution: boolean;
}): AppScreen {
  if (
    (input.finding.remediationStatus === "patch_generated" || input.finding.remediationStatus === "validation_failed")
    && input.hasPlan
  ) {
    return "patch-ready";
  }

  if (input.finding.remediationStatus === "verified_partial" && input.hasExecution) {
    return "verification";
  }

  return "finding-detail";
}

export function shouldRetainReviewContext(screen: AppScreen): boolean {
  return screen === "patch-ready";
}

export function shouldRetainFindingContext(screen: AppScreen): boolean {
  return screen === "verification"
    || screen === "decision-center"
    || screen === "policy-center"
    || screen === "finding-detail"
    || screen === "export-patch";
}

export function resolveReviewEntryRoute(): {
  screen: AppScreen;
  phase: RemediationWorkflowPhase;
} {
  return {
    screen: "patch-ready",
    phase: "review",
  };
}
