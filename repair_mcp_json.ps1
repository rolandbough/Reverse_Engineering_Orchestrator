# Repair script for mcp.json - Restores missing MCP servers
# This script fixes malformed mcp.json and restores ida-pro-mcp if needed

param(
    [switch]$Backup = $true
)

Write-Host "MCP.json Repair Script" -ForegroundColor Cyan
Write-Host "=====================`n" -ForegroundColor Cyan

$mcpConfigPath = Join-Path $env:USERPROFILE ".cursor\mcp.json"

# Backup existing file
if ($Backup -and (Test-Path $mcpConfigPath)) {
    $backupPath = "$mcpConfigPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $mcpConfigPath $backupPath
    Write-Host "Backup created: $backupPath" -ForegroundColor Green
}

# Read current config
$config = @{}
if (Test-Path $mcpConfigPath) {
    Write-Host "Reading existing mcp.json..." -ForegroundColor Green
    try {
        $jsonContent = Get-Content $mcpConfigPath -Raw -Encoding UTF8
        # Remove BOM if present
        if ($jsonContent.StartsWith([char]0xFEFF)) {
            $jsonContent = $jsonContent.Substring(1)
        }
        $config = $jsonContent | ConvertFrom-Json -ErrorAction Stop
        Write-Host "✅ Successfully parsed existing config" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Error parsing existing config: $_" -ForegroundColor Yellow
        Write-Host "   Creating new config structure..." -ForegroundColor Yellow
        $config = New-Object PSObject
    }
} else {
    Write-Host "Creating new mcp.json..." -ForegroundColor Green
    $config = New-Object PSObject
}

# Ensure mcpServers exists
if (-not $config.PSObject.Properties['mcpServers']) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value (New-Object PSObject) -Force
}

# Get current servers
$currentServers = $config.mcpServers
Write-Host "`nCurrent servers:" -ForegroundColor Cyan
foreach ($serverName in $currentServers.PSObject.Properties.Name) {
    Write-Host "  - $serverName" -ForegroundColor White
}

# Check for ida-pro-mcp and restore if missing
$venvPath = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "venv"
$idaProMcpPath = Join-Path $venvPath "Lib\site-packages\ida_pro_mcp\server.py"

if (-not $currentServers.PSObject.Properties['ida-pro-mcp']) {
    Write-Host "`n⚠️  ida-pro-mcp server not found!" -ForegroundColor Yellow
    
    if (Test-Path $idaProMcpPath) {
        Write-Host "   Found ida-pro-mcp installation, restoring..." -ForegroundColor Green
        
        $pythonExe = Join-Path $venvPath "Scripts\python.exe"
        if (-not (Test-Path $pythonExe)) {
            # Try to find Python in venv
            $pythonExe = (Get-Command python).Source
            Write-Host "   Using system Python: $pythonExe" -ForegroundColor Yellow
        }
        
        $idaConfig = New-Object PSObject
        $idaConfig | Add-Member -MemberType NoteProperty -Name "command" -Value $pythonExe
        $idaConfig | Add-Member -MemberType NoteProperty -Name "args" -Value @($idaProMcpPath)
        $idaConfig | Add-Member -MemberType NoteProperty -Name "timeout" -Value 1800
        $idaConfig | Add-Member -MemberType NoteProperty -Name "disabled" -Value $false
        $idaConfig | Add-Member -MemberType NoteProperty -Name "autoApprove" -Value @(
            "list_functions",
            "get_function_info",
            "get_metadata"
        )
        $idaConfig | Add-Member -MemberType NoteProperty -Name "alwaysAllow" -Value @(
            "get_metadata"
        )
        
        $currentServers | Add-Member -MemberType NoteProperty -Name "ida-pro-mcp" -Value $idaConfig -Force
        Write-Host "   ✅ Restored ida-pro-mcp configuration" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  ida-pro-mcp not found in venv, skipping..." -ForegroundColor Yellow
        Write-Host "   Run: pip install ida-pro-mcp" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✅ ida-pro-mcp already configured" -ForegroundColor Green
}

# Ensure reverse-engineering-orchestrator is properly configured
$projectPath = Split-Path $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectPath "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $venvPython = (Get-Command python).Source
}

