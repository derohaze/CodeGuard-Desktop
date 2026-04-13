import { useEffect, useMemo, useRef, useState } from "react";
import {
  builderConversations,
  builderMessages,
  builderPromptSuggestions,
  builderThreadGroups,
  type BuilderConversation,
  type BuilderMessage,
  type BuilderThreadGroup,
} from "./mockBuilderAgent";
import { createMockBuilderStreamPlan } from "./mockBuilderResponder";

const BUILDER_WORKSPACES_KEY = "builder-workspaces";
const BUILDER_CONVERSATIONS_KEY = "builder-conversations";
const BUILDER_MESSAGES_KEY = "builder-messages";
const BUILDER_COMPOSER_SETTINGS_KEY = "builder-composer-settings";

type PermissionMode = "default" | "full-access";
type ResponseSpeed = "normal" | "speed";

interface BuilderComposerSettings {
  permissionMode: PermissionMode;
  planMode: boolean;
  responseSpeed: ResponseSpeed;
  attachedFiles: string[];
}

function formatRelativeNow() {
  return "now";
}

function basenameFromPath(path: string) {
  if (!path) return "workspace";
  const normalized = path.replace(/\\/g, "/");
  const parts = normalized.split("/").filter(Boolean);
  return parts[parts.length - 1] || normalized;
}

function loadStoredWorkspaces() {
  if (typeof window === "undefined") return builderThreadGroups;

  try {
    const stored = window.localStorage.getItem(BUILDER_WORKSPACES_KEY);
    if (!stored) return builderThreadGroups;
    const parsed = JSON.parse(stored) as BuilderThreadGroup[];
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : builderThreadGroups;
  } catch {
    return builderThreadGroups;
  }
}

function loadStoredConversations() {
  if (typeof window === "undefined") return builderConversations;

  try {
    const stored = window.localStorage.getItem(BUILDER_CONVERSATIONS_KEY);
    if (!stored) return builderConversations;
    const parsed = JSON.parse(stored) as BuilderConversation[];
    return Array.isArray(parsed) ? parsed : builderConversations;
  } catch {
    return builderConversations;
  }
}

function loadStoredMessages() {
  if (typeof window === "undefined") return builderMessages;

  try {
    const stored = window.localStorage.getItem(BUILDER_MESSAGES_KEY);
    if (!stored) return builderMessages;
    const parsed = JSON.parse(stored) as Record<string, BuilderMessage[]>;
    return parsed && typeof parsed === "object" ? parsed : builderMessages;
  } catch {
    return builderMessages;
  }
}

function loadComposerSettings(): BuilderComposerSettings {
  if (typeof window === "undefined") {
    return {
      permissionMode: "full-access",
      planMode: false,
      responseSpeed: "normal",
      attachedFiles: [],
    };
  }

  try {
    const stored = window.localStorage.getItem(BUILDER_COMPOSER_SETTINGS_KEY);
    if (!stored) {
      return {
        permissionMode: "full-access",
        planMode: false,
        responseSpeed: "normal",
        attachedFiles: [],
      };
    }
    const parsed = JSON.parse(stored) as Partial<BuilderComposerSettings>;
    return {
      permissionMode: parsed.permissionMode === "default" ? "default" : "full-access",
      planMode: Boolean(parsed.planMode),
      responseSpeed: parsed.responseSpeed === "speed" ? "speed" : "normal",
      attachedFiles: Array.isArray(parsed.attachedFiles) ? parsed.attachedFiles : [],
    };
  } catch {
    return {
      permissionMode: "full-access",
      planMode: false,
      responseSpeed: "normal",
      attachedFiles: [],
    };
  }
}

function getTypedReasoningLines(step: [string, string, string], charsVisible: number) {
  let remaining = charsVisible;

  return step.map((line) => {
    if (remaining <= 0) return "";
    const nextLine = line.slice(0, remaining);
    remaining -= line.length;
    return nextLine;
  });
}

function getReasoningStepLength(step: [string, string, string]) {
  return step[0].length + step[1].length + step[2].length;
}

