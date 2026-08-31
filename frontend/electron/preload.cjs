const { contextBridge, ipcRenderer } = require('electron');

// Keep track so the renderer can subscribe to maximize changes.
const windowStateListeners = new Set();

ipcRenderer.on('window:state-changed', (_event, state) => {
  for (const listener of windowStateListeners) {
    listener(state);
  }
});

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  pickPath: (kind) => ipcRenderer.invoke('dialog:pick-path', kind),
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  },
  windowControls: {
    minimize: () => ipcRenderer.invoke('window:minimize'),
    toggleMaximize: () => ipcRenderer.invoke('window:toggle-maximize'),
    isMaximized: () => ipcRenderer.invoke('window:is-maximized'),
    close: () => ipcRenderer.invoke('window:close'),
    onStateChanged: (listener) => {
      windowStateListeners.add(listener);
      return () => windowStateListeners.delete(listener);
    }
  }
});
