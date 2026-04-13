import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { findings, type Finding } from "@/data/mockAppData";
import { SeverityBadge } from "@/components/SeverityBadge";

interface Props {
  onSelectFinding: (finding: Finding) => void;
  selectedFindingId?: string;
}

export function ScanResultsScreen({ onSelectFinding, selectedFindingId }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex-1 px-8 py-8 overflow-y-auto"
    >
      <div className="max-w-2xl mx-auto space-y-4">
        {/* Summary card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl bg-card border border-border-soft p-5 flex items-center justify-between shadow-sm"
        >
          <div>
            <p className="text-sm font-semibold text-foreground">acme-corp/hookrelay</p>
            <p className="text-xs text-text-tertiary mt-0.5">1 minute ago · 4 findings</p>
          </div>
          <div className="flex items-center gap-1.5 text-success">
            <CheckCircle2 size={16} />
            <span className="text-sm font-medium">Completed</span>
          </div>
        </motion.div>

        {/* Findings card */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl bg-card border border-border-soft overflow-hidden shadow-sm"
        >
          <div className="px-5 pt-5 pb-3">
            <h3 className="text-sm font-semibold text-foreground">4 findings</h3>
          </div>
          <div className="divide-y divide-border-soft">
            {findings.map((finding, i) => (
              <motion.button
                key={finding.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.25 + i * 0.06 }}
                onClick={() => onSelectFinding(finding)}
                className={`w-full text-left px-5 py-4 flex items-start gap-4 transition-colors ${
                  selectedFindingId === finding.id
                    ? "bg-muted/60"
                    : "hover:bg-muted/30"
                }`}
              >
                <div className="mt-0.5">
                  <SeverityBadge severity={finding.severity} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground leading-snug">{finding.title}</p>
                  <p className="text-xs text-text-tertiary mt-1">
                    {finding.file}:{finding.line} · {finding.category}
                  </p>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
