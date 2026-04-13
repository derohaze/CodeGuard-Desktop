import { motion } from "framer-motion";
import { ChevronDown, Send } from "lucide-react";
import { fixedCode } from "@/data/mockAppData";
import { CodeBlock } from "./CodeBlock";

export function PatchReadyScreen() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex-1 bg-surface overflow-y-auto"
    >
      <div className="max-w-2xl mx-auto px-8 py-8">
        <p className="text-sm font-semibold text-foreground mb-6">
          [Security Scan] Fix command_injection: app/services/notifiers/script_runner.py
        </p>

        <section className="mb-6">
          <h3 className="text-sm font-semibold text-foreground mb-3">The Fix</h3>
          <p className="text-sm text-text-secondary leading-relaxed mb-4">
            I replaced the vulnerable code with secure subprocess execution:
          </p>
          <CodeBlock code={fixedCode} />
        </section>

        <div className="space-y-2 text-sm text-text-secondary mb-6">
          <p>File modified: <span className="font-mono text-foreground">app/services/notifiers/script_runner.py</span></p>
          <p>Lines changed: <span className="text-success">4 insertions</span>, <span className="text-critical">4 deletions</span></p>
          <p>Commit: <span className="font-mono text-foreground">f774881</span></p>
        </div>

        <p className="text-sm text-text-secondary mb-8">A patch is ready for your review.</p>

        {/* Footer */}
        <div className="flex items-center gap-3 pt-4 border-t border-border-soft">
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center px-3 py-1.5 rounded-lg border border-border-soft text-xs font-medium text-foreground bg-card"
          >
            Diffs <span className="text-success ml-1.5">+4</span> <span className="text-critical ml-1">-4</span>
          </motion.span>

          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Reply..."
              className="w-full px-4 py-2 rounded-xl border border-border-soft bg-card text-sm text-foreground placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
            />
            <button className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-lg hover:bg-muted transition-colors">
              <Send size={14} className="text-text-tertiary" />
            </button>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="flex"
          >
            <button className="px-4 py-2 rounded-l-xl bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity">
              Create PR
            </button>
            <button className="px-2 py-2 rounded-r-xl bg-primary text-primary-foreground border-l border-primary-foreground/20 hover:opacity-90 transition-opacity">
              <ChevronDown size={14} />
            </button>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
