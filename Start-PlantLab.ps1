param([int]$Port = 8787, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$url = "http://127.0.0.1:$Port"
function Test-PlantService {
    try {
        $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2
        return ($health.status -eq 'ready' -and $health.model -eq 'VGG19' -and $health.class_count -eq 36)
    } catch { return $false }
}
if (Test-PlantService) {
    Write-Host "Plant Disease Lab is already ready at $url"
    if (-not $NoBrowser) { Start-Process $url }
    exit 0
}
$pythonExe = $null
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not $pythonExe -and (Test-Path -LiteralPath $venvPython)) { $pythonExe = $venvPython }
if (-not $pythonExe) {
    $candidate = $null
    foreach ($version in @('3.12','3.11','3.10')) {
        try {
            $out = & py "-$version" -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { $candidate = ($out | Select-Object -Last 1).Trim(); break }
        } catch {}
    }
    if (-not $candidate) {
        try {
            $out = & python -c 'import sys; assert (3,10) <= sys.version_info[:2] <= (3,12); print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { $candidate = ($out | Select-Object -Last 1).Trim() }
        } catch {}
    }
    if (-not $candidate) { throw 'Install 64-bit Python 3.10, 3.11 or 3.12, then run this launcher again.' }
    Write-Host 'Creating an isolated Python environment in this project...'
    & $candidate -m venv (Join-Path $projectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
    $pythonExe = $venvPython
    Write-Host 'Installing the model runtime. The first setup downloads TensorFlow.'
    & $pythonExe -m pip install -r (Join-Path $projectRoot 'backend\requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your internet connection and requirements.txt.' }
}
$runDir = Join-Path $projectRoot '.run'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$serverPath = Join-Path $projectRoot 'backend\server.py'
$outLog = Join-Path $runDir "server-$Port.log"
$errLog = Join-Path $runDir "server-$Port-errors.log"
$modelPath = Join-Path $projectRoot 'models\best_model.h5'
$arguments = '"' + $serverPath + '" --model "' + $modelPath + '" --port ' + $Port
$process = Start-Process -FilePath $pythonExe -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
Set-Content -LiteralPath (Join-Path $runDir "server-$Port.pid") -Value $process.Id
Write-Host 'Loading your original model. This can take a minute on the first launch...'
for ($attempt = 0; $attempt -lt 90; $attempt++) {
    if (Test-PlantService) {
        Write-Host "Plant Disease Lab is ready at $url"
        Write-Host "Stop it with: .\Stop-PlantLab.ps1 -Port $Port"
        if (-not $NoBrowser) { Start-Process $url }
        exit 0
    }
    $process.Refresh()
    if ($process.HasExited) { throw "The model service stopped. Read $errLog" }
    Start-Sleep -Seconds 2
}
throw "The service has not become ready yet. Check $outLog and $errLog."
