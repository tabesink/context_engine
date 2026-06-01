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
Usage: scripts/deploy-all.ps1 [-LocalApi] [-Dev] [-NoDocker] [-RefreshDeps]

Starts:
  - backend via docker compose (postgres, redis, migrate, api, worker, status-poller)
  - client via npm run dev in ./client

Optional local API mode:
  -LocalApi      Run backend via scripts/deploy-server.ps1
  -Dev           (LocalApi only) pass through to deploy-server.ps1
  -NoDocker      (LocalApi only) pass through to deploy-server.ps1
  -RefreshDeps   Reinstall client npm deps; with -LocalApi, also pass through to deploy-server.ps1

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
$envExampleFile = Join-Path $repoRoot '.env.example'

if ($LocalApi -and -not (Test-Path $serverScript)) {
    throw "Missing server script: $serverScript"
}

if (-not $LocalApi -and ($Dev -or $NoDocker)) {
    throw 'Use -LocalApi when passing -Dev or -NoDocker.'
}

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $envExampleFile)) {
        throw "Missing env template: $envExampleFile"
    }
    Copy-Item $envExampleFile $envFile
    Write-Host "Created .env from .env.example - edit if needed."
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

function Invoke-Npm {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $npmExecutable
    $psi.Arguments = ($Arguments -join ' ')
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $process = [System.Diagnostics.Process]::Start($psi)
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "npm $($Arguments -join ' ') failed with exit code $($process.ExitCode)."
    }
}

function Ensure-ClientDependencies {
    param(
        [string]$WorkingDirectory,
        [switch]$Force
    )

    $nodeModulesDir = Join-Path $WorkingDirectory 'node_modules'
    if ($Force -or -not (Test-Path $nodeModulesDir)) {
        Write-Host 'Installing client npm dependencies...'
        Invoke-Npm -Arguments @('install') -WorkingDirectory $WorkingDirectory
    }
}

function Wait-ForApi {
    param(
        [string]$BaseUrl,
        [int]$TimeoutSeconds = 300
    )

    $healthUrl = "$BaseUrl/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    Write-Host "Waiting for API at $healthUrl ..."

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host 'API is ready.'
                return
            }
        }
        catch {
            # API not ready yet.
        }
        Start-Sleep -Seconds 2
    }

    throw "API did not become ready at $healthUrl within ${TimeoutSeconds}s."
}

function Invoke-ComposeBuild {
    param(
        [string]$WorkingDirectory
    )

    Write-Host 'Building docker compose images...'
    $process = Start-Process -FilePath 'docker' `
        -ArgumentList @('compose', 'build') `
        -WorkingDirectory $WorkingDirectory `
        -Wait `
        -PassThru `
        -NoNewWindow
    if ($process.ExitCode -ne 0) {
        throw "docker compose build failed with exit code $($process.ExitCode)."
    }
}

function Stop-StaleComposeApi {
    param(
        [string]$WorkingDirectory
    )

    $null = Start-Process -FilePath 'docker' `
        -ArgumentList @('compose', 'stop', 'api') `
        -WorkingDirectory $WorkingDirectory `
        -Wait `
        -PassThru `
        -NoNewWindow
}

function Invoke-SeedAdmin {
    param(
        [string]$WorkingDirectory,
        [int]$MaxAttempts = 30
    )

    Write-Host 'Seeding admin user...'
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $process = Start-Process -FilePath 'docker' `
            -ArgumentList @('compose', 'run', '--rm', '--no-deps', 'api', 'python', '-m', 'scripts.seed_admin') `
            -WorkingDirectory $WorkingDirectory `
            -Wait `
            -PassThru `
            -NoNewWindow
        if ($process.ExitCode -eq 0) {
            return
        }
        if ($attempt -lt $MaxAttempts) {
            Start-Sleep -Seconds 2
        }
    }

    throw "seed_admin failed after $MaxAttempts attempts."
}

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
        Invoke-ComposeBuild -WorkingDirectory $repoRoot
        Stop-StaleComposeApi -WorkingDirectory $repoRoot
        $composeProcess = Start-Process -FilePath 'docker' `
            -ArgumentList @('compose', 'up', '--force-recreate') `
            -WorkingDirectory $repoRoot `
            -PassThru `
            -NoNewWindow
    }

    Ensure-ClientDependencies -WorkingDirectory $clientDir -Force:$RefreshDeps

    Wait-ForApi -BaseUrl "http://${apiHost}:${apiPort}"

    if ($composeProcess) {
        Invoke-SeedAdmin -WorkingDirectory $repoRoot
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
