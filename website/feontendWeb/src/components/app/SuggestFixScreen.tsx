import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { taskLines } from "@/data/mockAppData";

interface Props {
  onComplete: () => void;
}

export function SuggestFixScreen({ onComplete }: Props) {
  const [visibleLines, setVisibleLines] = useState(0);

  useEffect(() => {
    const total = taskLines.length;
    let current = 0;
    const interval = setInterval(() => {
      current++;
      setVisibleLines(current);
      if (current >= total) {
        clearInterval(interval);
        setTimeout(onComplete, 800);
      }
    }, 700);
    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex-1 bg-surface overflow-y-auto"
    >
      <div className="max-w-2xl mx-auto px-8 py-8 space-y-1">
        {taskLines.slice(0, visibleLines).map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="py-1.5"
          >
            {line.type === "header" ? (
              <p className="text-sm font-semibold text-foreground">{line.text}</p>
            ) : line.type === "status" ? (
              <StatusText text={line.text} />
            ) : (
              <p className="text-sm text-text-secondary">{line.text}</p>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

function StatusText({ text }: { text: string }) {
  return (
    <motion.p
      animate={{ opacity: [1, 0.5, 1] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      className="text-sm font-medium text-accent"
    >
      {text}
    </motion.p>
  );
}
