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
        $config = Get-Content $mcpConfigPath -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    } catch {
        Write-Host "Warning: Could not parse existing mcp.json, creating new one" -ForegroundColor Yellow
        $config = @{}
    }
} else {
    Write-Host "Creating new mcp.json..." -ForegroundColor Green
    $config = @{}
}

# Ensure mcpServers exists
if (-not $config.mcpServers) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value @{} -Force
}

# Add or update our server config
$serverConfig = @{
    command = $PythonPath
    args = @("-m", "src.mcp_server")
    cwd = $ProjectPath
    timeout = 1800
    disabled = $false
    autoApprove = @(
        "detect_re_tool",
        "get_function_info",
        "find_references"
    )
    alwaysAllow = @(
        "detect_re_tool"
    )
}

$config.mcpServers."reverse-engineering-orchestrator" = $serverConfig

# Write config
Write-Host "Writing configuration to: $mcpConfigPath" -ForegroundColor Green
$config | ConvertTo-Json -Depth 10 | Set-Content $mcpConfigPath -Encoding UTF8

Write-Host "`n✅ Configuration complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart Cursor completely" -ForegroundColor White
Write-Host "2. The MCP server should start automatically" -ForegroundColor White
Write-Host "3. Try asking: 'What reverse engineering tools are available?'" -ForegroundColor White
Write-Host "`nConfiguration file: $mcpConfigPath" -ForegroundColor Gray

