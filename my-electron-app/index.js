const { app, BrowserWindow, screen } = require('electron/main')

let win;

function createWindow() {
  const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
  const windowWidth = Math.floor(screenWidth / 3);
  const xPosition = 0; // left side

  win = new BrowserWindow({
    width: windowWidth,
    height: screenHeight,
    x: xPosition,
    y: 0,
    minWidth: 400,
    minHeight: 600,
    vibrancy: "hud",
    titleBarStyle: 'hiddenInset',
    titleBarOverlay: {
      color: '#ffffff',
      symbolColor: '#000000',
      height: 40
    },
    visualEffectState: "active",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    alwaysOnTop: true
  });

  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})