export type AppScreen =
  | "home"
  | "analytics-dashboard"
  | "audit-trail"
  | "governance-center"
  | "repo-overview"
  | "service-exposure"
  | "team-security-posture"
  | "approval-queue"
  | "decision-center"
  | "policy-center"
  | "operations-console"
  | "export-patch"
  | "verification"
  | "scan-empty"
  | "scan-starting"
  | "scan-progress"
  | "scan-completed"
  | "finding-detail"
  | "suggest-fix"
  | "patch-ready";

export type AppView = "workspace" | "settings";

export type WorkspaceMode = "security" | "builder";
