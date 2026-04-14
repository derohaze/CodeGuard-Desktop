import type { BuilderThreadDto, BuilderWorkspaceDto } from "../builderApi";
import type { BuilderMessage, BuilderThreadGroup } from "../mockBuilderAgent";

export function formatRelativeTime(isoValue: string): string {
  const parsed = new Date(isoValue);
  if (Number.isNaN(parsed.getTime())) {
    return "now";
  }
  const diffMs = Date.now() - parsed.getTime();
  if (diffMs <= 60_000) return "now";
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d`;
  const months = Math.floor(days / 30);
  return `${Math.max(months, 1)}mo`;
}

export function mapMessage(message: BuilderThreadDto["messages"][number]): BuilderMessage {
  return {
    id: message.id,
    role: message.role,
    text: message.text,
    isStreaming: false,
  };
}

export function mapWorkspace(workspace: BuilderWorkspaceDto): BuilderThreadGroup {
  return {
    id: workspace.id,
    label: workspace.label,
    path: workspace.path,
    threads: workspace.threads.map((thread) => ({
      id: thread.id,
      title: thread.title,
      updatedAt: formatRelativeTime(thread.updatedAt),
    })),
  };
}
