const { app, BrowserWindow, screen } = require('electron/main');

let win;

function createWindow() {
  const display = screen.getPrimaryDisplay();
  const { width: screenWidth } = display.workAreaSize;
  const { height: fullHeight } = display.bounds; // includes Dock

  const windowWidth = Math.floor(screenWidth / 3.5);
  const windowHeight = Math.floor(fullHeight * 0.5);

  const xPosition = 0; // left edge
  const yPosition = fullHeight - windowHeight; // true bottom

  win = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    x: xPosition,
    y: yPosition,
    minWidth: 200,
    minHeight: 300,
    vibrancy: 'hud',
    titleBarStyle: 'hiddenInset',
    titleBarOverlay: {
      color: '#ffffff',
      symbolColor: '#000000',
      height: 40
    },
    visualEffectState: 'active',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    alwaysOnTop: true
  });

  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
