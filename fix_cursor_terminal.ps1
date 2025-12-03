# Script to help diagnose and fix Cursor terminal detection issues

Write-Host "Cursor Terminal Detection Diagnostic" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Check PowerShell version
Write-Host "PowerShell Version:" -ForegroundColor Green
$PSVersionTable | Format-List

# Check prompt
Write-Host "`nCurrent Prompt:" -ForegroundColor Green
Write-Host "  Function: $($PROMPT)"
Write-Host "  Test output: $(prompt)"

# Check profile
Write-Host "`nPowerShell Profile:" -ForegroundColor Green
if (Test-Path $PROFILE) {
    Write-Host "  Profile exists: $PROFILE"
    Write-Host "  Profile size: $((Get-Item $PROFILE).Length) bytes"
} else {
    Write-Host "  No profile found at: $PROFILE"
}

# Check execution policy
Write-Host "`nExecution Policy:" -ForegroundColor Green
$policy = Get-ExecutionPolicy
Write-Host "  Current: $policy"
if ($policy -eq "Restricted") {
    Write-Host "  ⚠️  Restricted policy may cause issues" -ForegroundColor Yellow
    Write-Host "  Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
}

# Check for background jobs
Write-Host "`nBackground Jobs:" -ForegroundColor Green
$jobs = Get-Job
if ($jobs) {
    Write-Host "  Found $($jobs.Count) background jobs:" -ForegroundColor Yellow
    $jobs | Format-Table
} else {
    Write-Host "  No background jobs"
}

# Check for hanging Python processes
Write-Host "`nPython Processes:" -ForegroundColor Green
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "  Found $($pythonProcs.Count) Python processes:" -ForegroundColor Yellow
    $pythonProcs | Format-Table Id, ProcessName, StartTime
} else {
    Write-Host "  No Python processes running"
}

# Recommendations
Write-Host "`nRecommendations:" -ForegroundColor Cyan
Write-Host "1. Ensure prompt ends with '> ' or '$ '" -ForegroundColor White
Write-Host "2. Check Cursor settings for terminal configuration" -ForegroundColor White
Write-Host "3. Try using -NoProfile flag in terminal settings" -ForegroundColor White
Write-Host "4. Restart Cursor if issues persist" -ForegroundColor White

Write-Host "`nCursor Settings Location:" -ForegroundColor Cyan
Write-Host "  File → Preferences → Settings → Search 'terminal'" -ForegroundColor White

