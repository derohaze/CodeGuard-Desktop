import { builderPromptSuggestions } from "../mockBuilderAgent";
import { type PermissionMode, type ResponseSpeed } from "../lib/types";
import { useBuilderComposerSettings } from "./useBuilderComposerSettings";
import { useBuilderMessageSending } from "./useBuilderMessageSending";
import { useBuilderWorkspaceState } from "./useBuilderWorkspaceState";

export function useBuilderAgent() {
  const workspaceState = useBuilderWorkspaceState();
  const { composerSettings, persistComposerSettings } = useBuilderComposerSettings();
  const { isStreaming, sendMessage, stopStreaming } = useBuilderMessageSending({
    activeConversationId: workspaceState.activeConversationId,
    composerSettings,
    currentWorkspace: workspaceState.currentWorkspace,
    currentWorkspaceId: workspaceState.currentWorkspaceId,
    draft: workspaceState.draft,
    refreshWorkspaces: workspaceState.refreshWorkspaces,
    setActiveConversationId: workspaceState.setActiveConversationId,
    setCurrentWorkspaceId: workspaceState.setCurrentWorkspaceId,
    setDraft: workspaceState.setDraft,
    setMessageMap: workspaceState.setMessageMap,
  });

  const addAttachment = () => {
    void (async () => {
      const canBrowse = typeof window !== "undefined" && typeof window.electronAPI?.pickPath === "function";
      const picked = canBrowse ? await window.electronAPI?.pickPath?.("file") : window.prompt("File path")?.trim() ?? null;
      if (!picked) return;
      const normalizedPath = picked.trim();
      if (!normalizedPath) return;

      const nextFiles = composerSettings.attachedFiles.includes(normalizedPath)
        ? composerSettings.attachedFiles
        : [...composerSettings.attachedFiles, normalizedPath];
      persistComposerSettings({
        ...composerSettings,
        attachedFiles: nextFiles,
      });
    })();
  };

  const removeAttachment = (filePath: string) => {
    persistComposerSettings({
      ...composerSettings,
      attachedFiles: composerSettings.attachedFiles.filter((item) => item !== filePath),
    });
  };

  const setPermissionMode = (permissionMode: PermissionMode) => {
    persistComposerSettings({
      ...composerSettings,
      permissionMode,
    });
  };

  const setPlanMode = (planMode: boolean) => {
    persistComposerSettings({
      ...composerSettings,
      planMode,
    });
  };

  const setResponseSpeed = (responseSpeed: ResponseSpeed) => {
    persistComposerSettings({
      ...composerSettings,
      responseSpeed,
    });
  };

  return {
    activeConversation: workspaceState.activeConversation,
    activeConversationId: workspaceState.activeConversationId,
    currentWorkspace: workspaceState.currentWorkspace,
    draft: workspaceState.draft,
    expandedWorkspaceIds: workspaceState.expandedWorkspaceIds,
    isStreaming,
    messages: workspaceState.messages,
    composerSettings,
    promptSuggestions: builderPromptSuggestions,
    showAllWorkspaceIds: workspaceState.showAllWorkspaceIds,
    sortMode: workspaceState.sortMode,
    threadGroups: workspaceState.sortedThreadGroups,
    addAttachment,
    addWorkspace: workspaceState.addWorkspace,
    archiveWorkspaceThreads: workspaceState.archiveWorkspaceThreads,
    archiveThread: workspaceState.archiveThread,
    collapseAllWorkspaces: workspaceState.collapseAllWorkspaces,
    createPermanentWorktree: workspaceState.createPermanentWorktree,
    createWorkspaceThread: workspaceState.createWorkspaceThread,
    expandAllWorkspaces: workspaceState.expandAllWorkspaces,
    hasPreviousConversation: workspaceState.hasPreviousConversation,
    openConversation: workspaceState.openConversation,
    openWorkspaceInExplorer: workspaceState.openWorkspaceInExplorer,
    removeWorkspace: workspaceState.removeWorkspace,
    removeThread: workspaceState.removeThread,
    reorderWorkspaces: workspaceState.reorderWorkspaces,
    renameWorkspace: workspaceState.renameWorkspace,
    renameThread: workspaceState.renameThread,
    reopenPreviousConversation: workspaceState.reopenPreviousConversation,
    removeAttachment,
    sendMessage,
    stopStreaming,
    setPermissionMode,
    setPlanMode,
    setResponseSpeed,
    setDraft: workspaceState.setDraft,
    startNewChat: workspaceState.startNewChat,
    toggleSortMode: workspaceState.toggleSortMode,
    toggleWorkspace: workspaceState.toggleWorkspace,
    toggleWorkspaceShowAll: workspaceState.toggleWorkspaceShowAll,
  };
}
