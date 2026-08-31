import type { Finding } from "@/entities/finding/model/types";

export function getRemediationStatusLabel(status: Finding["remediationStatus"]) {
  switch (status) {
    case "patch_generated":
      return "Plan ready";
    case "applied":
      return "Applied";
    case "verified_fixed":
      return "Verified fixed";
    case "verified_partial":
      return "Needs review";
    case "validation_failed":
      return "Apply failed";
    case "rejected":
      return "Rejected";
    case "rolled_back":
      return "Rolled back";
    default:
      return "Open";
  }
}

export function getRemediationStatusTone(status: Finding["remediationStatus"]) {
  switch (status) {
    case "verified_fixed":
      return "success";
    case "patch_generated":
    case "applied":
      return "progress";
    case "verified_partial":
    case "validation_failed":
      return "warning";
    case "rejected":
    case "rolled_back":
      return "muted";
    default:
      return "default";
  }
}
