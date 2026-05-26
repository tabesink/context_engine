#Requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap the context-engine CLI into repo-local .venv using uv.

.DESCRIPTION
  Creates .venv if needed, installs editable project dependencies only when
  required, then launches the TUI-only CLI against the configured API.

.PARAMETER Dev
  Install optional dev dependencies as well (equivalent to -e ".[dev]").

.PARAMETER RefreshDeps
  Force reinstall of editable dependencies into .venv.

.PARAMETER ApiBaseUrl
  Override API base URL. If omitted, reads API_PORT from .env and falls back
  to http://127.0.0.1:8010.
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

function Get-EnvValue([string]$Key, [string]$Path = ".env") {
    if (-not (Test-Path $Path)) { return $null }
    $line = Select-String -Path $Path -Pattern "^\s*$Key\s*=" | Select-Object -First 1
    if (-not $line) { return $null }
    $value = ($line.Line -split '=', 2)[1].Trim()
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return $value
}

$venvDir = '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$venvCli = Join-Path $venvDir 'Scripts\context-engine.exe'
$fallbackCli = Join-Path $venvDir 'Scripts\context-tui.exe'

if (-not (Test-Path $venvPython)) {
    uv venv $venvDir
}

$baseMarker = Join-Path $venvDir '.deps-base.stamp'
$devMarker = Join-Path $venvDir '.deps-dev.stamp'
$needsInstall = $RefreshDeps -or (-not (Test-Path $baseMarker))
if ($Dev -and -not (Test-Path $devMarker)) {
    $needsInstall = $true
}
if (-not (Test-Path $venvCli) -and -not (Test-Path $fallbackCli)) {
    # New script entrypoints require reinstall when migrating from old ragcli-only envs.
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
    $apiPort = if ($env:API_PORT) { $env:API_PORT } else { Get-EnvValue -Key 'API_PORT' }
    if (-not $apiPort) { $apiPort = '8010' }
    $apiHost = if ($env:API_HOST) { $env:API_HOST } else { Get-EnvValue -Key 'API_HOST' }
    if (-not $apiHost) { $apiHost = '127.0.0.1' }
    $ApiBaseUrl = "http://$apiHost:$apiPort"
}

if (-not (Test-Path $venvCli)) {
    if (Test-Path $fallbackCli) {
        $venvCli = $fallbackCli
    } else {
        throw "context-engine executable not found. Re-run with -RefreshDeps."
    }
}

Write-Host "CLI ready."
Write-Host "API base URL: $ApiBaseUrl"
Write-Host ""
Write-Host "Example commands:"
Write-Host "  `$env:CONTEXT_ENGINE_API_BASE_URL = '$ApiBaseUrl'"
Write-Host "  $venvCli --help"
Write-Host "  $venvCli"
Write-Host ""

$env:CONTEXT_ENGINE_API_BASE_URL = $ApiBaseUrl
& $venvCli
