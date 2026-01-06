<#
.SYNOPSIS
    Intune Detection Script for Device Inventory Agent

.DESCRIPTION
    Returns exit code 0 if the agent is properly installed and running.
    Used by Intune to detect if the application is installed.
#>

$ServiceName = "InventoryAgent"
$InstallDir = "$env:ProgramFiles\InventoryAgent"
$ConfigFile = "$env:ProgramData\InventoryAgent\config.json"

# Check if installation directory exists
if (-not (Test-Path $InstallDir)) {
    Write-Host "Installation directory not found"
    exit 1
}

# Check if main agent file exists
if (-not (Test-Path "$InstallDir\agent.py")) {
    Write-Host "Agent files not found"
    exit 1
}

# Check if configuration exists
if (-not (Test-Path $ConfigFile)) {
    Write-Host "Configuration file not found"
    exit 1
}

# Check if service exists and is running
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "Service not installed"
    exit 1
}

if ($service.Status -ne "Running") {
    Write-Host "Service not running"
    exit 1
}

# All checks passed
Write-Host "Device Inventory Agent is installed and running"
exit 0
