/// <reference types="vite/client" />

interface Window {
  electronAPI?: {
    platform: string;
    versions: {
      node: string;
      chrome: string;
      electron: string;
    };
    pickPath?: (kind: "file" | "folder") => Promise<string | null>;
    windowControls?: {
      minimize: () => Promise<void>;
      toggleMaximize: () => Promise<boolean | null>;
      isMaximized: () => Promise<boolean>;
      close: () => Promise<void>;
      onStateChanged: (listener: (state: { maximized: boolean }) => void) => () => void;
    };
  };
}