export interface ElectronWindowState {
  maximized: boolean;
}

export interface ElectronWindowControls {
  minimize: () => Promise<void>;
  toggleMaximize: () => Promise<boolean | null>;
  isMaximized: () => Promise<boolean>;
  close: () => Promise<void>;
  onStateChanged: (listener: (state: ElectronWindowState) => void) => () => void;
}

export interface ElectronAPI {
  platform: string;
  versions: {
    node: string;
    chrome: string;
    electron: string;
  };
  pickPath?: (kind: "file" | "folder") => Promise<string | null>;
  windowControls?: ElectronWindowControls;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}