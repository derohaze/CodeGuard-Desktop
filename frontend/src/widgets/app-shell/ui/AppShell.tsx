import { motion } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";
import { WindowTitleBar } from "./WindowTitleBar";

interface AppShellProps {
  children: ReactNode;
  onToggleSidebar?: () => void;
  isSidebarCollapsed?: boolean;
  onNavigateHome?: () => void;
  onOpenSettings?: () => void;
}

export function AppShell({ children, onToggleSidebar, isSidebarCollapsed, onNavigateHome, onOpenSettings }: AppShellProps) {
  const hasElectronTitlebar = typeof window !== "undefined" && typeof window.electronAPI?.versions?.electron === "string";
  const controls = typeof window !== "undefined" ? window.electronAPI?.windowControls : undefined;
  const [maximized, setMaximized] = useState(false);

  useEffect(() => {
    if (!controls) return;
    let cancelled = false;
    void controls.isMaximized().then((value) => {
      if (!cancelled) setMaximized(value);
    });
    const unsubscribe = controls.onStateChanged(({ maximized: value }) => {
      setMaximized(value);
    });
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [controls]);

  return (
    <div
      className={`flex h-screen w-screen overflow-hidden p-0 ${hasElectronTitlebar ? (maximized ? "rounded-none" : "rounded-[12px] border border-white/[0.07] shadow-[0_16px_64px_rgba(0,0,0,0.55)]") : ""}`}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className={`relative flex h-full min-h-0 w-full min-w-0 max-w-none flex-col overflow-hidden bg-[#1a1a1a] ${hasElectronTitlebar && !maximized ? "rounded-[12px] border border-white/[0.05] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]" : ""}`}
      >
        <WindowTitleBar
          controls={controls}
          onToggleSidebar={onToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
          onNavigateHome={onNavigateHome}
          onOpenSettings={onOpenSettings}
        />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
      </motion.div>
    </div>
  );
}