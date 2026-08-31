import type { Finding } from "@/entities/finding/model/types";

export function orderFindingsByDecisionPriority(findings: Finding[]): Finding[] {
  return [...findings].sort((left, right) => {
    const leftRank = Number(left.decisionSummary?.triageRank ?? 999);
    const rightRank = Number(right.decisionSummary?.triageRank ?? 999);
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }

    const leftScore = Number(left.decisionSummary?.riskScore ?? 0);
    const rightScore = Number(right.decisionSummary?.riskScore ?? 0);
    if (rightScore !== leftScore) {
      return rightScore - leftScore;
    }

    const severityDelta = severityRank(right.severity) - severityRank(left.severity);
    if (severityDelta !== 0) {
      return severityDelta;
    }

    return left.title.localeCompare(right.title);
  });
}

function severityRank(severity: Finding["severity"]): number {
  switch (severity) {
    case "critical":
      return 4;
    case "high":
      return 3;
    case "medium":
      return 2;
    default:
      return 1;
  }
}
