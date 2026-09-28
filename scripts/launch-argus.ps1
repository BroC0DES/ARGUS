# Starts every piece of ARGUS with one double-click (via ..\Launch ARGUS.bat):
# backend, the 6 mock services + mock gateway, the frontend dev server, and
# opens your browser to it. The traffic simulator is NOT started here -- the
# backend starts it automatically on its own startup (see
# backend/traffic_control.py), which is also what lets the Traffic ON/OFF
# button in the UI stop and restart it later without touching a terminal.
#
# Each piece runs in its own titled console window so you can see its logs;
# ..\Stop ARGUS.bat closes all of them cleanly by PID.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $PSScriptRoot ".run"
$PidFile = Join-Path $RunDir "pids.txt"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

if (Test-Path $PidFile) {
    $existing = Get-Content $PidFile | ForEach-Object {
        $p = ($_ -split ",")[1]
        if ($p -and (Get-Process -Id $p -ErrorAction SilentlyContinue)) { $p }
    }
    if ($existing) {
        Write-Host "ARGUS looks like it's already running. Run 'Stop ARGUS.bat' first, then try again." -ForegroundColor Yellow
        exit 1
    }
}

$BackendDir = Join-Path $Root "backend"
$MockDir = Join-Path $Root "mock-codebase2"
$FrontendDir = Join-Path $Root "frontend"

$missing = @()
if (-not (Test-Path (Join-Path $MockDir "node_modules"))) { $missing += "mock-codebase2 (run: cd mock-codebase2 && npm install)" }
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) { $missing += "frontend (run: cd frontend && npm install)" }
if ($missing) {
    Write-Host "First-time setup isn't done yet:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "Run those once, then double-click Launch ARGUS.bat again." -ForegroundColor Yellow
    exit 1
}

function Start-Titled($title, $dir, $command) {
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "title $title && $command" -WorkingDirectory $dir -WindowStyle Normal -PassThru
    return $p
}

Write-Host "Starting ARGUS backend (port 8000)..." -ForegroundColor Cyan
$backend = Start-Titled "ARGUS - Backend" $BackendDir "py -3 -m uvicorn main:app --port 8000"

Write-Host "Starting mock services (6 services + mock gateway)..." -ForegroundColor Cyan
$mock = Start-Titled "ARGUS - Mock Services" $MockDir "node dev.mjs"

Write-Host "Starting frontend (port 5173)..." -ForegroundColor Cyan
$frontend = Start-Titled "ARGUS - Frontend" $FrontendDir "npm run dev"

"backend,$($backend.Id)`nmock,$($mock.Id)`nfrontend,$($frontend.Id)" | Set-Content -Path $PidFile

Write-Host "Waiting a few seconds for everything to come up..." -ForegroundColor Cyan
Start-Sleep -Seconds 4

Write-Host "Opening ARGUS in your browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "ARGUS is starting up. Three windows are running its pieces (Backend / Mock Services / Frontend) --" -ForegroundColor Green
Write-Host "leave them open. The traffic simulator started automatically with the backend; use the" -ForegroundColor Green
Write-Host "Traffic ON/OFF button in the app to pause/resume it. Run 'Stop ARGUS.bat' when you're done." -ForegroundColor Green
