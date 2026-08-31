import { Settings02Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

export function SidebarFooter({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <div className="px-3 pb-4 pt-2">
      <button
        type="button"
        onClick={onOpenSettings}
        className="flex h-7 w-full items-center gap-1.5 rounded-lg px-2 text-left text-[12px] font-medium text-txt-secondary transition-colors hover:bg-muted hover:text-txt-primary"
        aria-label="Open settings"
      >
        <HugeiconsIcon
          icon={Settings02Icon}
          size={13}
          strokeWidth={1.7}
          color="currentColor"
          aria-hidden="true"
          focusable="false"
        />
        <span className="truncate">Settings</span>
      </button>
    </div>
  );
}