export function useBuilderAgent() {
  const [threadGroups, setThreadGroups] = useState<BuilderThreadGroup[]>(() => loadStoredWorkspaces());
  const [conversations, setConversations] = useState<BuilderConversation[]>(() => loadStoredConversations());
  const [messageMap, setMessageMap] = useState<Record<string, BuilderMessage[]>>(() => loadStoredMessages());
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(() => loadStoredWorkspaces()[0]?.id ?? null);
  const [previousConversationId, setPreviousConversationId] = useState<string | null>(null);
  const [expandedWorkspaceIds, setExpandedWorkspaceIds] = useState<string[]>(() => loadStoredWorkspaces().map((group) => group.id));
  const [showAllWorkspaceIds, setShowAllWorkspaceIds] = useState<string[]>([]);
  const [sortMode, setSortMode] = useState<"recent" | "alphabetical">("recent");
  const [composerSettings, setComposerSettings] = useState<BuilderComposerSettings>(() => loadComposerSettings());
  const streamTimerRef = useRef<number | null>(null);

  const persistWorkspaces = (nextWorkspaces: BuilderThreadGroup[]) => {
    setThreadGroups(nextWorkspaces);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(BUILDER_WORKSPACES_KEY, JSON.stringify(nextWorkspaces));
    }
  };

  const persistConversations = (nextConversations: BuilderConversation[]) => {
    setConversations(nextConversations);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(BUILDER_CONVERSATIONS_KEY, JSON.stringify(nextConversations));
    }
  };

  const persistMessages = (nextMessages: Record<string, BuilderMessage[]>) => {
    setMessageMap(nextMessages);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(BUILDER_MESSAGES_KEY, JSON.stringify(nextMessages));
    }
  };

  const persistComposerSettings = (nextSettings: BuilderComposerSettings) => {
    setComposerSettings(nextSettings);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(BUILDER_COMPOSER_SETTINGS_KEY, JSON.stringify(nextSettings));
    }
  };

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) {
        window.clearInterval(streamTimerRef.current);
      }
    };
  }, []);

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeConversationId) ?? null,
    [activeConversationId, conversations],
  );

  const currentWorkspace = useMemo(
    () =>
      threadGroups.find((group) => group.id === (activeConversation?.groupId ?? currentWorkspaceId)) ??
      threadGroups[0] ??
      null,
    [activeConversation?.groupId, currentWorkspaceId, threadGroups],
  );

  const sortedThreadGroups = useMemo(() => {
    const normalize = (value: string) => value.toLowerCase();
    return threadGroups.map((group) => ({
      ...group,
      threads:
        sortMode === "alphabetical"
          ? [...group.threads].sort((a, b) => normalize(a.title).localeCompare(normalize(b.title)))
          : group.threads,
    }));
  }, [sortMode, threadGroups]);

  const messages = activeConversationId ? messageMap[activeConversationId] ?? [] : [];
  const isStreaming = messages.some((message) => message.isStreaming);

  const stopActiveStream = () => {
    if (streamTimerRef.current) {
      window.clearInterval(streamTimerRef.current);
      streamTimerRef.current = null;
    }

    const latest = loadStoredMessages();
    const nextMessages = Object.fromEntries(
      Object.entries(latest).map(([conversationId, conversationMessages]) => [
        conversationId,
        conversationMessages.filter((message) => !(message.isStreaming && !message.text.trim())).map((message) =>
          message.isStreaming
            ? {
                ...message,
                reasoningLines: [],
                isStreaming: false,
              }
            : message,
        ),
      ]),
    ) as Record<string, BuilderMessage[]>;

    persistMessages(nextMessages);
  };

  const stopStreaming = () => {
    stopActiveStream();
  };

  const openConversation = (conversationId: string) => {
    if (activeConversationId && activeConversationId !== conversationId) {
      setPreviousConversationId(activeConversationId);
    }

    const conversation = conversations.find((item) => item.id === conversationId);
    setActiveConversationId(conversationId);
    if (conversation) {
      setCurrentWorkspaceId(conversation.groupId);
      setExpandedWorkspaceIds((current) =>
        current.includes(conversation.groupId) ? current : [...current, conversation.groupId],
      );
    }
  };

  const startNewChat = (workspaceId?: string) => {
    if (activeConversationId) {
      setPreviousConversationId(activeConversationId);
    }

    const targetWorkspaceId = workspaceId ?? currentWorkspace?.id ?? threadGroups[0]?.id ?? null;
    if (targetWorkspaceId) {
      setCurrentWorkspaceId(targetWorkspaceId);
      setExpandedWorkspaceIds((current) =>
        current.includes(targetWorkspaceId) ? current : [...current, targetWorkspaceId],
      );
    }

    setActiveConversationId(null);
    setDraft("");
  };

  const toggleWorkspace = (workspaceId: string) => {
    setExpandedWorkspaceIds((current) =>
      current.includes(workspaceId) ? current.filter((id) => id !== workspaceId) : [...current, workspaceId],
    );
  };

  const toggleWorkspaceShowAll = (workspaceId: string) => {
    setShowAllWorkspaceIds((current) =>
      current.includes(workspaceId) ? current.filter((id) => id !== workspaceId) : [...current, workspaceId],
    );
  };

  const collapseAllWorkspaces = () => setExpandedWorkspaceIds([]);
  const expandAllWorkspaces = () => setExpandedWorkspaceIds(threadGroups.map((group) => group.id));

  const reopenPreviousConversation = () => {
    if (!previousConversationId) return;
    openConversation(previousConversationId);
  };

  const toggleSortMode = () => {
    setSortMode((current) => (current === "recent" ? "alphabetical" : "recent"));
  };

  const addWorkspace = () => {
    void (async () => {
      const canBrowse = typeof window !== "undefined" && typeof window.electronAPI?.pickPath === "function";
      const picked = canBrowse ? await window.electronAPI?.pickPath?.("folder") : window.prompt("Project folder path")?.trim() ?? null;
      if (!picked) return;

      const normalizedPath = picked.trim();
      const existing = threadGroups.find((group) => group.path === normalizedPath);
      if (existing) {
        setCurrentWorkspaceId(existing.id);
        setExpandedWorkspaceIds((current) => (current.includes(existing.id) ? current : [...current, existing.id]));
        setActiveConversationId(null);
        return;
      }

      const nextId = `workspace-${Date.now()}`;
      const nextWorkspace: BuilderThreadGroup = {
        id: nextId,
        label: basenameFromPath(normalizedPath),
        path: normalizedPath,
        threads: [],
      };

      persistWorkspaces([...threadGroups, nextWorkspace]);
      setExpandedWorkspaceIds((current) => [...current, nextId]);
      setCurrentWorkspaceId(nextId);
      setActiveConversationId(null);
      setDraft("");
    })();
  };

  const renameWorkspace = (workspaceId: string) => {
    const workspace = threadGroups.find((group) => group.id === workspaceId);
    if (!workspace) return;

    const nextLabel = window.prompt("Rename workspace", workspace.label)?.trim();
    if (!nextLabel) return;

    persistWorkspaces(
      threadGroups.map((group) => (group.id === workspaceId ? { ...group, label: nextLabel } : group)),
    );
    persistConversations(
      conversations.map((conversation) =>
        conversation.groupId === workspaceId ? { ...conversation, subtitle: nextLabel } : conversation,
      ),
    );
  };

  const archiveWorkspaceThreads = (workspaceId: string) => {
    persistWorkspaces(threadGroups.map((group) => (group.id === workspaceId ? { ...group, threads: [] } : group)));
    persistConversations(conversations.filter((conversation) => conversation.groupId !== workspaceId));

    const nextMessageMap = { ...messageMap };
    for (const conversation of conversations) {
      if (conversation.groupId === workspaceId) {
        delete nextMessageMap[conversation.id];
      }
    }
    persistMessages(nextMessageMap);

    if (activeConversation?.groupId === workspaceId) {
      setActiveConversationId(null);
      setDraft("");
    }
  };

  const removeWorkspace = (workspaceId: string) => {
    const fallbackWorkspace = threadGroups.find((group) => group.id !== workspaceId) ?? null;

    persistWorkspaces(threadGroups.filter((group) => group.id !== workspaceId));
    persistConversations(conversations.filter((conversation) => conversation.groupId !== workspaceId));
    const nextMessageMap = { ...messageMap };
    for (const conversation of conversations) {
      if (conversation.groupId === workspaceId) {
        delete nextMessageMap[conversation.id];
      }
    }
    persistMessages(nextMessageMap);
    setExpandedWorkspaceIds((current) => current.filter((id) => id !== workspaceId));
    setShowAllWorkspaceIds((current) => current.filter((id) => id !== workspaceId));

    if (currentWorkspaceId === workspaceId) {
      setCurrentWorkspaceId(fallbackWorkspace?.id ?? null);
    }

    if (activeConversation?.groupId === workspaceId) {
      setActiveConversationId(null);
      setDraft("");
    }
  };

  const openWorkspaceInExplorer = (workspaceId: string) => {
    const workspace = threadGroups.find((group) => group.id === workspaceId);
    if (!workspace) return;

    if (typeof window === "undefined") return;

    const normalized = workspace.path.replace(/\\/g, "/");
    const fileUrl = normalized.startsWith("/") ? `file://${normalized}` : `file:///${normalized}`;

    try {
      window.open(fileUrl, "_blank", "noopener,noreferrer");
    } catch {
      if (navigator.clipboard) {
        void navigator.clipboard.writeText(workspace.path);
      }
    }
  };

  const createPermanentWorktree = (workspaceId: string) => {
    const workspace = threadGroups.find((group) => group.id === workspaceId);
    if (!workspace) return;
  };

  const createWorkspaceThread = (workspaceId: string) => {
    startNewChat(workspaceId);
  };

  const reorderWorkspaces = (orderedWorkspaceIds: string[]) => {
    const nextGroups = orderedWorkspaceIds
      .map((workspaceId) => threadGroups.find((group) => group.id === workspaceId) ?? null)
      .filter((group): group is BuilderThreadGroup => group !== null);

    if (nextGroups.length !== threadGroups.length) return;
    persistWorkspaces(nextGroups);
  };

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

  const renameThread = (threadId: string) => {
    const thread = conversations.find((conversation) => conversation.id === threadId);
    if (!thread) return;

    const nextTitle = window.prompt("Rename chat", thread.title)?.trim();
    if (!nextTitle) return;

    persistConversations(
      conversations.map((conversation) => (conversation.id === threadId ? { ...conversation, title: nextTitle } : conversation)),
    );
    persistWorkspaces(
      threadGroups.map((group) =>
        group.id === thread.groupId
          ? {
              ...group,
              threads: group.threads.map((item) => (item.id === threadId ? { ...item, title: nextTitle } : item)),
            }
          : group,
      ),
    );
  };

  const removeThread = (threadId: string) => {
    const thread = conversations.find((conversation) => conversation.id === threadId);
    if (!thread) return;

    persistConversations(conversations.filter((conversation) => conversation.id !== threadId));
    persistWorkspaces(
      threadGroups.map((group) =>
        group.id === thread.groupId
          ? {
              ...group,
              threads: group.threads.filter((item) => item.id !== threadId),
            }
          : group,
      ),
    );
    const nextMessageMap = { ...messageMap };
    delete nextMessageMap[threadId];
    persistMessages(nextMessageMap);

    if (activeConversationId === threadId) {
      setActiveConversationId(null);
      setDraft("");
    }
  };

  const archiveThread = (threadId: string) => {
    removeThread(threadId);
  };

  const startStreamingReply = (conversationId: string, prompt: string) => {
    stopActiveStream();

    const plan = createMockBuilderStreamPlan(prompt);
    const assistantId = `assistant-${Date.now()}`;
    let phase: "reasoning" | "response" = "reasoning";
    let reasoningIndex = 0;
    let reasoningCharsVisible = 0;
    let reasoningHoldTicks = 0;
    let responseCharIndex = 0;

    const latestMessages = loadStoredMessages();
    const seededMessages = {
      ...latestMessages,
      [conversationId]: [
        ...(latestMessages[conversationId] ?? []),
        {
          id: assistantId,
          role: "assistant",
          text: "",
          reasoningLines: [],
          isStreaming: true,
        },
      ],
    };
    persistMessages(seededMessages);

    streamTimerRef.current = window.setInterval(() => {
      const latest = loadStoredMessages();

      if (phase === "reasoning") {
        const currentStep = plan.reasoning[reasoningIndex];
        if (!currentStep) {
          phase = "response";
          return;
        }

        const stepLength = getReasoningStepLength(currentStep);
        const isStepComplete = reasoningCharsVisible >= stepLength;

        if (!isStepComplete) {
          reasoningCharsVisible += 3;
        } else {
          reasoningHoldTicks += 1;
        }

        const visibleReasoning = getTypedReasoningLines(currentStep, reasoningCharsVisible);

        persistMessages({
          ...latest,
          [conversationId]: (latest[conversationId] ?? []).map((message) =>
            message.id === assistantId
              ? {
                  ...message,
                  reasoningLines: visibleReasoning,
                  isStreaming: true,
                }
              : message,
          ),
        });

        if (isStepComplete && reasoningHoldTicks >= 14) {
          reasoningIndex += 1;
          reasoningCharsVisible = 0;
          reasoningHoldTicks = 0;
        }

        if (reasoningIndex >= plan.reasoning.length) {
          phase = "response";
        }
        return;
      }

      responseCharIndex += 4;
      const nextText = plan.response.slice(0, responseCharIndex);
      const completed = responseCharIndex >= plan.response.length;

      persistMessages({
        ...latest,
        [conversationId]: (latest[conversationId] ?? []).map((message) => {
          if (message.id !== assistantId) return message;
          return {
            ...message,
            reasoningLines: [],
            text: nextText,
            isStreaming: !completed,
          };
        }),
      });

      if (completed && streamTimerRef.current) {
        window.clearInterval(streamTimerRef.current);
        streamTimerRef.current = null;
      }
    }, 22);
  };

  const sendMessage = () => {
    const prompt = draft.trim();
    if (!prompt || !currentWorkspace) return;

    let conversationId = activeConversationId;

    if (!conversationId) {
      conversationId = `thread-${Date.now()}`;
      const updatedAt = formatRelativeNow();
      const nextConversation: BuilderConversation = {
        id: conversationId,
        title: prompt,
        subtitle: currentWorkspace.label,
        groupId: currentWorkspace.id,
        updatedAt,
      };

      persistConversations([nextConversation, ...conversations]);
      persistWorkspaces(
        threadGroups.map((group) =>
          group.id === currentWorkspace.id
            ? {
                ...group,
                threads: [{ id: conversationId!, title: prompt, updatedAt }, ...group.threads],
              }
            : group,
        ),
      );
      setActiveConversationId(conversationId);
    } else {
      persistWorkspaces(
        threadGroups.map((group) =>
          group.id === currentWorkspace.id
            ? {
                ...group,
                threads: group.threads.map((thread) =>
                  thread.id === conversationId ? { ...thread, updatedAt: formatRelativeNow() } : thread,
                ),
              }
            : group,
        ),
      );
    }

    const latestMessages = loadStoredMessages();
    const nextMessages = {
      ...latestMessages,
      [conversationId]: [
        ...(latestMessages[conversationId] ?? []),
        {
          id: `user-${Date.now()}`,
          role: "user",
          text: prompt,
        },
      ],
    };
    persistMessages(nextMessages);
    setDraft("");
    startStreamingReply(conversationId, prompt);
  };

  return {
    activeConversation,
    activeConversationId,
    currentWorkspace,
    draft,
    expandedWorkspaceIds,
    isStreaming,
    messages,
    composerSettings,
    promptSuggestions: builderPromptSuggestions,
    showAllWorkspaceIds,
    sortMode,
    threadGroups: sortedThreadGroups,
    addAttachment,
    addWorkspace,
    archiveWorkspaceThreads,
    archiveThread,
    collapseAllWorkspaces,
    createPermanentWorktree,
    createWorkspaceThread,
    expandAllWorkspaces,
    hasPreviousConversation: previousConversationId !== null,
    openConversation,
    openWorkspaceInExplorer,
    removeWorkspace,
    removeThread,
    reorderWorkspaces,
    renameWorkspace,
    renameThread,
    reopenPreviousConversation,
    removeAttachment,
    sendMessage,
    stopStreaming,
    setPermissionMode,
    setPlanMode,
    setResponseSpeed,
    setDraft,
    startNewChat,
    toggleSortMode,
    toggleWorkspace,
    toggleWorkspaceShowAll,
  };
}
