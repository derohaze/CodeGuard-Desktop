const { app, BrowserWindow, dialog, ipcMain, Menu, Tray } = require('electron');
const path = require('path');

let mainWindow;
let tray = null;
let isQuitting = false;
const INITIAL_WINDOW_WIDTH = 1120;
const INITIAL_WINDOW_HEIGHT = 720;
const MIN_WINDOW_WIDTH = 980;
const MIN_WINDOW_HEIGHT = 640;
const APP_NAME = 'CodeGuard';
const APP_ID = 'com.codeguard.desktop';
const APP_ICON_PATH = process.platform === 'win32'
  ? path.join(__dirname, '../public/icon.ico')
  : path.join(__dirname, '../public/icon.png');

app.setName(APP_NAME);
app.setAppUserModelId(APP_ID);

function createWindow() {
  mainWindow = new BrowserWindow({
    width: INITIAL_WINDOW_WIDTH,
    height: INITIAL_WINDOW_HEIGHT,
    minWidth: MIN_WINDOW_WIDTH,
    minHeight: MIN_WINDOW_HEIGHT,
    center: true,
    show: false,
    backgroundColor: '#1a1a1a',
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    frame: process.platform === 'win32' ? false : true,
    roundedCorners: true,
    title: APP_NAME,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
    icon: APP_ICON_PATH
  });

  mainWindow.removeMenu();

  // ÙÙŠ Development mode Ù‡Ù†Ø­Ù…Ù„ Ù…Ù† Vite dev server
  // ÙÙŠ Production Ù‡Ù†Ø­Ù…Ù„ Ù…Ù† Ø§Ù„Ù…Ù„ÙØ§Øª Ø§Ù„Ù…Ø¨Ù†ÙŠØ©
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:8080');
    // Open DevTools in a detached window (mode: 'detach') so the developer
    // can close it on its own without closing or affecting the main app.
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.setTitle(APP_NAME);
  mainWindow.once('ready-to-show', () => {
    if (!mainWindow) return;
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    }
    if (mainWindow.isFullScreen()) {
      mainWindow.setFullScreen(false);
    }
    mainWindow.setSize(INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT);
    mainWindow.center();
    mainWindow.show();
  });

  const broadcastWindowState = () => {
    if (!mainWindow) return;
    mainWindow.webContents.send('window:state-changed', {
      maximized: mainWindow.isMaximized(),
    });
  };

  mainWindow.on('maximize', broadcastWindowState);
  mainWindow.on('unmaximize', broadcastWindowState);
  mainWindow.on('enter-full-screen', broadcastWindowState);
  mainWindow.on('leave-full-screen', broadcastWindowState);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.on('close', (event) => {
    if (isQuitting) return;
    event.preventDefault();
    mainWindow.hide();
  });
}

function createTray() {
  if (tray) return;

  tray = new Tray(APP_ICON_PATH);
  tray.setToolTip(APP_NAME);
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: `Open ${APP_NAME}`,
        click: () => {
          if (!mainWindow) {
            createWindow();
            return;
          }
          mainWindow.show();
          if (mainWindow.isMinimized()) {
            mainWindow.restore();
          }
          mainWindow.focus();
        },
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          isQuitting = true;
          app.quit();
        },
      },
    ]),
  );

  tray.on('double-click', () => {
    if (!mainWindow) {
      createWindow();
      return;
    }
    mainWindow.show();
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.focus();
  });
}

app.whenReady().then(() => {
  ipcMain.removeHandler('dialog:pick-path');
  ipcMain.handle('dialog:pick-path', async (_event, kind) => {
    if (!mainWindow) return null;

    const properties = kind === 'file' ? ['openFile'] : ['openDirectory'];
    const title = kind === 'file' ? 'Choose a file to scan' : 'Choose a folder to scan';

    const result = await dialog.showOpenDialog(mainWindow, {
      title,
      properties,
    });

    if (result.canceled || result.filePaths.length === 0) {
      return null;
    }

    return result.filePaths[0];
  });

  ipcMain.removeHandler('window:minimize');
  ipcMain.handle('window:minimize', () => {
    if (!mainWindow) return;
    mainWindow.minimize();
  });

  ipcMain.removeHandler('window:toggle-maximize');
  ipcMain.handle('window:toggle-maximize', () => {
    if (!mainWindow) return null;
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
    return mainWindow.isMaximized();
  });

  ipcMain.removeHandler('window:is-maximized');
  ipcMain.handle('window:is-maximized', () => {
    return mainWindow ? mainWindow.isMaximized() : false;
  });

  ipcMain.removeHandler('window:close');
  ipcMain.handle('window:close', () => {
    if (!mainWindow) return;
    // Match the existing behavior of hiding-to-tray on close.
    mainWindow.hide();
  });

  createTray();
  createWindow();
});

app.on('window-all-closed', () => {
  if (isQuitting && process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
});
