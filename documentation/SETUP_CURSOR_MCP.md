# Setting Up Reverse Engineering Orchestrator in Cursor

This guide explains how to configure the Reverse Engineering Orchestrator MCP server in Cursor IDE.

## Prerequisites

- ✅ Python 3.8+ installed
- ✅ Virtual environment created and activated
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ IDA Pro or Ghidra installed and detected

## Installation Steps

### 1. Verify MCP Server Works

First, test that the MCP server can start:

```bash
# From project root
python -m src.mcp_server
```

You should see the server initialize. Press Ctrl+C to stop it.

### 2. Locate Cursor MCP Configuration

Cursor stores MCP configuration in:
- **Windows**: `C:\Users\<username>\.cursor\mcp.json`
- **macOS**: `~/.cursor/mcp.json`
- **Linux**: `~/.cursor/mcp.json`

### 3. Add MCP Server Configuration

Open `mcp.json` and add the Reverse Engineering Orchestrator server:

```json
{
  "mcpServers": {
    "reverse-engineering-orchestrator": {
      "command": "<path_to_python>",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "<path_to_project_root>",
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

### 4. Configuration Details

#### Windows Example

```json
{
  "mcpServers": {
    "reverse-engineering-orchestrator": {
      "command": "W:\\_Projects\\Dev\\Reverse_Engineering_Orchestrator\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "W:\\_Projects\\Dev\\Reverse_Engineering_Orchestrator",
      "timeout": 1800,
      "disabled": false
    }
  }
}
```

#### Using Environment Variables

You can also use environment variables for paths:

```json
{
  "mcpServers": {
    "reverse-engineering-orchestrator": {
      "command": "${env:VIRTUAL_ENV}\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "${workspaceFolder}",
      "timeout": 1800
    }
  }
}
```

### 5. Restart Cursor

After adding the configuration:
1. **Close Cursor completely**
2. **Reopen Cursor**
3. The MCP server should start automatically

### 6. Verify Connection

To verify the MCP server is connected:

1. Open Cursor
2. Check the MCP status (usually in status bar or settings)
3. Try asking the AI: "What reverse engineering tools are available?"

## Available MCP Tools

Once configured, the following tools are available:

### Core Tools

- **`detect_re_tool`** - Detect and select available tool (IDA Pro or Ghidra)
  - Parameters: `preferred_tool` (optional: "ida" or "ghidra")

- **`load_binary`** - Load a binary file for analysis
  - Parameters: `binary_path` (required), `project_name` (optional)

- **`decompile_function`** - Decompile function at address
  - Parameters: `address` (required, hex string like "0x401000")

- **`get_function_info`** - Get function information at address
  - Parameters: `address` (required, hex string)

- **`find_references`** - Find references to address
  - Parameters: `address` (required, hex string)

- **`read_memory`** - Read memory at address
  - Parameters: `address` (required), `size` (required, bytes)

- **`set_breakpoint`** - Set breakpoint (IDA Pro only)
  - Parameters: `address` (required), `type` (required: "software", "hardware", etc.)

### Resources

- **`reo://tool_status`** - Current tool status and connection info

## Usage Examples

### Example 1: Detect Available Tools

Ask Cursor AI:
```
What reverse engineering tools are available? Use detect_re_tool.
```

### Example 2: Decompile a Function

```
Decompile the function at address 0x401000 using the detect_re_tool first.
```

### Example 3: Find References

```
Find all references to address 0x404000 in the current binary.
```

### Example 4: Get Function Information

```
Get information about the function at address 0x401000.
```

## Troubleshooting

### MCP Server Not Starting

**Problem**: Server doesn't start in Cursor

**Solutions**:
1. Check Python path is correct in `mcp.json`
2. Verify virtual environment is activated
3. Check `cwd` path is correct
4. Look for errors in Cursor's MCP logs

### Tool Not Detected

**Problem**: "No reverse engineering tools detected"

**Solutions**:
1. Ensure IDA Pro or Ghidra is installed
2. Check environment variables:
   - `IDA_PATH` for IDA Pro
   - `GHIDRA_INSTALL_DIR` for Ghidra
3. Run `python test_mcp_server.py` to verify detection

### IDA Pro Connection Failed

**Problem**: "Cannot connect to IDA Pro RPC server"

**Solutions**:
1. Ensure IDA Pro is running
2. Verify MCP plugin is loaded (Edit → Plugins → MCP)
3. Check RPC server is running on port 13337
4. Test with: `python query_ida_functions.py --metadata`

### Ghidra Script Execution Failed

**Problem**: "pyGhidraRun not found"

**Solutions**:
1. Verify Ghidra is installed in `tools/ghidra/`
2. Check `tools/ghidra/support/pyGhidraRun.bat` exists (Windows)
3. Set `GHIDRA_INSTALL_DIR` environment variable

### Permission Errors

**Problem**: Permission denied when executing scripts

**Solutions**:
1. Ensure Python executable has proper permissions
2. Check file paths are accessible
3. On Windows, run Cursor as administrator if needed

## Advanced Configuration

### Custom RPC URL for IDA Pro

Set environment variable:
```bash
# Windows PowerShell
$env:IDA_RPC_URL = "http://127.0.0.1:13337"

# Or in mcp.json, add env section:
{
  "mcpServers": {
    "reverse-engineering-orchestrator": {
      "command": "...",
      "args": [...],
      "env": {
        "IDA_RPC_URL": "http://127.0.0.1:13337"
      }
    }
  }
}
```

### Preferred Tool Selection

Set environment variable:
```bash
$env:REO_PREFERRED_TOOL = "ida"  # or "ghidra"
```

## Integration with Other MCP Servers

The Reverse Engineering Orchestrator works alongside other MCP servers:

```json
{
  "mcpServers": {
    "ida-pro-mcp": {
      "command": "...",
      "args": [...]
    },
    "reverse-engineering-orchestrator": {
      "command": "...",
      "args": [...]
    }
  }
}
```

**Note**: Both can run simultaneously. The orchestrator provides a unified interface, while `ida-pro-mcp` provides direct IDA Pro access.

## Next Steps

1. **Test Basic Operations**: Try detecting tools and getting function info
2. **Load a Binary**: Load a test binary in IDA Pro or Ghidra
3. **Decompile Functions**: Test decompilation on real functions
4. **Explore References**: Find cross-references in your binary

## Support

For issues or questions:
1. Check `documentation/INTEGRATION_STATUS.md` for current status
2. Review `documentation/ADR-006-tool-integration-strategy.md` for architecture
3. Test with `test_mcp_server.py` to isolate issues

