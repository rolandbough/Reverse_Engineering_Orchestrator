# Quick Start Guide

Get the Reverse Engineering Orchestrator running in Cursor in 5 minutes.

## Prerequisites Check

```bash
# 1. Check Python
python --version  # Should be 3.8+

# 2. Check virtual environment
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS

# 3. Check dependencies
pip list | findstr mcp  # Windows
# or
pip list | grep mcp  # Linux/macOS
```

## Quick Setup

### Option 1: Automated Setup (Windows)

```powershell
.\setup_cursor_mcp.ps1
```

This script will:
- Find your Python executable
- Configure Cursor's `mcp.json`
- Set up the MCP server

### Option 2: Manual Setup

1. **Find your Python path:**
   ```bash
   # In your virtual environment
   where python  # Windows
   which python  # Linux/macOS
   ```

2. **Edit Cursor's mcp.json:**
   - Location: `C:\Users\<username>\.cursor\mcp.json` (Windows)
   - Add configuration (see `documentation/SETUP_CURSOR_MCP.md`)

3. **Restart Cursor**

## Test It Works

### 1. Test MCP Server Locally

```bash
python test_mcp_server.py
```

Expected output:
```
✅ Tool detected: ida_pro (or ghidra)
✅ Adapter initialized successfully
✅ MCP Server test passed!
```

### 2. Test in Cursor

After restarting Cursor, ask the AI:

```
What reverse engineering tools are available? Use detect_re_tool.
```

Or:

```
Decompile the function at address 0x401000
```

## Common Issues

### "No tools detected"

**Solution**: Ensure IDA Pro or Ghidra is installed and detected:
```bash
python test_mcp_server.py
```

### "Cannot connect to IDA Pro"

**Solution**: 
1. Start IDA Pro
2. Load MCP plugin: Edit → Plugins → MCP (Ctrl+Alt+M)
3. Verify RPC server: `python query_ida_functions.py --metadata`

### "MCP server not starting in Cursor"

**Solution**:
1. Check Python path in `mcp.json` is correct
2. Verify `cwd` path is correct
3. Check Cursor's MCP logs for errors

## Next Steps

- Read `documentation/SETUP_CURSOR_MCP.md` for detailed configuration
- Check `documentation/INTEGRATION_STATUS.md` for current status
- Explore available MCP tools in the setup guide

## Getting Help

1. Run test scripts to isolate issues
2. Check documentation in `documentation/` folder
3. Review ADR documents for architecture decisions

