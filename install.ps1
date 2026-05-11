# Kalpixk Agent Installer (Windows)
# ATLATL-ORDNANCE Protocol v5.0

$ErrorActionPreference = "Stop"

Write-Host "🏹 Kalpixk Agent Installer Starting..." -ForegroundColor Cyan

# Check for Administrator privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run PowerShell as Administrator."
    exit 1
}

# 1. Download binary
$binaryUrl = "https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps/releases/latest/download/kalpixk-agent-windows.exe"
$installDir = "C:\Program Files\kalpixk-agent"
$installPath = Join-Path $installDir "kalpixk-agent.exe"

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Force -Path $installDir
}

Write-Host "Downloading binary from $binaryUrl..."
Invoke-WebRequest -Uri $binaryUrl -OutFile $installPath

# 2. Prompt for configuration
$apiUrl = Read-Host "Enter API_URL [http://localhost:8000]"
if ([string]::IsNullOrWhiteSpace($apiUrl)) { $apiUrl = "http://localhost:8000" }

$apiKey = Read-Host "Enter API_KEY"

# 3. Create configuration file
$configPath = Join-Path $installDir "kalpixk-agent.toml"
Write-Host "Creating configuration at $configPath..."

$configContent = @"
api_url = "$apiUrl"
api_key = "$apiKey"
watch_dir = "C:\\Users"
interval_secs = 2
log_file = "kalpixk-alerts.log"
"@

$configContent | Out-File -FilePath $configPath -Encoding utf8

# 4. Register Windows Service
Write-Host "Registering Windows Service..."
$serviceName = "kalpixk-agent"

# Check if service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Stopping and removing existing service..."
    Stop-Service -Name $serviceName -ErrorAction SilentlyContinue
    & sc.exe delete $serviceName
}

$binPath = "`"$installPath`" --config `"$configPath`""
& sc.exe create $serviceName binPath= $binPath start= auto
& sc.exe description $serviceName "Kalpixk Agent - OS Monitoring"

# 5. Start service
Write-Host "Starting kalpixk-agent service..."
Start-Service -Name $serviceName

Write-Host "✅ Kalpixk Agent installed and started successfully!" -ForegroundColor Green
Get-Service -Name $serviceName
