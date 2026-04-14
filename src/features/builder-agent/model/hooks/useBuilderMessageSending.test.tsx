import { renderHook, waitFor, act } from "@testing-library/react";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BuilderMessage } from "../mockBuilderAgent";
import { useBuilderMessageSending } from "./useBuilderMessageSending";

const createBuilderThreadMock = vi.fn();
const sendBuilderMessageMock = vi.fn();
const sendBuilderMessageStreamMock = vi.fn();

vi.mock("../builderApi", () => ({
  createBuilderThread: (...args: unknown[]) => createBuilderThreadMock(...args),
  sendBuilderMessage: (...args: unknown[]) => sendBuilderMessageMock(...args),
  sendBuilderMessageStream: (...args: unknown[]) => sendBuilderMessageStreamMock(...args),
}));

describe("useBuilderMessageSending", () => {
  beforeEach(() => {
    createBuilderThreadMock.mockReset();
    sendBuilderMessageMock.mockReset();
    sendBuilderMessageStreamMock.mockReset();
  });

  it("updates the assistant message before the final stream payload arrives", async () => {
    createBuilderThreadMock.mockResolvedValue({
      id: "thread-1",
      workspaceId: "workspace-1",
      title: "New chat",
      updatedAt: "2026-04-14T00:00:00Z",
      messages: [],
    });

    sendBuilderMessageStreamMock.mockImplementation(async (_payload, handlers) => {
      handlers.onToken("Streaming ");
      await new Promise((resolve) => window.setTimeout(resolve, 120));
      handlers.onToken("reply");
      await new Promise((resolve) => window.setTimeout(resolve, 120));
      return {
        thread: {
          id: "thread-1",
          workspaceId: "workspace-1",
          title: "Streaming reply",
          updatedAt: "2026-04-14T00:00:02Z",
          messages: [
            {
              id: "user-1",
              role: "user",
              text: "hello",
              createdAt: "2026-04-14T00:00:00Z",
              model: null,
            },
            {
              id: "assistant-1",
              role: "assistant",
              text: "Streaming reply",
              createdAt: "2026-04-14T00:00:02Z",
              model: "route/glm-5.1",
            },
          ],
        },
        assistantMessage: {
          id: "assistant-1",
          role: "assistant",
          text: "Streaming reply",
          createdAt: "2026-04-14T00:00:02Z",
          model: "route/glm-5.1",
        },
      };
    });

    const refreshWorkspaces = vi.fn(async () => {});

    const { result } = renderHook(() => {
      const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
      const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>("workspace-1");
      const [draft, setDraft] = useState("hello");
      const [messageMap, setMessageMap] = useState<Record<string, BuilderMessage[]>>({});

      const sending = useBuilderMessageSending({
        activeConversationId,
        composerSettings: {
          permissionMode: "default",
          planMode: false,
          responseSpeed: "normal",
          attachedFiles: [],
        },
        currentWorkspaceId,
        currentWorkspace: { id: "workspace-1" },
        draft,
        refreshWorkspaces,
        setActiveConversationId,
        setCurrentWorkspaceId,
        setDraft,
        setMessageMap,
      });

      return {
        ...sending,
        activeConversationId,
        currentWorkspaceId,
        draft,
        messageMap,
      };
    });

    act(() => {
      result.current.sendMessage();
    });

    await waitFor(() => {
      expect(result.current.activeConversationId).toBe("thread-1");
    });

    await waitFor(() => {
      const assistant = result.current.messageMap["thread-1"]?.find((message) => message.role === "assistant");
      expect(assistant?.text.length ?? 0).toBeGreaterThan(0);
      expect(assistant?.text).not.toBe("Streaming reply");
    });

    await waitFor(() => {
      const assistant = result.current.messageMap["thread-1"]?.find((message) => message.role === "assistant");
      expect(assistant?.text).toBe("Streaming reply");
      expect(result.current.isStreaming).toBe(false);
    });

    expect(refreshWorkspaces).toHaveBeenCalledTimes(1);
    expect(sendBuilderMessageMock).not.toHaveBeenCalled();
  });
});
