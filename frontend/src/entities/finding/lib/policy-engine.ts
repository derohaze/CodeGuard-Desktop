import type { Finding, FindingDecisionSummary } from "@/entities/finding/model/types";

export function buildPolicyOutcome({
  finding,
  riskScore,
  touchesIdentity,
  safeAutoPath,
}: {
  finding: Finding;
  riskScore: number;
  touchesIdentity: boolean;
  safeAutoPath: boolean;
}): FindingDecisionSummary["policyOutcome"] {
  if (finding.remediationStatus === "validation_failed") {
    return "blocked-by-policy";
  }
  if (getApprovalStatus(finding) === "approved" && finding.remediationStatus !== "verified_partial" && safeAutoPath) {
    return "auto-eligible";
  }
  if (
    touchesIdentity
    || finding.remediationStatus === "verified_partial"
    || finding.remediationStatus === "patch_generated"
    || finding.remediationStatus === "rejected"
    || finding.remediationStatus === "rolled_back"
    || finding.severity === "critical"
    || finding.severity === "high"
    || riskScore >= 85
  ) {
    return "review-required";
  }
  return "auto-eligible";
}

export function buildPolicyReason({
  finding,
  riskScore,
  touchesIdentity,
  safeAutoPath,
}: {
  finding: Finding;
  riskScore: number;
  touchesIdentity: boolean;
  safeAutoPath: boolean;
}): string {
  if (finding.remediationStatus === "validation_failed") {
    return "The last remediation attempt was blocked by a safety boundary, so this path cannot proceed without a stronger patch.";
  }
  if (getApprovalStatus(finding) === "approved" && finding.remediationStatus !== "verified_partial" && safeAutoPath) {
    return "This remediation path already has an explicit approval record, so workspace apply can proceed within the current review session.";
  }
  if (getApprovalStatus(finding) === "approved" && finding.remediationStatus !== "verified_partial" && !safeAutoPath) {
    return "Approval is recorded for this remediation path, but policy still keeps it on a human-controlled review track because the decision pressure remains too high for autonomous progression.";
  }
  if (touchesIdentity) {
    return "This finding touches identity, session, or authorization logic, so policy requires human review before closure.";
  }
  if (finding.remediationStatus === "verified_partial") {
    return "A workspace patch exists, but policy still requires verification review before final closure.";
  }
  if (finding.remediationStatus === "patch_generated") {
    return "A patch is ready, but policy still requires explicit review before workspace apply.";
  }
  if (finding.severity === "critical" || finding.severity === "high" || riskScore >= 85) {
    return "This finding has enough decision pressure that policy requires human review before broader rollout.";
  }
  return "This finding is localized enough to stay eligible for the normal remediation flow.";
}

export function buildPolicySummary(
  finding: Finding,
  touchesIdentity: boolean,
  riskScore: number,
  safeAutoPath: boolean,
): FindingDecisionSummary["policySummary"] {
  const approvalStatus = getApprovalStatus(finding);
  const policyOutcome = buildPolicyOutcome({ finding, riskScore, touchesIdentity, safeAutoPath });
  if (policyOutcome === "blocked-by-policy") {
    return {
      posture: "block",
      label: "Blocked by policy",
      summary: "The current remediation path cannot proceed because policy requires a stronger or safer patch.",
      autoPathState: "forbidden",
      humanPathState: "regenerate-required",
      nextControl: "generate-a-stronger-patch",
    };
  }
  if (approvalStatus === "approved" && finding.remediationStatus !== "verified_partial") {
    return {
      posture: safeAutoPath ? "allow" : "review",
      label: safeAutoPath ? "Approved within policy" : "Approved but still human-controlled",
      summary: safeAutoPath
        ? "Policy allows this remediation path to proceed because the required approval is already recorded."
        : "Approval is recorded, but policy still keeps this remediation path on a human-controlled track because the remaining decision pressure is too high for autonomous progression.",
      autoPathState: safeAutoPath ? "eligible" : "gated",
      humanPathState: "approved-review-cycle",
      nextControl: "proceed-with-workspace-apply",
    };
  }
  if (approvalStatus === "escalated") {
    return {
      posture: "review",
      label: "Escalated policy review",
      summary: "Policy keeps this remediation path in escalated review until the higher-risk decision is resolved.",
      autoPathState: "gated",
      humanPathState: "escalated-review",
      nextControl: "resolve-escalation",
    };
  }
  if (policyOutcome === "review-required") {
    return {
      posture: "review",
      label: "Review-controlled path",
      summary: "Policy allows remediation to continue only through an explicit human-controlled review path.",
      autoPathState: "gated",
      humanPathState: "approval-required",
      nextControl: "collect-approval",
    };
  }
  return {
    posture: "allow",
    label: "Standard policy flow",
    summary: "Policy allows this remediation path to stay on the standard low-risk flow after patch review.",
    autoPathState: "eligible",
    humanPathState: "standard-review",
    nextControl: "continue-standard-review",
  };
}

function getApprovalStatus(finding: Finding): Finding["approvalStatus"] {
  return finding.approvalStatus ?? "not_required";
}
