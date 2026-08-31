import type { Finding, PatchCandidate, RemediationPlan, RemediationStrategy } from "@/entities/finding/model/types";

export function calculateFindingRiskScore(finding: Finding, touchesIdentity: boolean): number {
  const severityBase = {
    critical: 92,
    high: 78,
    medium: 58,
    low: 36,
  }[finding.severity];
  const confidenceAdjustment = Math.round((finding.confidence - 70) / 4);
  const lifecycleAdjustment =
    finding.remediationStatus === "validation_failed"
      ? 6
      : finding.remediationStatus === "verified_partial"
        ? 4
        : finding.remediationStatus === "verified_fixed"
          ? -22
          : 0;
  const identityAdjustment = touchesIdentity ? 8 : 0;
  return clamp(severityBase + confidenceAdjustment + lifecycleAdjustment + identityAdjustment, 0, 100);
}

export function calculatePatchRiskScore({
  severity,
  confidence,
  touchesIdentity,
  selectedStrategy,
  patch,
  mode,
}: {
  severity: Finding["severity"];
  confidence: number;
  touchesIdentity: boolean;
  selectedStrategy: RemediationStrategy | null | undefined;
  patch: PatchCandidate | null | undefined;
  mode: RemediationPlan["mode"];
}): number {
  const severityBase = {
    critical: 90,
    high: 76,
    medium: 58,
    low: 42,
  }[severity];
  const confidenceAdjustment = Math.round((confidence - 70) / 5);
  const regressionAdjustment =
    selectedStrategy?.regressionRisk === "high"
      ? 12
      : selectedStrategy?.regressionRisk === "medium"
        ? 6
        : 0;
  const policyAdjustment = selectedStrategy?.policyCompliant === false ? 14 : 0;
  const manualReviewAdjustment = patch?.manualReviewRequired ? 8 : 0;
  const batchAdjustment = mode === "batch" ? 6 : 0;
  const identityAdjustment = touchesIdentity ? 10 : 0;
  return clamp(
    severityBase + confidenceAdjustment + regressionAdjustment + policyAdjustment + manualReviewAdjustment + batchAdjustment + identityAdjustment,
    0,
    100,
  );
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
