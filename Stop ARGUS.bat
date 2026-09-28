@echo off
REM Double-click this to cleanly stop everything Launch ARGUS.bat started.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-argus.ps1"
pause
