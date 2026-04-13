import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanEmptyScreen } from "./app/ScanEmptyScreen";
import { ScanProgressScreen } from "./app/ScanProgressScreen";
import { ScanResultsScreen } from "./app/ScanResultsScreen";
import { FindingDetailPanel } from "./app/FindingDetailPanel";
import { SuggestFixScreen } from "./app/SuggestFixScreen";
import { PatchReadyScreen } from "./app/PatchReadyScreen";
import { findings, type Finding } from "@/data/mockAppData";

type Screen = "empty" | "progress" | "results" | "detail" | "fixing" | "patch";

export function InteractiveDemo() {
  const [screen, setScreen] = useState<Screen>("empty");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  const handleStartScan = () => {
    setScreen("progress");
    setTimeout(() => setScreen("results"), 2000);
  };

  const handleSelectFinding = (finding: Finding) => {
    setSelectedFinding(finding);
    setScreen("detail");
  };

  const handleDismiss = () => {
    setSelectedFinding(null);
    setScreen("results");
  };

  const handleSuggestFix = () => {
    setScreen("fixing");
  };

  const handleFixComplete = () => {
    setScreen("patch");
  };

  const handleReset = () => {
    setScreen("empty");
    setSelectedFinding(null);
  };

  return (
    <div className="rounded-2xl border border-border-soft bg-surface overflow-hidden shadow-lg min-h-[400px] max-h-[500px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-soft bg-card">
        <span className="text-xs font-medium text-text-tertiary">Interactive Demo</span>
        <button
          onClick={handleReset}
          className="text-xs text-accent hover:underline"
        >
          Reset Demo
        </button>
      </div>
      <AnimatePresence mode="wait">
        {screen === "empty" && (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <ScanEmptyScreen onStartScan={handleStartScan} />
          </motion.div>
        )}

        {screen === "progress" && (
          <motion.div
            key="progress"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <ScanProgressScreen />
          </motion.div>
        )}

        {screen === "results" && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <ScanResultsScreen
              onSelectFinding={handleSelectFinding}
              selectedFindingId={selectedFinding?.id}
            />
          </motion.div>
        )}

        {screen === "detail" && selectedFinding && (
          <motion.div
            key="detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <FindingDetailPanel
              finding={selectedFinding}
              onDismiss={handleDismiss}
              onSuggestFix={handleSuggestFix}
            />
          </motion.div>
        )}

        {screen === "fixing" && (
          <motion.div
            key="fixing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <SuggestFixScreen onComplete={handleFixComplete} />
          </motion.div>
        )}

        {screen === "patch" && (
          <motion.div
            key="patch"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full"
          >
            <PatchReadyScreen />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
