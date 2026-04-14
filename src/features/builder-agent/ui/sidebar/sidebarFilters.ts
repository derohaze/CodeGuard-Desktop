import type { Dispatch, SetStateAction } from "react";
import { Clock3, FolderOpen, MessageSquareMore, PenSquare, SquarePen } from "lucide-react";

export function buildFilterSections({
  organizeMode,
  setOrganizeMode,
  showMode,
  setShowMode,
  sortBy,
  setSortBy,
}: {
  organizeMode: "workspace" | "time" | null;
  setOrganizeMode: Dispatch<SetStateAction<"workspace" | "time" | null>>;
  showMode: "all" | "relevant" | null;
  setShowMode: Dispatch<SetStateAction<"all" | "relevant" | null>>;
  sortBy: "created" | "updated" | null;
  setSortBy: Dispatch<SetStateAction<"created" | "updated" | null>>;
}) {
  return [
    {
      title: "Organize",
      items: [
        {
          label: "By workspace",
          selected: organizeMode === "workspace",
          icon: FolderOpen,
          onSelect: () => setOrganizeMode((current) => (current === "workspace" ? null : "workspace")),
        },
        {
          label: "Chronological list",
          selected: organizeMode === "time",
          icon: Clock3,
          onSelect: () => setOrganizeMode((current) => (current === "time" ? null : "time")),
        },
      ],
    },
    {
      title: "Sort by",
      items: [
        {
          label: "Created",
          selected: sortBy === "created",
          icon: SquarePen,
          onSelect: () => setSortBy((current) => (current === "created" ? null : "created")),
        },
        {
          label: "Updated",
          selected: sortBy === "updated",
          icon: MessageSquareMore,
          onSelect: () => setSortBy((current) => (current === "updated" ? null : "updated")),
        },
      ],
    },
    {
      title: "Show",
      items: [
        {
          label: "All chats",
          selected: showMode === "all",
          icon: FolderOpen,
          onSelect: () => setShowMode((current) => (current === "all" ? null : "all")),
        },
        {
          label: "Relevant",
          selected: showMode === "relevant",
          icon: PenSquare,
          onSelect: () => setShowMode((current) => (current === "relevant" ? null : "relevant")),
        },
      ],
    },
  ];
}
