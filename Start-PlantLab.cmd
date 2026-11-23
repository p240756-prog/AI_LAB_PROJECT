@echo off
powershell.exe -NoProfile -File "%~dp0Start-PlantLab.ps1"
if errorlevel 1 pause
