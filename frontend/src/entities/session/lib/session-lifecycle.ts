import type { Session } from "@/entities/session/model/types";

type LifecycleSummary = {
  label: string;
  tone: "neutral" | "progress" | "warning" | "success";
} | null;

export function getSessionLifecycleSummary(session: Session): LifecycleSummary {
  const lastVerificationStatus = String(session.lastVerification?.status ?? "").trim().toLowerCase();
  if (lastVerificationStatus === "rolled_back") {
    return {
      label: "Rolled back",
      tone: "warning",
    };
  }

  const counts = getRemediationStatusCounts(session);
  if (counts.validation_failed > 0) {
    return {
      label: pluralize(counts.validation_failed, "blocked patch"),
      tone: "warning",
    };
  }
  if (counts.verified_partial > 0) {
    return {
      label: pluralize(counts.verified_partial, "needs verification review"),
      tone: "progress",
    };
  }
  if (counts.patch_generated > 0) {
    return {
      label: pluralize(counts.patch_generated, "patch ready"),
      tone: "progress",
    };
  }
  if (counts.rejected > 0) {
    return {
      label: pluralize(counts.rejected, "rejected remediation"),
      tone: "neutral",
    };
  }
  if (counts.verified_fixed > 0 && session.findingsCount === 0) {
    return {
      label: pluralize(counts.verified_fixed, "verified fix"),
      tone: "success",
    };
  }
  return null;
}

function getRemediationStatusCounts(session: Session) {
  const raw = session.reviewQueueSummary?.remediation_status_counts;
  const counts = typeof raw === "object" && raw !== null ? raw as Record<string, unknown> : {};
  return {
    patch_generated: toCount(counts.patch_generated),
    verified_fixed: toCount(counts.verified_fixed),
    verified_partial: toCount(counts.verified_partial),
    validation_failed: toCount(counts.validation_failed),
    rejected: toCount(counts.rejected),
  };
}

function toCount(value: unknown): number {
  return Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0;
}

function pluralize(count: number, noun: string): string {
  if (count === 1) {
    return `${count} ${noun}`;
  }
  const suffix = noun.endsWith("ch") ? "es" : "s";
  return `${count} ${noun}${suffix}`;
}
