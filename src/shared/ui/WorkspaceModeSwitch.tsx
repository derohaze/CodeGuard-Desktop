import { motion } from "framer-motion";
import { Shield, Code2 } from "lucide-react";
import type { WorkspaceMode } from "@/shared/types/app";

interface WorkspaceModeSwitchProps {
  mode: WorkspaceMode;
  onChange: (mode: WorkspaceMode) => void;
}

export function WorkspaceModeSwitch({ mode, onChange }: WorkspaceModeSwitchProps) {
  const options = [
    { id: "security" as const, label: "Security", icon: Shield },
    { id: "builder" as const, label: "Builder", icon: Code2 },
  ];

  return (
    <div
      className="inline-flex rounded-[18px] border bg-[#ebe6d8] p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.6)]"
      style={{ borderColor: "hsl(var(--border-soft))" }}
      aria-label="Switch workspace mode"
    >
      {options.map((option) => {
        const Icon = option.icon;
        const active = mode === option.id;

        return (
          <button
            key={option.id}
            onClick={() => onChange(option.id)}
            className={`relative inline-flex h-9 min-w-[56px] items-center justify-center rounded-[14px] px-3 transition-colors ${
              active ? "text-txt-primary" : "text-txt-secondary hover:text-txt-primary"
            }`}
            aria-pressed={active}
            aria-label={option.label}
          >
            {active && (
              <motion.span
                layoutId="workspace-mode-thumb"
                className="absolute inset-0 rounded-[14px] bg-white shadow-[0_4px_12px_rgba(52,42,28,0.12)]"
                transition={{ type: "spring", stiffness: 560, damping: 42, mass: 0.68 }}
              />
            )}
            <motion.span
              animate={{ scale: active ? 1 : 0.96, opacity: active ? 1 : 0.82 }}
              transition={{ duration: 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="relative z-10 inline-flex items-center justify-center"
            >
            <Icon size={16} strokeWidth={2.1} />
            </motion.span>
          </button>
        );
      })}
    </div>
  );
}
