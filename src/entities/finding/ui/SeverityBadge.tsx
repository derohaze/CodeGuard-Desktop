import type { FindingSeverity } from "@/entities/finding/model/types";

interface Props {
  severity: FindingSeverity;
}

export function SeverityBadge({ severity }: Props) {
  const styles = {
    critical: "bg-status-critical-bg text-status-critical border-status-critical/20",
    high: "bg-status-high-bg text-status-high border-status-high/20",
    medium: "bg-[#fbf7f1] text-[#9a7d57] border-[#e6d8c5]",
    low: "bg-[#f6f1ea] text-[#8f877a] border-[#dfd2c1]",
  };

  return (
    <span className={`inline-flex items-center rounded-lg border px-2.5 py-0.5 text-xs font-medium capitalize ${styles[severity]}`}>
      {severity}
    </span>
  );
}
