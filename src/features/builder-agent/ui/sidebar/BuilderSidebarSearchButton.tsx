import { motion } from "framer-motion";
import { Search } from "lucide-react";

export function BuilderSidebarSearchButton({ onOpen }: { onOpen: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1], delay: 0.04 }}
      className="px-3 py-2"
    >
      <motion.button
        onClick={onOpen}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1], delay: 0.07 }}
        className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm text-txt-primary transition-colors hover:bg-muted"
      >
        <Search size={16} className="text-txt-secondary" />
        <span>Search</span>
      </motion.button>
    </motion.div>
  );
}
