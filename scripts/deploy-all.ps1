#Requires -Version 5.1
<#
.SYNOPSIS
  Start backend and frontend dev servers together.

.DESCRIPTION
  Starts:
    - backend via docker compose (recommended default)
    - client via npm run dev in ./client

  Optional local API mode uses scripts/deploy-server.ps1.

.EXAMPLE
  .\scripts\deploy-all.ps1

.EXAMPLE
  .\scripts\deploy-all.ps1 -LocalApi -Dev
#>
param(
    [switch]$LocalApi,
    [switch]$Dev,
    [switch]$NoDocker,
    [switch]$RefreshDeps,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Show-Usage {
    @"
Usage: scripts/deploy-all.ps1 [-Dev] [-NoDocker] [-RefreshDeps]

Starts:
  - backend via docker compose (postgres, redis, migrate, api, worker, status-poller)
  - client via npm run dev in ./client

Optional local API mode:
  -LocalApi      Run backend via scripts/deploy-server.ps1
  -Dev           (LocalApi only) pass through to deploy-server.ps1
  -NoDocker      (LocalApi only) pass through to deploy-server.ps1
  -RefreshDeps   (LocalApi only) pass through to deploy-server.ps1

Examples:
  .\scripts\deploy-all.ps1
  .\scripts\deploy-all.ps1 -LocalApi -Dev
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$serverScript = Join-Path $PSScriptRoot 'deploy-server.ps1'
$clientDir = Join-Path $repoRoot 'client'
$envFile = Join-Path $repoRoot '.env'

if ($LocalApi -and -not (Test-Path $serverScript)) {
    throw "Missing server script: $serverScript"
}

if (-not $LocalApi -and ($Dev -or $NoDocker -or $RefreshDeps)) {
    throw 'Use -LocalApi when passing -Dev, -NoDocker, or -RefreshDeps.'
}

if (-not (Test-Path (Join-Path $clientDir 'package.json'))) {
    throw "Missing client package.json: $(Join-Path $clientDir 'package.json')"
}

function Get-NpmExecutable {
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmCmd) {
        return $npmCmd.Source
    }

    $npmPs1 = Get-Command npm -ErrorAction SilentlyContinue
    if ($npmPs1 -and $npmPs1.Source) {
        $candidate = Join-Path (Split-Path $npmPs1.Source -Parent) 'npm.cmd'
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw 'npm is required to run the client. Install Node.js/npm.'
}

$npmExecutable = Get-NpmExecutable

function Get-EnvValue([string]$Key, [string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    $line = Select-String -Path $Path -Pattern "^\s*$Key\s*=" | Select-Object -First 1
    if (-not $line) { return $null }
    $value = ($line.Line -split '=', 2)[1].Trim()
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return $value
}

$apiHost = if ($env:API_HOST) { $env:API_HOST } else { Get-EnvValue -Key 'API_HOST' -Path $envFile }
if (-not $apiHost) { $apiHost = '127.0.0.1' }

$apiPort = if ($env:API_PORT) { $env:API_PORT } else { Get-EnvValue -Key 'API_PORT' -Path $envFile }
if (-not $apiPort) { $apiPort = '8010' }

$clientHost = if ($env:CLIENT_HOST) { $env:CLIENT_HOST } else { Get-EnvValue -Key 'CLIENT_HOST' -Path $envFile }
if (-not $clientHost) { $clientHost = '127.0.0.1' }

$clientPort = if ($env:CLIENT_PORT) { $env:CLIENT_PORT } else { Get-EnvValue -Key 'CLIENT_PORT' -Path $envFile }
if (-not $clientPort) { $clientPort = '3007' }

$clientApiBase = $env:NEXT_PUBLIC_API_URL
if ([string]::IsNullOrWhiteSpace($clientApiBase)) {
    $clientApiBase = $env:NEXT_PUBLIC_BACKEND_BASE_URL
}
if ([string]::IsNullOrWhiteSpace($clientApiBase)) {
    $clientApiBase = Get-EnvValue -Key 'NEXT_PUBLIC_API_URL' -Path $envFile
}
if ([string]::IsNullOrWhiteSpace($clientApiBase)) {
    $clientApiBase = Get-EnvValue -Key 'NEXT_PUBLIC_BACKEND_BASE_URL' -Path $envFile
}
if ([string]::IsNullOrWhiteSpace($clientApiBase)) {
    $clientApiBase = "http://${apiHost}:${apiPort}"
}

function Stop-ProcessTree([int]$ProcessId) {
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-ProcessTree -ProcessId $_.ProcessId }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Start-NpmDevProcess {
    param(
        [string]$WorkingDirectory,
        [hashtable]$Environment
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $npmExecutable
    $psi.Arguments = 'run dev'
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false

    foreach ($key in $Environment.Keys) {
        $psi.EnvironmentVariables[$key] = [string]$Environment[$key]
    }

    return [System.Diagnostics.Process]::Start($psi)
}

$composeProcess = $null
$serverProcess = $null
$clientProcess = $null

function Stop-ChildProcesses {
    if ($composeProcess -and -not $composeProcess.HasExited) {
        Stop-ProcessTree -ProcessId $composeProcess.Id
    }
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-ProcessTree -ProcessId $serverProcess.Id
    }
    if ($clientProcess -and -not $clientProcess.HasExited) {
        Stop-ProcessTree -ProcessId $clientProcess.Id
    }
}

try {
    if ($LocalApi) {
        Write-Host 'Starting backend via local API script...'
        $serverArgs = @(
            '-NoProfile'
            '-ExecutionPolicy', 'Bypass'
            '-File', $serverScript
        )
        if ($Dev) { $serverArgs += '-Dev' }
        if ($NoDocker) { $serverArgs += '-NoDocker' }
        if ($RefreshDeps) { $serverArgs += '-RefreshDeps' }

        $serverProcess = Start-Process -FilePath 'powershell.exe' `
            -ArgumentList $serverArgs `
            -WorkingDirectory $repoRoot `
            -PassThru `
            -NoNewWindow
    }
    else {
        Write-Host 'Starting backend via docker compose (api + worker + status-poller)...'
        $composeProcess = Start-Process -FilePath 'docker' `
            -ArgumentList @('compose', 'up', '--build') `
            -WorkingDirectory $repoRoot `
            -PassThru `
            -NoNewWindow

        $apiBaseUrl = "http://${apiHost}:${apiPort}"
        $null = Start-Job -ScriptBlock {
            param($Root, $ApiBase)
            Set-Location $Root
            for ($attempt = 0; $attempt -lt 90; $attempt++) {
                try {
                    Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 2 | Out-Null
                    break
                } catch {
                    Start-Sleep -Seconds 2
                }
            }
            docker compose exec -T api python -c "from app.seed import ensure_seed_admin; user = ensure_seed_admin(sync_password=True); print('Seed admin ready:', user.email)"
        } -ArgumentList $repoRoot.Path, $apiBaseUrl
    }

    Write-Host 'Starting client...'

    $clientProcess = Start-NpmDevProcess -WorkingDirectory $clientDir -Environment @{
        PORT = $clientPort
        HOSTNAME = $clientHost
        NEXT_PUBLIC_API_URL = $clientApiBase
        NEXT_PUBLIC_BACKEND_BASE_URL = $clientApiBase
        NEXT_PUBLIC_API_PORT = $apiPort
    }

    if ($composeProcess) {
        Write-Host "Compose PID: $($composeProcess.Id)"
    }
    else {
        Write-Host "Server PID: $($serverProcess.Id)"
    }
    Write-Host "Client PID: $($clientProcess.Id)"
    Write-Host "API host:port: ${apiHost}:${apiPort}"
    Write-Host "Client host:port: ${clientHost}:${clientPort}"
    Write-Host "Client API base: $clientApiBase"
    $seedUsername = Get-EnvValue -Key 'SEED_ADMIN_USERNAME' -Path $envFile
    if (-not $seedUsername) { $seedUsername = 'admin' }
    $seedPassword = Get-EnvValue -Key 'SEED_ADMIN_PASSWORD' -Path $envFile
    if (-not $seedPassword) { $seedPassword = 'admin-password' }
    Write-Host "Login: $seedUsername / $seedPassword (from .env SEED_ADMIN_*)"
    Write-Host 'Press Ctrl+C to stop both processes.'

    while ($true) {
        $backendExited = if ($composeProcess) { $composeProcess.HasExited } else { $serverProcess.HasExited }
        if ($backendExited -or $clientProcess.HasExited) {
            break
        }
        Start-Sleep -Milliseconds 500
    }

    if ($composeProcess -and $composeProcess.HasExited -and $composeProcess.ExitCode -ne 0) {
        exit $composeProcess.ExitCode
    }
    if ($serverProcess -and $serverProcess.HasExited -and $serverProcess.ExitCode -ne 0) {
        exit $serverProcess.ExitCode
    }
    if ($clientProcess.HasExited -and $clientProcess.ExitCode -ne 0) {
        exit $clientProcess.ExitCode
    }
}
finally {
    Stop-ChildProcesses
}
