const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

app.setName('CodeGuard');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1180,
    minHeight: 760,
    center: true,
    backgroundColor: '#f8f4ee',
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#f8f4ee',
      symbolColor: '#2a241e',
      height: 32
    },
    title: 'CodeGuard',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/icon.png')
  });

  mainWindow.removeMenu();

  // في Development mode هنحمل من Vite dev server
  // في Production هنحمل من الملفات المبنية
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:8080');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.setTitle('CodeGuard');

  mainWindow.on('closed', () => {
    mainWindow = null;
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

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
