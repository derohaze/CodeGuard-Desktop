import { Shield01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import type { AppScreen } from "@/shared/types/app";

export function SidebarActions({
  currentScreen,
  onNavigate,
}: {
  currentScreen: AppScreen;
  onNavigate: (screen: AppScreen) => void;
}) {
  const isScanActive = currentScreen === "home" || currentScreen === "scan-empty";

  return (
    <div className="space-y-0.5 px-3 py-2">
      <button
        onClick={() => onNavigate("home")}
        className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-[12.5px] transition-colors ${
          isScanActive ? "bg-muted font-medium text-txt-primary" : "text-txt-primary hover:bg-muted"
        }`}
      >
        <HugeiconsIcon icon={Shield01Icon} size={14} strokeWidth={1.7} color="currentColor" className="text-txt-secondary" />
        <span>Code Review</span>
      </button>
    </div>
  );
}
