const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let pythonProcess;

const SERVER_PORT = 8787;
const SERVER_URL = `http://127.0.0.1:${SERVER_PORT}/pet_studio.html`;

function getServerSpawnConfig() {
    if (app.isPackaged) {
        const exe = path.join(process.resourcesPath, 'python-dist', 'server', 'pet_studio_server.exe');
        return { command: exe, args: [], cwd: path.dirname(exe) };
    }
    // Development: run from project root (3 levels up from src/main/)
    const projectRoot = path.join(__dirname, '..', '..', '..');
    return { command: 'python', args: [path.join(projectRoot, 'pet_studio_server.py')], cwd: projectRoot };
}

function isServerRunning(callback) {
    const req = http.get(`http://127.0.0.1:${SERVER_PORT}/`, (res) => {
        callback(true);
    });
    req.on('error', () => callback(false));
    req.setTimeout(1000, () => { req.destroy(); callback(false); });
}

function waitForServer(timeout, callback) {
    const start = Date.now();
    const check = () => {
        const req = http.get(`http://127.0.0.1:${SERVER_PORT}/`, (res) => {
            callback(null);
        });
        req.on('error', () => {
            if (Date.now() - start > timeout) {
                callback(new Error('Server startup timed out'));
            } else {
                setTimeout(check, 300);
            }
        });
        req.setTimeout(500, () => req.destroy());
    };
    check();
}

function startPythonServer(callback) {
    isServerRunning((running) => {
        if (running) {
            console.log('[Lamuh Pets] Server already running on port ' + SERVER_PORT);
            callback();
            return;
        }

        const { command, args, cwd } = getServerSpawnConfig();
        console.log('[Lamuh Pets] Starting server: ' + command + ' ' + args.join(' '));
        pythonProcess = spawn(command, args, {
            cwd,
            stdio: ['ignore', 'pipe', 'pipe'],
            windowsHide: true
        });

        pythonProcess.stdout.on('data', (d) => console.log('[Server] ' + d.toString().trim()));
        pythonProcess.stderr.on('data', (d) => console.error('[Server] ' + d.toString().trim()));
        pythonProcess.on('error', (err) => console.error('[Lamuh Pets] Server error:', err.message));
        pythonProcess.on('close', (code) => {
            console.log('[Lamuh Pets] Server exited with code ' + code);
            pythonProcess = null;
        });

        // Wait for it to be ready
        waitForServer(15000, callback);
    });
}

function killPythonServer() {
    if (pythonProcess) {
        console.log('[Lamuh Pets] Shutting down server...');
        pythonProcess.kill();
        pythonProcess = null;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 850,
        minWidth: 900,
        minHeight: 600,
        title: 'Lamuh Pets \u2014 Pet Hatch Studio',
        backgroundColor: '#101114',
        show: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.loadURL(SERVER_URL);
    mainWindow.once('ready-to-show', () => mainWindow.show());
    mainWindow.on('closed', () => { mainWindow = null; });
}

app.on('ready', () => {
    // Check for updates and notify the user
    autoUpdater.checkForUpdatesAndNotify();

    startPythonServer((err) => {
        if (err) console.error('[Lamuh Pets] ' + err.message);
        createWindow();
    });
});

app.on('window-all-closed', () => {
    killPythonServer();
    app.quit();
});

app.on('before-quit', killPythonServer);
process.on('exit', killPythonServer);
