# IDA Pro MCP Setup

## Installation Steps

### 1. Install Python Package

```bash
# In virtual environment
pip install --upgrade ida-pro-mcp

# Or from GitHub for latest features
pip install git+https://github.com/mrexodia/ida-pro-mcp
```

### 2. Install IDA Pro Plugin

```bash
ida-pro-mcp --install
```

This command:
- Installs the IDA Pro plugin to: `%APPDATA%\Hex-Rays\IDA Pro\plugins\mcp-plugin.py`
- Configures MCP servers for:
  - Cursor IDE
  - Claude Code
  - LM Studio
  - Other supported IDEs

### 3. Restart Required

After installation:
- **IDA Pro**: Restart IDA Pro to load the plugin
- **Cursor**: Restart Cursor to load MCP configuration

## Configuration Files

### Cursor MCP Config
Location: `C:\Users\<username>\.cursor\mcp.json`

The `ida-pro-mcp --install` command automatically adds the IDA Pro MCP server configuration:

```json
"ida-pro-mcp": {
  "command": "<venv_path>\\Scripts\\python.exe",
  "args": [
    "<venv_path>\\Lib\\site-packages\\ida_pro_mcp\\server.py"
  ],
  "timeout": 1800,
  "disabled": false,
  "autoApprove": [...],
  "alwaysAllow": [...]
}
```

**Note:** The installer automatically detects your virtual environment and uses it.

### IDA Pro Plugin
Location: `%APPDATA%\Hex-Rays\IDA Pro\plugins\mcp-plugin.py`

The plugin enables MCP communication from IDA Pro.

## Usage

### Starting the MCP Server

The MCP server can be started in different ways:

1. **Via Cursor**: Automatically started when Cursor connects
2. **Manually**: `ida-pro-mcp` (uses stdio transport by default)
3. **HTTP Mode**: `ida-pro-mcp --transport http://127.0.0.1:8744`

### IDA RPC Server

The MCP server communicates with IDA Pro via RPC:
- Default RPC endpoint: `http://127.0.0.1:13337`
- Can be changed with: `ida-pro-mcp --ida-rpc <url>`

### Unsafe Functions

For advanced operations (use with caution):
```bash
ida-pro-mcp --unsafe
```

## Integration with Our Orchestrator

**ADR Note:** The `ida-pro-mcp` package provides a standalone MCP server for IDA Pro.
Our Reverse Engineering Orchestrator aims to provide a unified interface for
both IDA Pro and Ghidra. We can:

1. **Learn from ida-pro-mcp**: Study its implementation patterns
2. **Use alongside**: Run both servers if needed
3. **Integrate**: Potentially use ida-pro-mcp's IDA connection in our adapter

## Verification

After installation and restart:

1. Open IDA Pro - plugin should be loaded
2. Open Cursor - MCP server should be available
3. Check Cursor MCP status to see if IDA Pro MCP server is connected

## Troubleshooting

### Plugin Not Loading
- Check IDA Pro plugin directory: `%APPDATA%\Hex-Rays\IDA Pro\plugins\`
- Verify `mcp-plugin.py` exists
- Check IDA Pro console for errors

### MCP Server Not Connecting
- Verify Cursor MCP config includes ida-pro-mcp
- Check if IDA Pro is running
- Verify RPC server is accessible on port 13337

### Dependencies Missing
```bash
pip install --upgrade ida-pro-mcp
```

## References

- ida-pro-mcp GitHub: https://github.com/mrexodia/ida-pro-mcp
- IDA Pro Plugin API Documentation
- MCP Protocol Specification

