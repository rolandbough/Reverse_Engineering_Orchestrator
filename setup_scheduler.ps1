# PowerShell script to set up Windows Task Scheduler for automated commits
# Run this script as Administrator to set up scheduled automation

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$automateScript = Join-Path $scriptPath "automate.ps1"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Warning: This script should be run as Administrator for best results" -ForegroundColor Yellow
}

# Task Scheduler settings
$taskName = "ReverseEngineeringOrchestrator-AutoCommit"
$taskDescription = "Automated versioning and commit system for Reverse Engineering Orchestrator"

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the scheduled task
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$automateScript`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 60) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Write-Host "Creating scheduled task: $taskName" -ForegroundColor Green
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -User $env:USERNAME

Write-Host "Scheduled task created successfully!" -ForegroundColor Green
Write-Host "Task will run every 60 minutes" -ForegroundColor Cyan
Write-Host "You can view/manage the task in Task Scheduler (taskschd.msc)" -ForegroundColor Cyan

