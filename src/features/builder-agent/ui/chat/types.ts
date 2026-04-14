import type { BuilderMessage, BuilderPromptSuggestion } from "../../model/mockBuilderAgent";
import type { BuilderComposerSettings } from "../../model/lib/types";

export interface BuilderChatScreenProps {
  activeConversationId: string | null;
  composerSettings: BuilderComposerSettings;
  currentWorkspaceId: string | null;
  currentWorkspacePath: string | null;
  conversationTitle: string;
  conversationSubtitle: string;
  draft: string;
  isNewChat: boolean;
  isStreaming: boolean;
  messages: BuilderMessage[];
  promptSuggestions: BuilderPromptSuggestion[];
  onArchiveConversation: (conversationId: string) => void;
  onOpenWorkspaceInExplorer: (workspaceId: string) => void;
  onPermissionModeChange: (mode: "default" | "full-access") => void;
  onPickAttachment: () => void;
  onPlanModeChange: (enabled: boolean) => void;
  onRenameConversation: (conversationId: string) => void;
  onDraftChange: (value: string) => void;
  onRemoveAttachment: (path: string) => void;
  onSend: () => void;
  onStopStreaming: () => void;
  onCreatePermanentWorktree: (workspaceId: string) => void;
}
