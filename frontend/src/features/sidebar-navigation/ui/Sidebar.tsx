import { motion } from "framer-motion";
import type { CSSProperties } from "react";
import type { Session } from "@/entities/session/model/types";
import type { AppScreen } from "@/shared/types/app";
import { SidebarActions } from "./SidebarActions";
import { SidebarFooter } from "./SidebarFooter";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarSessionsList } from "./SidebarSessionsList";

interface SidebarProps {
  sessions: Session[];
  sessionOrder: string[];
  currentScreen: AppScreen;
  onNavigate: (screen: AppScreen) => void;
  activeSessionId?: string | null;
  onOpenSession: (session: Session) => void;
  onDeleteSession: (session: Session) => void;
  onDeleteAllSessions: () => void;
  onReorderSessions: (orderedSessionIds: string[]) => void;
  isCollapsed: boolean;
  onOpenSettings: () => void;
}

export function Sidebar({
  sessions,
  sessionOrder,
  currentScreen,
  onNavigate,
  activeSessionId,
  onOpenSession,
  onDeleteSession,
  onDeleteAllSessions,
  onReorderSessions,
  isCollapsed,
  onOpenSettings,
}: SidebarProps) {
  return (
    <div
      className="relative h-full shrink-0 overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]"
      style={{ width: isCollapsed ? 0 : 300 }}
      aria-hidden={isCollapsed}
    >
      <motion.aside
        className="absolute inset-y-0 left-0 flex w-[300px] min-h-0 flex-col overflow-hidden bg-[#1a1a1a]"
        style={
          {
            "--text-primary": "0 0% 92%",
            "--text-secondary": "0 0% 68%",
            "--text-tertiary": "0 0% 52%",
            "--text-placeholder": "0 0% 45%",
            "--border-soft": "0 0% 24%",
            "--border-primary": "0 0% 28%",
            "--muted": "0 0% 21%",
            "--secondary": "0 0% 21%",
            "--card": "0 0% 20%",
            "--surface": "0 0% 16%",
            "--surface-secondary": "0 0% 18%",
            "--surface-sidebar": "0 0% 10%",
          } as CSSProperties
        }
        initial={false}
        animate={{
          x: isCollapsed ? -300 : 0,
          opacity: isCollapsed ? 0 : 1,
        }}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      >
        <SidebarHeader />
        <SidebarActions currentScreen={currentScreen} onNavigate={onNavigate} />
        <SidebarSessionsList
          sessions={sessions}
          sessionOrder={sessionOrder}
          activeSessionId={activeSessionId}
          onOpenSession={onOpenSession}
          onDeleteSession={onDeleteSession}
          onDeleteAllSessions={onDeleteAllSessions}
          onReorderSessions={onReorderSessions}
        />
        <SidebarFooter onOpenSettings={onOpenSettings} />
      </motion.aside>
    </div>
  );
}
