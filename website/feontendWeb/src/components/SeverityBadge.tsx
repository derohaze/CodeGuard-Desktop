import { cn } from "@/lib/utils";

type Severity = "critical" | "high" | "medium" | "low" | "resolved";

const styles: Record<Severity, string> = {
  critical: "bg-status-critical-bg text-status-critical border-status-critical/20",
  high: "bg-status-high-bg text-status-high border-status-high/20",
  medium: "bg-muted text-text-secondary border-border",
  low: "bg-muted text-text-tertiary border-border-soft",
  resolved: "bg-status-success-bg text-status-success border-status-success/20",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border", styles[severity], className)}>
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}
