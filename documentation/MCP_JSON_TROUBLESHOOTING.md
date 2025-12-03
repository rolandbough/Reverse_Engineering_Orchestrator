# MCP.json Troubleshooting Guide

## Problem: Malformed JSON or Missing Servers

If `mcp.json` becomes malformed or loses MCP server configurations, use these tools to fix it.

## Quick Fix

### Option 1: Format Existing JSON (Recommended)

If JSON is malformed but servers are present:

```powershell
python format_mcp_json.py
```

This will:
- Read the existing `mcp.json`
- Fix formatting issues
- Preserve all existing servers
- Write properly formatted JSON

### Option 2: Repair and Restore Servers

If servers are missing:

```powershell
.\repair_mcp_json.ps1
```

This will:
- Backup existing `mcp.json`
- Restore `ida-pro-mcp` if missing
- Restore `reverse-engineering-orchestrator` if missing
- Format JSON properly

## Common Issues

### Issue 1: PowerShell ConvertTo-Json Formatting

**Problem**: PowerShell's `ConvertTo-Json` creates malformed JSON with extra whitespace.

**Solution**: Use `format_mcp_json.py` to reformat:
```powershell
python format_mcp_json.py
```

### Issue 2: Missing ida-pro-mcp Server

**Problem**: `ida-pro-mcp` server disappeared from config.

**Solution**: Run repair script:
```powershell
.\repair_mcp_json.ps1
```

The script will:
- Detect if `ida-pro-mcp` is installed in venv
- Restore the configuration automatically
- Preserve other servers

### Issue 3: UTF-8 BOM Issues

**Problem**: JSON parsing fails due to Byte Order Mark (BOM).

**Solution**: The Python formatter handles this automatically:
```powershell
python format_mcp_json.py
```

### Issue 4: JSON Validation Errors

**Problem**: Cursor can't parse `mcp.json`.

**Solution**:
1. Run `python format_mcp_json.py` to fix formatting
2. Verify with: `python test_cursor_integration.py`
3. Check JSON manually: `Get-Content $env:USERPROFILE\.cursor\mcp.json`

## Verification

After fixing, verify the configuration:

```powershell
# Check JSON is valid
python test_cursor_integration.py

# List all servers
$config = Get-Content $env:USERPROFILE\.cursor\mcp.json -Raw | ConvertFrom-Json
$config.mcpServers.PSObject.Properties.Name
```

Expected output:
```
✅ Config
✅ Python
✅ Project
✅ All checks passed!

Servers:
  - ida-pro-mcp
  - reverse-engineering-orchestrator
```

## Manual Configuration

If automated tools fail, you can manually edit `mcp.json`:

**Location**: `C:\Users\<username>\.cursor\mcp.json`

**Structure**:
```json
{
  "mcpServers": {
    "ida-pro-mcp": {
      "command": "<venv_path>\\Scripts\\python.exe",
      "args": [
        "<venv_path>\\Lib\\site-packages\\ida_pro_mcp\\server.py"
      ],
      "timeout": 1800,
      "disabled": false,
      "autoApprove": [
        "list_functions",
        "get_function_info",
        "get_metadata"
      ],
      "alwaysAllow": [
        "get_metadata"
      ]
    },
    "reverse-engineering-orchestrator": {
      "command": "<venv_path>\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "<project_path>",
      "timeout": 1800,
      "disabled": false,
      "autoApprove": [
        "detect_re_tool",
        "get_function_info",
        "find_references"
      ],
      "alwaysAllow": [
        "detect_re_tool"
      ]
    }
  }
}
```

## Prevention

To prevent issues:

1. **Always use `format_mcp_json.py`** after manual edits
2. **Use `setup_cursor_mcp.ps1`** instead of manual editing
3. **Backup before changes**: The repair script creates backups automatically
4. **Verify after changes**: Run `python test_cursor_integration.py`

## Tools Reference

### format_mcp_json.py
- **Purpose**: Format JSON properly
- **Usage**: `python format_mcp_json.py [path_to_mcp.json]`
- **What it does**: Reads JSON, validates, reformats with proper indentation

### repair_mcp_json.ps1
- **Purpose**: Restore missing servers and fix JSON
- **Usage**: `.\repair_mcp_json.ps1`
- **What it does**: 
  - Backs up existing config
  - Restores `ida-pro-mcp` if missing
  - Restores `reverse-engineering-orchestrator` if missing
  - Formats JSON properly

### setup_cursor_mcp.ps1
- **Purpose**: Initial setup or update of orchestrator config
- **Usage**: `.\setup_cursor_mcp.ps1`
- **What it does**: 
  - Adds/updates `reverse-engineering-orchestrator`
  - Preserves other servers
  - Formats JSON properly

## Getting Help

If issues persist:

1. Check Cursor logs: Help → Toggle Developer Tools → Console
2. Verify Python paths are correct
3. Check virtual environment is activated
4. Ensure all dependencies are installed
5. Review `documentation/TROUBLESHOOTING.md` for general issues

