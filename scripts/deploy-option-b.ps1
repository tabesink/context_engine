#Requires -Version 5.1
<#
.SYNOPSIS
  Option B: local Postgres/Redis via Docker (optional), editable install, seed admin, uvicorn.

.PARAMETER Dev
  pip install -e ".[dev]"

.PARAMETER NoDocker
  Skip docker compose (you already run Postgres/Redis per .env).

.PARAMETER RefreshDeps
  Force reinstall of editable dependencies into .venv.
#>
param(
    [switch]$Dev,
    [switch]$NoDocker,
    [switch]$RefreshDeps
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw "uv is required for Option B. Install from https://docs.astral.sh/uv/getting-started/installation/"
}

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - edit if needed."
}

$apiPort = '8000'
$apiPortLine = Select-String -Path '.env' -Pattern '^\s*API_PORT\s*=' | Select-Object -First 1
if ($apiPortLine) {
    $value = ($apiPortLine.Line -split '=', 2)[1].Trim()
    if ($value) { $apiPort = $value }
}

if (-not $NoDocker) {
    docker compose up postgres redis -d
    $ok = $false
    for ($i = 0; $i -lt 45; $i++) {
        docker compose exec -T postgres pg_isready -U context_engine -d context_engine 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ok = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ok) { throw "Postgres not ready (docker compose postgres)." }
}

$venvDir = '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    uv venv $venvDir
}

$baseMarker = Join-Path $venvDir '.deps-base.stamp'
$devMarker = Join-Path $venvDir '.deps-dev.stamp'
$needsInstall = $RefreshDeps -or (-not (Test-Path $baseMarker))
if ($Dev -and -not (Test-Path $devMarker)) {
    $needsInstall = $true
}

if ($needsInstall) {
    $spec = if ($Dev) { '.[dev]' } else { '.' }
    uv pip install --python $venvPython -e $spec
    if (-not (Test-Path $baseMarker)) {
        New-Item -ItemType File -Path $baseMarker | Out-Null
    }
    if ($Dev -and -not (Test-Path $devMarker)) {
        New-Item -ItemType File -Path $devMarker | Out-Null
    }
}

& $venvPython -m scripts.seed_admin
& $venvPython -m uvicorn app.main:create_app --factory --reload --port $apiPort
