import { AnimatePresence, motion } from "framer-motion";
import type { WorkspaceMode } from "@/shared/types/app";
import { DecryptedText } from "./DecryptedText";

const MODE_LABELS: Record<WorkspaceMode, string> = {
  security: "Security",
  builder: "Builder",
};

export function BrandModeHeading({ mode }: { mode: WorkspaceMode }) {
  const modeLabel = MODE_LABELS[mode];

  return (
    <h1 className="inline-flex items-baseline whitespace-nowrap font-brand text-[22px] font-normal tracking-[-0.01em] text-txt-primary">
      <span>Khwarizm</span>
      <span className="inline-grid min-w-[8ch] pl-2 text-left" aria-live="polite">
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={modeLabel}
            initial={{ opacity: 0, filter: "blur(3px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, filter: "blur(2px)" }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className="col-start-1 row-start-1 inline-block"
          >
            <DecryptedText
              text={modeLabel}
              speed={38}
              characters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#*@%&!+=?/~$<>[]{}^"
              className="text-txt-primary"
              encryptedClassName="text-[#9f9587]"
            />
          </motion.span>
        </AnimatePresence>
      </span>
    </h1>
  );
}
