import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export function ScanProgressScreen() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex-1 flex flex-col items-center justify-center px-8 py-12"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Loader2 size={40} className="text-text-secondary animate-spin" />
      </motion.div>

      <h2 className="text-xl font-semibold text-foreground mb-2">Scan in progress</h2>
      <motion.p
        animate={{ opacity: [1, 0.5, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="text-sm text-text-secondary max-w-md text-center mb-8 leading-relaxed"
      >
        The assistant analyzes your repositories for vulnerabilities, misconfigurations, and potential security issues.
      </motion.p>

      <button
        disabled
        className="px-6 py-2.5 rounded-xl bg-muted text-text-tertiary text-sm font-medium cursor-not-allowed"
      >
        Starting...
      </button>
    </motion.div>
  );
}