if (-not $currentServers.PSObject.Properties['reverse-engineering-orchestrator']) {
    Write-Host "`n⚠️  reverse-engineering-orchestrator not found, adding..." -ForegroundColor Yellow
} else {
    Write-Host "`n✅ reverse-engineering-orchestrator already configured" -ForegroundColor Green
}

# Update or add reverse-engineering-orchestrator
$reoConfig = New-Object PSObject
$reoConfig | Add-Member -MemberType NoteProperty -Name "command" -Value $venvPython
$reoConfig | Add-Member -MemberType NoteProperty -Name "args" -Value @("-m", "src.mcp_server")
$reoConfig | Add-Member -MemberType NoteProperty -Name "cwd" -Value $projectPath
$reoConfig | Add-Member -MemberType NoteProperty -Name "timeout" -Value 1800
$reoConfig | Add-Member -MemberType NoteProperty -Name "disabled" -Value $false
$reoConfig | Add-Member -MemberType NoteProperty -Name "autoApprove" -Value @(
    "detect_re_tool",
    "get_function_info",
    "find_references"
)
$reoConfig | Add-Member -MemberType NoteProperty -Name "alwaysAllow" -Value @(
    "detect_re_tool"
)

$currentServers | Add-Member -MemberType NoteProperty -Name "reverse-engineering-orchestrator" -Value $reoConfig -Force

# Write fixed config
Write-Host "`nWriting fixed configuration..." -ForegroundColor Green
try {
    # Write compact JSON first (PowerShell's ConvertTo-Json has formatting issues)
    $json = $config | ConvertTo-Json -Depth 10 -Compress
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($mcpConfigPath, $json, $utf8NoBom)
    
    # Format using Python for consistent, readable JSON
    $formatScript = Join-Path $projectPath "format_mcp_json.py"
    if (Test-Path $formatScript) {
        $pythonExe = Join-Path $projectPath "venv\Scripts\python.exe"
        if (-not (Test-Path $pythonExe)) {
            $pythonExe = "python"
        }
        & $pythonExe $formatScript $mcpConfigPath 2>&1 | Out-Null
        Write-Host "✅ Configuration formatted with Python" -ForegroundColor Green
    } else {
        Write-Host "⚠️  format_mcp_json.py not found, using raw JSON" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Configuration saved successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error writing config: $_" -ForegroundColor Red
    Write-Host "   Run: python format_mcp_json.py" -ForegroundColor Yellow
    exit 1
}

# Verify JSON is valid
Write-Host "`nVerifying JSON..." -ForegroundColor Cyan
try {
    $verify = Get-Content $mcpConfigPath -Raw -Encoding UTF8
    if ($verify.StartsWith([char]0xFEFF)) {
        $verify = $verify.Substring(1)
    }
    $null = $verify | ConvertFrom-Json -ErrorAction Stop
    Write-Host "✅ JSON is valid" -ForegroundColor Green
} catch {
    Write-Host "❌ JSON validation failed: $_" -ForegroundColor Red
    Write-Host "   File content preview:" -ForegroundColor Yellow
    Get-Content $mcpConfigPath -TotalCount 10 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    exit 1
}

# Show final configuration
Write-Host "`nFinal configuration:" -ForegroundColor Cyan
$finalConfig = Get-Content $mcpConfigPath -Raw -Encoding UTF8
if ($finalConfig.StartsWith([char]0xFEFF)) {
    $finalConfig = $finalConfig.Substring(1)
}
$final = $finalConfig | ConvertFrom-Json
Write-Host "  Servers configured:" -ForegroundColor White
foreach ($serverName in $final.mcpServers.PSObject.Properties.Name) {
    Write-Host "    - $serverName" -ForegroundColor Green
}

Write-Host "`n✅ Repair complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart Cursor completely" -ForegroundColor White
Write-Host "2. Verify MCP servers are loaded" -ForegroundColor White
Write-Host "3. Run: python test_cursor_integration.py" -ForegroundColor White

