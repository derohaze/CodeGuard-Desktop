import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Loader } from "./Loader";

interface Props {
  onStartScan: () => void;
}

export function ScanEmptyScreen({ onStartScan }: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = () => {
    setLoading(true);
    setTimeout(() => {
      onStartScan();
    }, 600);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35 }}
      className="flex-1 flex flex-col items-center justify-center px-8 py-12"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className="w-16 h-16 rounded-2xl bg-card border border-border-soft shadow-md flex items-center justify-center mb-6"
      >
        <ShieldCheck size={28} className="text-text-secondary" />
      </motion.div>

      <h2 className="text-xl font-semibold text-foreground mb-2">Scan your code for security issues</h2>
      <p className="text-sm text-text-secondary max-w-md text-center mb-8 leading-relaxed">
        The assistant analyzes your repositories for vulnerabilities, misconfigurations, and potential security issues.
      </p>

      <motion.button
        whileHover={!loading ? { scale: 1.02 } : {}}
        whileTap={!loading ? { scale: 0.98 } : {}}
        onClick={handleClick}
        disabled={loading}
        className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium shadow-sm hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-80"
      >
        {loading && <Loader variant="spin" className="size-4 text-primary-foreground" />}
        {loading ? "Starting..." : "Start a scan"}
      </motion.button>
    </motion.div>
  );
}
