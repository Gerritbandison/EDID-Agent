#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Device Inventory Agent - Intune Silent Installer

.DESCRIPTION
    Silent installation script for deployment via Microsoft Intune.
    Configure API_URL and API_KEY before packaging.
#>

$ErrorActionPreference = "Stop"

# ====== CONFIGURATION - MODIFY BEFORE DEPLOYMENT ======
$ApiUrl = "https://inventory.yourcompany.com"
$ApiKey = "YOUR-API-KEY-HERE"
$CheckInInterval = 1800
# ======================================================

$InstallDir = "$env:ProgramFiles\InventoryAgent"
$DataDir = "$env:ProgramData\InventoryAgent"
$LogDir = "$DataDir\logs"
$ServiceName = "InventoryAgent"

# Log function
function Write-Log {
    param([string]$Message)
    $logFile = "$env:TEMP\InventoryAgent_Install.log"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
    Write-Host $Message
}

Write-Log "Starting Device Inventory Agent installation..."

try {
    # Check/Install Python
    $pythonPath = $null
    $pythonPaths = @(
        "python",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
    )

    foreach ($path in $pythonPaths) {
        try {
            $null = & $path --version 2>&1
            $pythonPath = $path
            break
        } catch {
            continue
        }
    }

    if (-not $pythonPath) {
        Write-Log "Python not found. Please ensure Python 3.10+ is installed."
        exit 1
    }

    Write-Log "Using Python: $pythonPath"

    # Stop existing service
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Log "Stopping existing service..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # Create directories
    Write-Log "Creating directories..."
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

    # Copy agent files (assuming they're in the same directory as this script)
    Write-Log "Copying agent files..."
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Copy-Item -Path "$scriptDir\agent\*" -Destination $InstallDir -Recurse -Force

    # Install dependencies
    Write-Log "Installing Python dependencies..."
    & $pythonPath -m pip install requests psutil pywin32 --quiet

    # Create configuration
    Write-Log "Creating configuration..."
    $config = @{
        api_url = $ApiUrl
        api_key = $ApiKey
        check_in_interval = $CheckInInterval
        max_retries = 3
        retry_delay = 5
        request_timeout = 30
        log_level = "INFO"
    }
    $config | ConvertTo-Json | Set-Content -Path "$DataDir\config.json"

    # Install service
    Write-Log "Installing Windows service..."
    & $pythonPath "$InstallDir\service_windows.py" install

    # Configure service
    Set-Service -Name $ServiceName -StartupType Automatic

    # Start service
    Write-Log "Starting service..."
    Start-Service -Name $ServiceName

    Write-Log "Installation completed successfully!"
    exit 0

} catch {
    Write-Log "Installation failed: $_"
    exit 1
}
