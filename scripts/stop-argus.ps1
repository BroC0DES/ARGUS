# Stops everything Launch ARGUS.bat started, cleanly. Kills each tracked
# process by PID with /T (its whole process tree), which also takes down
# the traffic simulator the backend spawned as its own child process --
# nothing is left running in the background.

$PidFile = Join-Path $PSScriptRoot ".run\pids.txt"

if (-not (Test-Path $PidFile)) {
    Write-Host "ARGUS doesn't look like it's running (no record of a Launch ARGUS.bat session)." -ForegroundColor Yellow
    exit 0
}

$stopped = 0
Get-Content $PidFile | ForEach-Object {
    $parts = $_ -split ","
    if ($parts.Count -lt 2) { return }
    $label, $procId = $parts[0], $parts[1]
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
        Write-Host "Stopping $label (pid $procId)..." -ForegroundColor Cyan
        taskkill /PID $procId /T /F 2>$null | Out-Null
        $stopped++
    }
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

if ($stopped -gt 0) {
    Write-Host "ARGUS stopped." -ForegroundColor Green
} else {
    Write-Host "Nothing was still running (already stopped)." -ForegroundColor Yellow
}
