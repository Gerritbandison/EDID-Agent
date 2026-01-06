#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Device Inventory Agent - Windows Installer

.DESCRIPTION
    Installs the Device Inventory Agent as a Windows Service.

.PARAMETER ApiUrl
    The URL of the inventory API server.

.PARAMETER ApiKey
    The API key for authentication.

.PARAMETER CheckInInterval
    Check-in interval in seconds (default: 1800).

.PARAMETER Silent
    Run in silent mode (no prompts).

.EXAMPLE
    .\install.ps1 -ApiUrl "https://inventory.company.com" -ApiKey "your-key" -Silent
#>

param(
    [string]$ApiUrl = "",
    [string]$ApiKey = "",
    [int]$CheckInInterval = 1800,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

# Configuration
$InstallDir = "$env:ProgramFiles\InventoryAgent"
$DataDir = "$env:ProgramData\InventoryAgent"
$LogDir = "$DataDir\logs"
$ServiceName = "InventoryAgent"
$ServiceDisplayName = "Device Inventory Agent"

Write-Host "Device Inventory Agent - Windows Installer" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# Check Python
$pythonPath = $null
$pythonPaths = @(
    "python",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe"
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
    Write-Host "Python 3 is required but not found." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/"
    exit 1
}

Write-Host "Found Python: $pythonPath"

# Get configuration if not silent
if (-not $Silent) {
    if (-not $ApiUrl) {
        $ApiUrl = Read-Host "API Server URL [http://localhost:5000]"
        if (-not $ApiUrl) { $ApiUrl = "http://localhost:5000" }
    }

    if (-not $ApiKey) {
        $ApiKey = Read-Host "API Key"
    }

    $intervalInput = Read-Host "Check-in interval (seconds) [$CheckInInterval]"
    if ($intervalInput) { $CheckInInterval = [int]$intervalInput }
}

# Stop existing service
Write-Host ""
Write-Host "Stopping existing service if running..."
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Create directories
Write-Host "Creating directories..."
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Copy files
Write-Host "Copying agent files..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentDir = Split-Path -Parent (Split-Path -Parent $scriptDir)

Copy-Item -Path "$agentDir\src\*" -Destination $InstallDir -Recurse -Force
Copy-Item -Path "$agentDir\requirements.txt" -Destination $InstallDir -Force

# Install dependencies
Write-Host "Installing Python dependencies..."
& $pythonPath -m pip install -r "$InstallDir\requirements.txt" --quiet

# Install pywin32 for service support
& $pythonPath -m pip install pywin32 --quiet

# Create configuration
Write-Host "Creating configuration..."
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

# Install Windows service
Write-Host "Installing Windows service..."
& $pythonPath "$InstallDir\service_windows.py" install

# Set service to auto-start
Set-Service -Name $ServiceName -StartupType Automatic

# Start service
Write-Host "Starting service..."
Start-Service -Name $ServiceName

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Service status:"
Get-Service -Name $ServiceName | Format-Table Name, Status, StartType

Write-Host ""
Write-Host "Configuration: $DataDir\config.json"
Write-Host "Logs: $LogDir\"
