import { useMemo, useState } from "react";
import { Reorder } from "framer-motion";
import {
  Delete02Icon,
  Folder01Icon,
  Message01Icon,
  MoreHorizontalIcon,
  PencilEdit01Icon,
  SlidersHorizontalIcon,
  SparklesIcon,
  Tick01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Session } from "@/entities/session/model/types";
import { SidebarSessionItem } from "@/entities/session/ui/SidebarSessionItem";

export function SidebarSessionsList({
  sessions,
  sessionOrder,
  activeSessionId,
  onOpenSession,
  onDeleteSession,
  onDeleteAllSessions,
  onReorderSessions,
}: {
  sessions: Session[];
  sessionOrder: string[];
  activeSessionId?: string | null;
  onOpenSession: (session: Session) => void;
  onDeleteSession: (session: Session) => void;
  onDeleteAllSessions: () => void;
  onReorderSessions: (orderedSessionIds: string[]) => void;
}) {
  const [organizeMode, setOrganizeMode] = useState<"repo" | null>(null);
  const [sortMode, setSortMode] = useState<"created" | "updated" | null>(null);
  const [showMode, setShowMode] = useState<"relevant" | null>(null);

  const filteredSessions = useMemo(() => {
    const visibleSessions = showMode === "relevant"
      ? sessions.filter((session) => session.unread || session.findingsCount > 0)
      : sessions;

    const orderedSessions = sessionOrder.length > 0
      ? sessionOrder
        .map((id) => visibleSessions.find((session) => session.id === id) ?? null)
        .filter((session): session is Session => session !== null)
      : visibleSessions;

    const sortedSessions = [...orderedSessions].sort((a, b) => {
      if (sortMode === "created") {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }

      if (sortMode === "updated") {
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      }

      return 0;
    });

    if (organizeMode === "repo") {
      return sortedSessions.sort((a, b) => {
        const repoCompare = a.repo.localeCompare(b.repo);
        return repoCompare !== 0 ? repoCompare : a.title.localeCompare(b.title);
      });
    }

    return sortedSessions;
  }, [organizeMode, sessionOrder, sessions, showMode, sortMode]);

  const canReorder = organizeMode === null && sortMode === null && showMode === null;

  const activeFilterCount = Number(organizeMode !== null) + Number(sortMode !== null) + Number(showMode !== null);

  const menuSections = [
    {
      title: "Organize",
      items: [
        {
          label: "By repository",
          value: "repo" as const,
          selected: organizeMode === "repo",
          icon: Folder01Icon,
          onSelect: () => setOrganizeMode((current) => (current === "repo" ? null : "repo")),
        },
      ],
    },
    {
      title: "Sort by",
      items: [
        {
          label: "Created",
          value: "created" as const,
          selected: sortMode === "created",
          icon: PencilEdit01Icon,
          onSelect: () => setSortMode((current) => (current === "created" ? null : "created")),
        },
        {
          label: "Updated",
          value: "updated" as const,
          selected: sortMode === "updated",
          icon: Message01Icon,
          onSelect: () => setSortMode((current) => (current === "updated" ? null : "updated")),
        },
      ],
    },
    {
      title: "Show",
      items: [
        {
          label: "Relevant only",
          value: "relevant" as const,
          selected: showMode === "relevant",
          icon: SparklesIcon,
          onSelect: () => setShowMode((current) => (current === "relevant" ? null : "relevant")),
        },
      ],
    },
  ];

  return (
    <>
      <div className="flex items-center justify-between px-4 pb-2 pt-3">
        <span className="text-[11px] font-medium uppercase tracking-wider text-txt-tertiary">Sessions</span>
        <div className="flex items-center gap-1.5">
          <Popover>
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <PopoverTrigger asChild>
                  <button
                    className={`relative flex h-7 w-7 items-center justify-center rounded-lg border transition-all ${
                      activeFilterCount > 0
                        ? "bg-secondary text-txt-primary shadow-sm"
                        : "bg-secondary/65 text-txt-tertiary hover:bg-secondary hover:text-txt-primary"
                    }`}
                    style={{ borderColor: "hsl(var(--border-soft))" }}
                    aria-label="Filter, sort, and organize sessions"
                  >
                    <HugeiconsIcon icon={SlidersHorizontalIcon} size={13} strokeWidth={1.7} color="currentColor" />
                    {activeFilterCount > 0 && (
                      <span className="absolute -right-1 -top-1 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-accent px-0.5 text-[9px] font-semibold text-accent-foreground">
                        {activeFilterCount}
                      </span>
                    )}
                  </button>
                </PopoverTrigger>
              </TooltipTrigger>
              <TooltipContent side="top" align="end" sideOffset={8} className="rounded-xl border border-border-soft bg-surface px-3 py-1.5 text-xs text-txt-primary shadow-md">
                Filter sessions
              </TooltipContent>
            </Tooltip>
            <PopoverContent align="end" sideOffset={10} className="w-[216px] rounded-[16px] border border-border-soft bg-surface p-1.5 shadow-[0_16px_36px_rgba(0,0,0,0.1)]">
              <div className="px-1 py-1">
                {menuSections.map((section, sectionIndex) => (
                  <div key={section.title}>
                    {sectionIndex > 0 && <div className="mx-1 my-1 border-t" style={{ borderColor: "hsl(var(--border-soft))" }} />}
                    <div className="px-2 pb-1 pt-1.5 text-[11px] font-medium text-txt-tertiary">{section.title}</div>
                    <div className="space-y-0.5 pb-1">
                      {section.items.map((item) => {
                        return (
                          <button
                            key={item.value}
                            onClick={item.onSelect}
                            className={`flex w-full items-center gap-1.5 rounded-lg px-2 py-1 text-left text-[12px] transition-colors ${
                              item.selected ? "bg-secondary text-txt-primary" : "text-txt-primary hover:bg-secondary/65"
                            }`}
                          >
                            <HugeiconsIcon
                              icon={item.icon}
                              size={12}
                              strokeWidth={1.7}
                              color="currentColor"
                              className="shrink-0 text-txt-secondary"
                            />
                            <span className="min-w-0 flex-1 truncate font-medium">{item.label}</span>
                            {item.selected && (
                              <HugeiconsIcon icon={Tick01Icon} size={12} strokeWidth={1.7} color="currentColor" className="shrink-0 text-txt-primary" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
          <DropdownMenu>
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <button
                    className="flex h-7 w-7 items-center justify-center rounded-lg border bg-secondary/65 text-txt-tertiary transition-all hover:bg-secondary hover:text-txt-primary"
                    style={{ borderColor: "hsl(var(--border-soft))" }}
                    aria-label="Session actions"
                  >
                    <HugeiconsIcon icon={MoreHorizontalIcon} size={13} strokeWidth={1.7} color="currentColor" />
                  </button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              <TooltipContent side="top" align="end" sideOffset={8} className="rounded-xl border border-border-soft bg-surface px-3 py-1.5 text-xs text-txt-primary shadow-md">
                Session actions
              </TooltipContent>
            </Tooltip>
            <DropdownMenuContent align="end" sideOffset={10} className="rounded-xl border border-border-soft bg-surface p-1 text-txt-primary shadow-[0_16px_36px_rgba(0,0,0,0.1)]">
              <DropdownMenuItem
                onClick={onDeleteAllSessions}
                disabled={sessions.length === 0}
                className="rounded-lg text-[12px] text-status-critical focus:bg-[#fff7f5] focus:text-status-critical"
              >
                <HugeiconsIcon icon={Delete02Icon} size={13} strokeWidth={1.7} color="currentColor" className="mr-2" />
                Delete all
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="hide-scrollbar min-h-0 flex-1 overflow-y-auto px-3">
        {canReorder ? (
          <Reorder.Group
            axis="y"
            values={filteredSessions.map((session) => session.id)}
            onReorder={onReorderSessions}
            className="space-y-0.5"
          >
            {filteredSessions.map((session, index) => (
              <Reorder.Item key={session.id} value={session.id} className="rounded-xl">
                <SidebarSessionItem
                  session={session}
                  index={index}
                  isActive={activeSessionId === session.id}
                  onClick={() => onOpenSession(session)}
                  onDelete={() => onDeleteSession(session)}
                />
              </Reorder.Item>
            ))}
          </Reorder.Group>
        ) : (
          <div className="space-y-0.5">
            {filteredSessions.map((session, index) => (
              <div key={session.id} className="rounded-xl">
                <SidebarSessionItem
                  session={session}
                  index={index}
                  isActive={activeSessionId === session.id}
                  onClick={() => onOpenSession(session)}
                  onDelete={() => onDeleteSession(session)}
                />
              </div>
            ))}
          </div>
        )}
        {filteredSessions.length === 0 && (
          <div className="px-3 py-6 text-sm text-txt-tertiary">
            No real review sessions yet
          </div>
        )}
      </div>
    </>
  );
}
