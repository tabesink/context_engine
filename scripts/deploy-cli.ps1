#Requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap the context-engine CLI into repo-local .venv using uv.

.DESCRIPTION
  Creates .venv if needed, installs editable project dependencies only when
  required, then shows/validates the ragcli command against the configured API.

.PARAMETER Dev
  Install optional dev dependencies as well (equivalent to -e ".[dev]").

.PARAMETER RefreshDeps
  Force reinstall of editable dependencies into .venv.

.PARAMETER ApiBaseUrl
  Override API base URL. If omitted, reads API_PORT from .env and falls back
  to http://127.0.0.1:8000.
#>
param(
    [switch]$Dev,
    [switch]$RefreshDeps,
    [string]$ApiBaseUrl
)

$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw "uv is required. Install from https://docs.astral.sh/uv/getting-started/installation/"
}

if (-not (Test-Path .env) -and (Test-Path .env.example)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - edit if needed."
}

$venvDir = '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$venvCli = Join-Path $venvDir 'Scripts\ragcli.exe'

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

if (-not $ApiBaseUrl) {
    $apiPort = '8000'
    if (Test-Path .env) {
        $apiPortLine = Select-String -Path '.env' -Pattern '^\s*API_PORT\s*=' | Select-Object -First 1
        if ($apiPortLine) {
            $value = ($apiPortLine.Line -split '=', 2)[1].Trim()
            if ($value) { $apiPort = $value }
        }
    }
    $ApiBaseUrl = "http://127.0.0.1:$apiPort"
}

if (-not (Test-Path $venvCli)) {
    throw "ragcli executable not found at $venvCli"
}

Write-Host "CLI ready."
Write-Host "API base URL: $ApiBaseUrl"
Write-Host ""
Write-Host "Example commands:"
Write-Host "  $venvCli --api-base-url $ApiBaseUrl --help"
Write-Host "  $venvCli --api-base-url $ApiBaseUrl login"
Write-Host "  $venvCli --api-base-url $ApiBaseUrl ui"
Write-Host ""

& $venvCli --api-base-url $ApiBaseUrl ui
