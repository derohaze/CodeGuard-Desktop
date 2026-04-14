import { PanelLeftClose } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { WorkspaceModeSwitch } from "@/shared/ui/WorkspaceModeSwitch";
import type { WorkspaceMode } from "@/shared/types/app";
import { BrandModeHeading } from "@/shared/ui/BrandModeHeading";

export function SidebarHeader({
  mode,
  onModeChange,
  onToggleCollapse,
}: {
  mode: WorkspaceMode;
  onModeChange: (mode: WorkspaceMode) => void;
  onToggleCollapse: () => void;
}) {
  return (
    <div className="px-5 pb-2 pt-5">
      <div className="relative">
        <div className="space-y-3 pr-8">
          <div className="flex items-center gap-2.5">
            <BrandModeHeading mode={mode} />
          </div>
          <WorkspaceModeSwitch mode={mode} onChange={onModeChange} />
        </div>
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>
            <button
              onClick={onToggleCollapse}
              className="absolute right-0 top-0 p-1 text-txt-secondary transition-colors hover:text-txt-primary"
              aria-label="Hide sidebar"
            >
              <PanelLeftClose size={17} />
            </button>
          </TooltipTrigger>
          <TooltipContent
            side="bottom"
            align="end"
            sideOffset={8}
            className="rounded-xl border border-border-soft bg-surface px-3 py-1.5 text-xs text-txt-primary shadow-md"
          >
            Hide sidebar
          </TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}
