#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Device Inventory Agent - Windows Uninstaller

.DESCRIPTION
    Removes the Device Inventory Agent service and files.

.PARAMETER KeepConfig
    Keep configuration files when uninstalling.
#>

param(
    [switch]$KeepConfig
)

$ErrorActionPreference = "Stop"

$InstallDir = "$env:ProgramFiles\InventoryAgent"
$DataDir = "$env:ProgramData\InventoryAgent"
$ServiceName = "InventoryAgent"

Write-Host "Device Inventory Agent - Uninstaller" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host ""

# Stop and remove service
Write-Host "Stopping service..."
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    Write-Host "Removing service..."

    # Find Python
    $pythonPath = "python"
    try {
        & $pythonPath "$InstallDir\service_windows.py" remove
    } catch {
        # Fallback: use sc.exe
        sc.exe delete $ServiceName
    }
}

# Remove installation directory
if (Test-Path $InstallDir) {
    Write-Host "Removing installation files..."
    Remove-Item -Path $InstallDir -Recurse -Force
}

# Remove data directory (unless KeepConfig)
if (-not $KeepConfig) {
    if (Test-Path $DataDir) {
        Write-Host "Removing configuration and data..."
        Remove-Item -Path $DataDir -Recurse -Force
    }
} else {
    Write-Host "Keeping configuration files at: $DataDir"
}

Write-Host ""
Write-Host "Uninstallation complete!" -ForegroundColor Green
