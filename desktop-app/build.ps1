# Build script for Lamuh Pets Windows installer
# Run from desktop-app/ with: .\build.ps1

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== Lamuh Pets Build ===" -ForegroundColor Cyan

# --- 1. Install Python dependencies ---
Write-Host "`n[1/4] Checking Python deps..." -ForegroundColor Yellow
python -m pip install pyinstaller pillow google-genai google-generativeai --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# --- 2. Build pet.exe ---
Write-Host "`n[2/4] Building pet.exe..." -ForegroundColor Yellow
if (Test-Path "dist\pet") { Remove-Item -Recurse -Force "dist\pet" }
python -m PyInstaller pet.spec --distpath dist --workpath build_tmp\pet --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller pet.spec failed" }

# --- 3. Build pet_studio_server.exe ---
Write-Host "`n[3/4] Building pet_studio_server.exe..." -ForegroundColor Yellow
if (Test-Path "dist\server") { Remove-Item -Recurse -Force "dist\server" }
python -m PyInstaller pet_studio_server.spec --distpath dist --workpath build_tmp\server --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller pet_studio_server.spec failed" }

# --- Copy Python bundles to python-dist/ for electron-builder ---
Write-Host "`nStaging Python bundles to python-dist/..." -ForegroundColor Yellow
if (Test-Path "python-dist") { Remove-Item -Recurse -Force "python-dist" }
New-Item -ItemType Directory -Path "python-dist" | Out-Null
Copy-Item -Recurse "dist\pet" "python-dist\pet"
Copy-Item -Recurse "dist\server" "python-dist\server"

# --- 4. Build Electron installer ---
Write-Host "`n[4/4] Building Electron installer..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
npm run build
if ($LASTEXITCODE -ne 0) { throw "electron-builder failed" }

Write-Host "`n=== Build complete! Installer is in desktop-app/dist/ ===" -ForegroundColor Green
