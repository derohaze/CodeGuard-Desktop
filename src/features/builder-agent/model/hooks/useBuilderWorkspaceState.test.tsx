import { renderHook, waitFor, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useBuilderWorkspaceState } from "./useBuilderWorkspaceState";

const listBuilderWorkspacesMock = vi.fn();
const getBuilderThreadMock = vi.fn();

vi.mock("../builderApi", async () => {
  const actual = await vi.importActual<object>("../builderApi");
  return {
    ...actual,
    listBuilderWorkspaces: (...args: unknown[]) => listBuilderWorkspacesMock(...args),
    getBuilderThread: (...args: unknown[]) => getBuilderThreadMock(...args),
  };
});

describe("useBuilderWorkspaceState", () => {
  beforeEach(() => {
    listBuilderWorkspacesMock.mockReset();
    getBuilderThreadMock.mockReset();
  });

  it("waits for first-load messages before activating a conversation", async () => {
    listBuilderWorkspacesMock.mockResolvedValue([
      {
        id: "workspace-1",
        label: "project x",
        path: "D:/workspace/project-x",
        updatedAt: "2026-04-14T00:00:00Z",
        threads: [
          {
            id: "thread-1",
            title: "The Latest Python",
            updatedAt: "2026-04-14T00:00:00Z",
          },
        ],
      },
    ]);

    let resolveThread: ((value: unknown) => void) | null = null;
    getBuilderThreadMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveThread = resolve;
        }),
    );

    const { result } = renderHook(() => useBuilderWorkspaceState());

    await waitFor(() => {
      expect(result.current.threadGroups).toHaveLength(1);
    });

    await act(async () => {
      const openPromise = result.current.openConversation("thread-1");
      expect(result.current.activeConversationId).toBeNull();
      expect(result.current.messages).toEqual([]);

      resolveThread?.({
        id: "thread-1",
        workspaceId: "workspace-1",
        title: "The Latest Python",
        updatedAt: "2026-04-14T00:00:01Z",
        messages: [
          {
            id: "assistant-1",
            role: "assistant",
            text: "Ready.",
            createdAt: "2026-04-14T00:00:01Z",
            model: "route/glm-5.1",
          },
        ],
      });

      await openPromise;
    });

    await waitFor(() => {
      expect(result.current.activeConversationId).toBe("thread-1");
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]?.text).toBe("Ready.");
    });
  });
});
