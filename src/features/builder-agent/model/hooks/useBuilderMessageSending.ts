import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import {
  createBuilderThread,
  sendBuilderMessage,
  sendBuilderMessageStream,
} from "../builderApi";
import type { BuilderMessage } from "../mockBuilderAgent";
import type { BuilderComposerSettings } from "../lib/types";
import { mapMessage } from "../lib/mappers";
import {
  builderStreamConfig,
  resolveStreamRevealBatchSize,
  resolveStreamingCharsPerSecond,
  splitStreamDisplayUnits,
} from "../lib/streaming";

interface UseBuilderMessageSendingParams {
  activeConversationId: string | null;
  composerSettings: BuilderComposerSettings;
  currentWorkspaceId: string | null;
  currentWorkspace: { id: string } | null;
  draft: string;
  refreshWorkspaces: () => Promise<void>;
  setActiveConversationId: Dispatch<SetStateAction<string | null>>;
  setCurrentWorkspaceId: Dispatch<SetStateAction<string | null>>;
  setDraft: Dispatch<SetStateAction<string>>;
  setMessageMap: Dispatch<SetStateAction<Record<string, BuilderMessage[]>>>;
}

export function useBuilderMessageSending({
  activeConversationId,
  composerSettings,
  currentWorkspace,
  draft,
  refreshWorkspaces,
  setActiveConversationId,
  setCurrentWorkspaceId,
  setDraft,
  setMessageMap,
}: UseBuilderMessageSendingParams) {
  const [isStreaming, setIsStreaming] = useState(false);
  const activeSendAbortRef = useRef<AbortController | null>(null);
  const activeStreamThreadIdRef = useRef<string | null>(null);
  const activeStreamAssistantIdRef = useRef<string | null>(null);
  const streamUnitsRef = useRef<string[]>([]);
  const streamVisibleTextRef = useRef("");
  const streamSourceCompletedRef = useRef(true);
  const streamDrainStartedRef = useRef(false);
  const streamDrainFrameRef = useRef<number | null>(null);
  const streamWarmupTimeoutRef = useRef<number | null>(null);
  const streamDrainResolverRef = useRef<(() => void) | null>(null);
  const streamRevealBudgetRef = useRef(0);
  const streamLastDrainAtRef = useRef<number | null>(null);

  const markAssistantStopped = useCallback((threadId?: string | null, assistantId?: string | null) => {
    const resolvedThreadId = threadId ?? activeStreamThreadIdRef.current;
    const resolvedAssistantId = assistantId ?? activeStreamAssistantIdRef.current;
    const visibleText = streamVisibleTextRef.current;
    if (!resolvedThreadId || !resolvedAssistantId) {
      return;
    }
    setMessageMap((current) => ({
      ...current,
      [resolvedThreadId]: (current[resolvedThreadId] ?? []).map((item) => (
        item.id === resolvedAssistantId
          ? {
              ...item,
              text: visibleText || item.text,
              isStreaming: false,
            }
          : item
      )),
    }));
  }, [setMessageMap]);

  const markActiveAssistantStopped = useCallback(() => {
    const threadId = activeStreamThreadIdRef.current;
    const assistantId = activeStreamAssistantIdRef.current;
    if (!threadId || !assistantId) {
      return;
    }
    markAssistantStopped(threadId, assistantId);
  }, [markAssistantStopped]);

  const stopStreaming = useCallback(() => {
    if (activeSendAbortRef.current) {
      activeSendAbortRef.current.abort();
      activeSendAbortRef.current = null;
    }
    if (streamDrainFrameRef.current !== null) {
      window.cancelAnimationFrame(streamDrainFrameRef.current);
      streamDrainFrameRef.current = null;
    }
    if (streamWarmupTimeoutRef.current !== null) {
      window.clearTimeout(streamWarmupTimeoutRef.current);
      streamWarmupTimeoutRef.current = null;
    }
    streamSourceCompletedRef.current = true;
    streamDrainStartedRef.current = false;
    streamUnitsRef.current = [];
    streamRevealBudgetRef.current = 0;
    streamLastDrainAtRef.current = null;
    markActiveAssistantStopped();
    if (streamDrainResolverRef.current) {
      streamDrainResolverRef.current();
      streamDrainResolverRef.current = null;
    }
    setIsStreaming(false);
  }, [markActiveAssistantStopped]);

  useEffect(() => {
    return () => {
      if (activeSendAbortRef.current) {
        activeSendAbortRef.current.abort();
      }
      if (streamDrainFrameRef.current !== null) {
        window.cancelAnimationFrame(streamDrainFrameRef.current);
      }
      if (streamWarmupTimeoutRef.current !== null) {
        window.clearTimeout(streamWarmupTimeoutRef.current);
      }
    };
  }, []);

  const sendMessage = useCallback(() => {
    void (async () => {
      const prompt = draft.trim();
      if (!prompt || !currentWorkspace) return;

      let threadId = activeConversationId;
      if (!threadId) {
        try {
          const created = await createBuilderThread(currentWorkspace.id);
          threadId = created.id;
          setActiveConversationId(created.id);
          setCurrentWorkspaceId(created.workspaceId);
          setMessageMap((current) => ({
            ...current,
            [created.id]: created.messages.map(mapMessage),
          }));
        } catch (error) {
          console.error("[CodeGuard Builder] Failed to bootstrap chat thread", error);
          return;
        }
      }
      if (!threadId) return;

      const optimisticUserMessage: BuilderMessage = {
        id: `local-user-${Date.now()}`,
        role: "user",
        text: prompt,
      };
      const optimisticAssistantId = `local-assistant-${Date.now() + 1}`;
      setMessageMap((current) => ({
        ...current,
        [threadId!]: [
          ...(current[threadId!] ?? []),
          optimisticUserMessage,
          {
            id: optimisticAssistantId,
            role: "assistant",
            text: "",
            isStreaming: true,
          },
        ],
      }));
      setDraft("");

      const abortController = new AbortController();
      activeSendAbortRef.current = abortController;
      activeStreamThreadIdRef.current = threadId;
      activeStreamAssistantIdRef.current = optimisticAssistantId;
      setIsStreaming(true);
      streamUnitsRef.current = [];
      streamVisibleTextRef.current = "";
      streamSourceCompletedRef.current = false;
      streamDrainStartedRef.current = false;
      streamRevealBudgetRef.current = 0;
      streamLastDrainAtRef.current = null;

      try {
        const payload = {
          workspaceId: currentWorkspace.id,
          threadId,
          message: prompt,
          permissionMode: composerSettings.permissionMode,
          planMode: composerSettings.planMode,
          responseSpeed: composerSettings.responseSpeed,
        } as const;

        const pushVisibleText = (nextText: string) => {
          streamVisibleTextRef.current = nextText;
          setMessageMap((current) => ({
            ...current,
            [threadId!]: (current[threadId!] ?? []).map((item) => (
              item.id === optimisticAssistantId
                ? { ...item, text: nextText }
                : item
            )),
          }));
        };

        const clearWarmupTimer = () => {
          if (streamWarmupTimeoutRef.current !== null) {
            window.clearTimeout(streamWarmupTimeoutRef.current);
            streamWarmupTimeoutRef.current = null;
          }
        };

        const resolveDrainWaiter = () => {
          if (streamDrainResolverRef.current) {
            streamDrainResolverRef.current();
            streamDrainResolverRef.current = null;
          }
        };

        const finishDrainIfIdle = () => {
          if (streamUnitsRef.current.length > 0) {
            return;
          }
          if (!streamSourceCompletedRef.current) {
            return;
          }
          if (streamDrainFrameRef.current !== null) {
            return;
          }
          clearWarmupTimer();
          resolveDrainWaiter();
        };

        const drainBufferedText = () => {
          streamDrainFrameRef.current = null;

          if (abortController.signal.aborted || activeSendAbortRef.current !== abortController) {
            finishDrainIfIdle();
            return;
          }

          const bufferLength = streamUnitsRef.current.length;
          const now = typeof performance !== "undefined" ? performance.now() : Date.now();
          const lastDrainAt = streamLastDrainAtRef.current ?? now;
          streamLastDrainAtRef.current = now;

          if (!streamDrainStartedRef.current) {
            const shouldStart =
              streamSourceCompletedRef.current || bufferLength >= builderStreamConfig.startBuffer;
            if (!shouldStart) {
              return;
            }
            streamDrainStartedRef.current = true;
            streamLastDrainAtRef.current = now;
            streamRevealBudgetRef.current = Math.max(streamRevealBudgetRef.current, 1);
          }

          if (bufferLength === 0) {
            if (streamSourceCompletedRef.current) {
              finishDrainIfIdle();
              return;
            }
            streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
            return;
          }

          const charsPerSecond = streamSourceCompletedRef.current
            ? builderStreamConfig.completionCharsPerSecond
            : resolveStreamingCharsPerSecond(bufferLength);
          const elapsedMs = Math.max(0, now - lastDrainAt);
          streamRevealBudgetRef.current += (elapsedMs / 1000) * charsPerSecond;

          const batchSize = resolveStreamRevealBatchSize(
            bufferLength,
            streamSourceCompletedRef.current,
            streamRevealBudgetRef.current,
          );
          if (batchSize <= 0) {
            streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
            return;
          }

          streamRevealBudgetRef.current = Math.max(0, streamRevealBudgetRef.current - batchSize);
          const nextChunk = streamUnitsRef.current.splice(0, batchSize).join("");
          if (nextChunk) {
            pushVisibleText(streamVisibleTextRef.current + nextChunk);
          }

          if (streamUnitsRef.current.length === 0 && streamSourceCompletedRef.current) {
            finishDrainIfIdle();
            return;
          }

          streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
        };

        const startDrain = () => {
          clearWarmupTimer();
          streamDrainStartedRef.current = true;
          if (streamDrainFrameRef.current === null) {
            streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
          }
        };

        const ensureWarmup = () => {
          if (streamDrainStartedRef.current || streamWarmupTimeoutRef.current !== null) {
            return;
          }
          streamWarmupTimeoutRef.current = window.setTimeout(() => {
            streamWarmupTimeoutRef.current = null;
            if (abortController.signal.aborted || activeSendAbortRef.current !== abortController) {
              return;
            }
            startDrain();
          }, builderStreamConfig.warmupMs);
        };

        const enqueueToken = (token: string) => {
          streamUnitsRef.current.push(...splitStreamDisplayUnits(token));
          if (!streamDrainStartedRef.current) {
            if (streamUnitsRef.current.length >= builderStreamConfig.startBuffer) {
              startDrain();
            } else {
              ensureWarmup();
            }
            return;
          }
          if (streamDrainFrameRef.current === null) {
            streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
          }
        };

        const waitForDrain = async () => {
          streamSourceCompletedRef.current = true;
          clearWarmupTimer();
          if (!streamDrainStartedRef.current) {
            startDrain();
          } else if (streamDrainFrameRef.current === null) {
            streamDrainFrameRef.current = window.requestAnimationFrame(drainBufferedText);
          }
          if (streamUnitsRef.current.length === 0 && streamDrainFrameRef.current === null) {
            return;
          }
          await new Promise<void>((resolve) => {
            streamDrainResolverRef.current = resolve;
          });
        };

        let result = await sendBuilderMessageStream(
          payload,
          {
            onToken: (token) => {
              enqueueToken(token);
            },
            onReasoning: () => {
              // Builder chat should stream only the visible assistant answer.
            },
          },
          abortController.signal,
        );
        await waitForDrain();

        if (!result) {
          result = await sendBuilderMessage(payload, abortController.signal);
        }

        setMessageMap((current) => ({
          ...current,
          [result.thread.id]: result.thread.messages.map(mapMessage),
        }));
        setActiveConversationId(result.thread.id);
        setCurrentWorkspaceId(result.thread.workspaceId);
        await refreshWorkspaces();
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }
        try {
          const result = await sendBuilderMessage(
            {
              workspaceId: currentWorkspace.id,
              threadId,
              message: prompt,
              permissionMode: composerSettings.permissionMode,
              planMode: composerSettings.planMode,
              responseSpeed: composerSettings.responseSpeed,
            },
            abortController.signal,
          );
          setMessageMap((current) => ({
            ...current,
            [result.thread.id]: result.thread.messages.map(mapMessage),
          }));
          setActiveConversationId(result.thread.id);
          setCurrentWorkspaceId(result.thread.workspaceId);
          await refreshWorkspaces();
        } catch (fallbackError) {
          console.error("[CodeGuard Builder] Failed to send message", fallbackError ?? error);
        }
      } finally {
        if (streamDrainFrameRef.current !== null) {
          window.cancelAnimationFrame(streamDrainFrameRef.current);
          streamDrainFrameRef.current = null;
        }
        if (streamWarmupTimeoutRef.current !== null) {
          window.clearTimeout(streamWarmupTimeoutRef.current);
          streamWarmupTimeoutRef.current = null;
        }
        streamUnitsRef.current = [];
        streamSourceCompletedRef.current = true;
        streamDrainStartedRef.current = false;
        streamRevealBudgetRef.current = 0;
        streamLastDrainAtRef.current = null;
        if (streamDrainResolverRef.current) {
          streamDrainResolverRef.current();
          streamDrainResolverRef.current = null;
        }
        markAssistantStopped(threadId, optimisticAssistantId);
        streamVisibleTextRef.current = "";
        if (
          activeStreamThreadIdRef.current === threadId &&
          activeStreamAssistantIdRef.current === optimisticAssistantId
        ) {
          activeStreamThreadIdRef.current = null;
          activeStreamAssistantIdRef.current = null;
        }
        if (activeSendAbortRef.current === abortController) {
          activeSendAbortRef.current = null;
          setIsStreaming(false);
        }
      }
    })();
  }, [
    activeConversationId,
    composerSettings.permissionMode,
    composerSettings.planMode,
    composerSettings.responseSpeed,
    currentWorkspace,
    draft,
    markAssistantStopped,
    refreshWorkspaces,
    setActiveConversationId,
    setCurrentWorkspaceId,
    setDraft,
    setMessageMap,
  ]);

  return {
    isStreaming,
    sendMessage,
    stopStreaming,
  };
}
