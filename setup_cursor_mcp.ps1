# PowerShell script to set up Reverse Engineering Orchestrator in Cursor
# This script helps configure the MCP server in Cursor's mcp.json

param(
    [string]$PythonPath = "",
    [string]$ProjectPath = ""
)

Write-Host "Reverse Engineering Orchestrator - Cursor MCP Setup" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

# Get project root (script location)
if (-not $ProjectPath) {
    $ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$ProjectPath = Resolve-Path $ProjectPath

Write-Host "Project Path: $ProjectPath" -ForegroundColor Green

# Find Python executable
if (-not $PythonPath) {
    # Check for virtual environment
    $venvPython = Join-Path $ProjectPath "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonPath = $venvPython
        Write-Host "Found virtual environment Python: $PythonPath" -ForegroundColor Green
    } else {
        # Use system Python
        $PythonPath = (Get-Command python).Source
        Write-Host "Using system Python: $PythonPath" -ForegroundColor Yellow
    }
} else {
    $PythonPath = Resolve-Path $PythonPath
}

Write-Host "Python Path: $PythonPath`n" -ForegroundColor Green

# Find Cursor config directory
$cursorConfigDir = Join-Path $env:USERPROFILE ".cursor"
$mcpConfigPath = Join-Path $cursorConfigDir "mcp.json"

if (-not (Test-Path $cursorConfigDir)) {
    Write-Host "Creating Cursor config directory: $cursorConfigDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $cursorConfigDir -Force | Out-Null
}

# Read existing config or create new
$config = @{}
if (Test-Path $mcpConfigPath) {
    Write-Host "Reading existing mcp.json..." -ForegroundColor Green
    try {
        # Read and parse JSON, handling UTF-8 BOM
        $jsonContent = Get-Content $mcpConfigPath -Raw -Encoding UTF8
        # Remove BOM if present
        if ($jsonContent.StartsWith([char]0xFEFF)) {
            $jsonContent = $jsonContent.Substring(1)
        }
        $config = $jsonContent | ConvertFrom-Json
    } catch {
        Write-Host "Warning: Could not parse existing mcp.json, creating new one" -ForegroundColor Yellow
        Write-Host "  Error: $_" -ForegroundColor Yellow
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

# Create server config object
$serverConfig = New-Object PSObject
$serverConfig | Add-Member -MemberType NoteProperty -Name "command" -Value $PythonPath
$serverConfig | Add-Member -MemberType NoteProperty -Name "args" -Value @("-m", "src.mcp_server")
$serverConfig | Add-Member -MemberType NoteProperty -Name "cwd" -Value $ProjectPath
$serverConfig | Add-Member -MemberType NoteProperty -Name "timeout" -Value 1800
$serverConfig | Add-Member -MemberType NoteProperty -Name "disabled" -Value $false
$serverConfig | Add-Member -MemberType NoteProperty -Name "autoApprove" -Value @(
    "detect_re_tool",
    "get_function_info",
    "find_references"
)
$serverConfig | Add-Member -MemberType NoteProperty -Name "alwaysAllow" -Value @(
    "detect_re_tool"
)

# Add or update our server config (preserving other servers)
$config.mcpServers | Add-Member -MemberType NoteProperty -Name "reverse-engineering-orchestrator" -Value $serverConfig -Force

# Write config with proper formatting (no BOM)
Write-Host "Writing configuration to: $mcpConfigPath" -ForegroundColor Green
try {
    # Write compact JSON first (PowerShell's ConvertTo-Json has formatting issues)
    $json = $config | ConvertTo-Json -Depth 10 -Compress
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($mcpConfigPath, $json, $utf8NoBom)
    
    # Format using Python for consistent, readable JSON
    $formatScript = Join-Path $ProjectPath "format_mcp_json.py"
    if (Test-Path $formatScript) {
        $pythonExe = Join-Path $ProjectPath "venv\Scripts\python.exe"
        if (-not (Test-Path $pythonExe)) {
            $pythonExe = "python"
        }
        & $pythonExe $formatScript $mcpConfigPath 2>&1 | Out-Null
    }
    
    Write-Host "✅ Configuration saved (preserving existing servers)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error writing config: $_" -ForegroundColor Red
    exit 1
}

# Verify JSON is valid
try {
    $verify = Get-Content $mcpConfigPath -Raw -Encoding UTF8
    if ($verify.StartsWith([char]0xFEFF)) {
        $verify = $verify.Substring(1)
    }
    $null = $verify | ConvertFrom-Json -ErrorAction Stop
    Write-Host "✅ JSON validation passed" -ForegroundColor Green
} catch {
    Write-Host "❌ JSON validation failed: $_" -ForegroundColor Red
    Write-Host "   Run: python format_mcp_json.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ Configuration complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart Cursor completely" -ForegroundColor White
Write-Host "2. The MCP server should start automatically" -ForegroundColor White
Write-Host "3. Try asking: 'What reverse engineering tools are available?'" -ForegroundColor White
Write-Host "`nConfiguration file: $mcpConfigPath" -ForegroundColor Gray

