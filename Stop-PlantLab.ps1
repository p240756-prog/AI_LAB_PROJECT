param([int]$Port = 8787)
$ErrorActionPreference = 'Stop'
$pidFile = Join-Path $PSScriptRoot ".run\server-$Port.pid"
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host 'No launcher-managed service was found for this port.'; exit 0 }
$taskProcessId = [int](Get-Content -LiteralPath $pidFile -Raw)
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskProcessId" -ErrorAction SilentlyContinue
$expectedScript = Join-Path $PSScriptRoot 'backend\server.py'
if ($taskProcess -and $taskProcess.Name -eq 'python.exe' -and $taskProcess.CommandLine.Contains($expectedScript) -and $taskProcess.CommandLine.Contains("--port $Port")) {
    Stop-Process -Id $taskProcessId
    Remove-Item -LiteralPath $pidFile
    Write-Host "Stopped Plant Disease Lab on port $Port."
} else { Write-Host 'Process identity did not match this project. No process was stopped.' }
