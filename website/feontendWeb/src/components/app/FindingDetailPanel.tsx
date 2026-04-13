import { motion } from "framer-motion";
import { type Finding, vulnerableCode, dataFlow } from "@/data/mockAppData";
import { CodeBlock } from "./CodeBlock";
import { Loader } from "./Loader";
import { useState } from "react";

interface Props {
  finding: Finding;
  onDismiss: () => void;
  onSuggestFix: () => void;
}

export function FindingDetailPanel({ finding, onDismiss, onSuggestFix }: Props) {
  const [loading, setLoading] = useState(false);

  const handleSuggestFix = () => {
    setLoading(true);
    setTimeout(() => {
      onSuggestFix();
    }, 500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="flex-1 bg-surface overflow-y-auto"
    >
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h2 className="text-lg font-semibold text-foreground mb-8">{finding.title}</h2>

        <section className="mb-8">
          <h3 className="text-sm font-semibold text-foreground mb-3">Details</h3>
          <p className="text-sm text-text-secondary leading-relaxed mb-4">
            The <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">ScriptNotifier</code> class constructs a shell command by directly interpolating the <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">message</code> parameter into a string passed to <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">subprocess.Popen()</code> with <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">shell=True</code>:
          </p>
          <CodeBlock code={vulnerableCode} />
          <p className="text-sm text-text-secondary leading-relaxed mt-4">
            The <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">message</code> originates from incoming webhook payloads received at the public <code className="font-mono text-critical text-xs bg-critical-bg/10 px-1.5 py-0.5 rounded">/api/incoming/{"{slug}"}</code> endpoint, which requires no authentication. When webhooks are dispatched to script-type destinations, attacker-controlled data flows into shell command execution without sanitization.
          </p>
        </section>

        <section className="mb-8">
          <h3 className="text-sm font-semibold text-foreground mb-3">Data flow:</h3>
          <ol className="space-y-2">
            {dataFlow.map((step, i) => (
              <li key={i} className="flex gap-3 text-sm text-text-secondary">
                <span className="text-text-tertiary font-medium">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="mb-8">
          <h3 className="text-sm font-semibold text-foreground mb-2">Location</h3>
          <p className="text-sm text-text-secondary font-mono">
            <a href="#" className="underline underline-offset-2 decoration-text-tertiary">{finding.file}:{finding.line}</a>
          </p>
        </section>

        <section className="mb-10">
          <h3 className="text-sm font-semibold text-foreground mb-2">Impact</h3>
          <p className="text-sm text-text-secondary leading-relaxed">
            Remote code execution on the server via unauthenticated webhook requests
          </p>
        </section>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border-soft">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onDismiss}
            disabled={loading}
            className="px-5 py-2 rounded-xl border border-border-soft bg-card text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            Dismiss
          </motion.button>
          <motion.button
            whileHover={!loading ? { scale: 1.02 } : {}}
            whileTap={!loading ? { scale: 0.98 } : {}}
            onClick={handleSuggestFix}
            disabled={loading}
            className="px-5 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-80"
          >
            {loading && <Loader variant="spin" className="size-4 text-primary-foreground" />}
            {loading ? "Loading..." : "Suggest fix"}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
