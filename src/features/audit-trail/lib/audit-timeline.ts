import type { Finding } from "@/entities/finding/model/types";

export interface AuditTimelineEvent {
  id: string;
  source: "approval" | "remediation" | "audit";
  label: string;
  detail: string;
  timestamp: string | null;
  sortKey: number;
}

export function buildAuditTimeline(finding: Finding): AuditTimelineEvent[] {
  const approvalEvents = finding.approvalHistory.map((entry, index) => ({
    id: `approval-${index}-${entry.status}`,
    source: "approval" as const,
    label: `Approval ${entry.status}`,
    detail: entry.note || "Approval state recorded without a note.",
    timestamp: entry.timestamp,
    sortKey: buildSortKey(entry.timestamp, index),
  }));

  const remediationEvents = finding.remediationNotes.map((note, index) => ({
    id: `remediation-${index}`,
    source: "remediation" as const,
    label: buildRemediationEventLabel(finding.remediationStatus, index, finding.remediationNotes.length),
    detail: note,
    timestamp: null,
    sortKey: buildFallbackSortKey(approvalEvents.length + index),
  }));

  const auditEvents = finding.auditLog.map((detail, index) => ({
    id: `audit-${index}`,
    source: "audit" as const,
    label: `Audit log ${index + 1}`,
    detail,
    timestamp: null,
    sortKey: buildFallbackSortKey(approvalEvents.length + remediationEvents.length + index),
  }));

  return [...approvalEvents, ...remediationEvents, ...auditEvents].sort((left, right) => right.sortKey - left.sortKey);
}

export function summarizeAuditTimeline(events: AuditTimelineEvent[]) {
  const latestEvent = events[0] ?? null;
  const approvalEvents = events.filter((event) => event.source === "approval").length;
  const remediationEvents = events.filter((event) => event.source === "remediation").length;
  const auditEvents = events.filter((event) => event.source === "audit").length;

  return {
    totalEvents: events.length,
    approvalEvents,
    remediationEvents,
    auditEvents,
    latestEventLabel: latestEvent?.label ?? "No audit events recorded",
    latestEventDetail: latestEvent?.detail ?? "No audit events recorded for this finding.",
  };
}

function buildRemediationEventLabel(status: Finding["remediationStatus"], index: number, count: number) {
  if (index === count - 1) {
    return `Remediation ${status}`;
  }

  return `Remediation note ${index + 1}`;
}

function buildSortKey(timestamp: string | null, index: number) {
  if (!timestamp) {
    return buildFallbackSortKey(index);
  }

  const parsed = new Date(timestamp).getTime();
  if (Number.isNaN(parsed)) {
    return buildFallbackSortKey(index);
  }

  return parsed + index;
}

function buildFallbackSortKey(index: number) {
  return -1_000_000_000 - index;
}
