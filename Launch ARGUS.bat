@echo off
REM Double-click this. Starts the backend, all mock services, the traffic
REM simulator (via the backend), and the frontend -- then opens your browser.
REM No terminal typing needed. See scripts\launch-argus.ps1 for the details.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch-argus.ps1"
pause
