# PowerShell script for automated commits
# Can be scheduled using Windows Task Scheduler

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Using Python: $pythonVersion"
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Run the automation script
Write-Host "Running automation script..." -ForegroundColor Green
python version_manager.py --auto

# Log the execution
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "automation.log" -Value "[$timestamp] Automation script executed"

Write-Host "Automation complete!" -ForegroundColor Green

