# Troubleshooting Guide

## Common Issues and Solutions

### Terminal Detection Issues

**Problem**: Cursor doesn't detect when terminal commands finish.

**Symptoms**:
- Terminal shows prompt but Cursor still thinks command is running
- Waiting for commands that have already completed
- Terminal appears "stuck"

**Solutions**:

1. **Check PowerShell Prompt**:
   ```powershell
   # Test if prompt is standard
   prompt
   # Should end with "> " or similar
   ```

2. **Use -NoProfile Flag**:
   - Cursor Settings → Terminal
   - Set PowerShell args to: `["-NoProfile"]`
   - This avoids custom prompts that confuse detection

3. **Reset Terminal**:
   - Kill terminal: Ctrl+Shift+`
   - Or: Terminal → Kill Terminal
   - Open new terminal

4. **Check for Background Jobs**:
   ```powershell
   Get-Job
   # If any found, remove with:
   Remove-Job *
   ```

5. **Manual Wake-up**:
   - Press Enter in terminal
   - Or press Ctrl+C to cancel

6. **Use Command Prompt Instead**:
   - Change default terminal to Command Prompt
   - Often has better detection

**Configuration** (add to Cursor settings.json):
```json
{
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": ["-NoProfile"]
    }
  }
}
```

### MCP Server Not Starting

**Problem**: MCP server doesn't start in Cursor.

**Solutions**:
1. Check Python path in `mcp.json`
2. Verify virtual environment is correct
3. Check `cwd` path is correct
4. Look at Cursor's MCP logs
5. Run `python test_cursor_integration.py` to verify config

### Tool Not Detected

**Problem**: "No reverse engineering tools detected"

**Solutions**:
1. Set environment variables:
   - `IDA_PATH` for IDA Pro
   - `GHIDRA_INSTALL_DIR` for Ghidra
2. Run `python test_mcp_server.py` to verify detection
3. Check tool installation paths

### IDA Pro Connection Failed

**Problem**: "Cannot connect to IDA Pro RPC server"

**Solutions**:
1. Ensure IDA Pro is running
2. Load MCP plugin: Edit → Plugins → MCP (Ctrl+Alt+M)
3. Verify RPC server: `python query_ida_functions.py --metadata`
4. Check firewall isn't blocking port 13337

### Visual Analyzer Not Available

**Problem**: "Visual analyzer not available"

**Solutions**:
1. Install dependencies: `pip install opencv-python mss numpy`
2. Verify installation: `python test_visual_analyzer.py`
3. Check for import errors in Cursor logs

### Import Errors

**Problem**: Module import failures

**Solutions**:
1. Ensure virtual environment is activated
2. Install missing dependencies: `pip install -r requirements.txt`
3. Check Python path in Cursor settings
4. Verify `src/` is in Python path

### JSON Parsing Errors

**Problem**: "Unexpected UTF-8 BOM" or JSON decode errors

**Solutions**:
1. Files may have BOM (Byte Order Mark)
2. Use `utf-8-sig` encoding when reading
3. Or remove BOM: `Get-Content file.json | Set-Content file.json -Encoding UTF8`

## Getting Help

1. **Check Logs**:
   - Cursor: Help → Toggle Developer Tools → Console
   - Python: Check for tracebacks

2. **Run Tests**:
   - `python test_mcp_server.py` - Test MCP server
   - `python test_visual_analyzer.py` - Test visual analyzer
   - `python test_cursor_integration.py` - Test Cursor config

3. **Verify Configuration**:
   - Check `mcp.json` syntax
   - Verify paths are correct
   - Check environment variables

4. **Documentation**:
   - `documentation/SETUP_CURSOR_MCP.md` - Setup guide
   - `documentation/INTEGRATION_STATUS.md` - Current status
   - `QUICK_START.md` - Quick reference

