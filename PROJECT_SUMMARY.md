# Reverse Engineering Orchestrator - Project Summary

## Overview

The Reverse Engineering Orchestrator is an MCP (Model Context Protocol) server that provides a unified interface for reverse engineering tools (IDA Pro and Ghidra) within Cursor IDE. It enables AI agents to perform reverse engineering operations like decompilation, function analysis, and memory reading.

## Current Status: ✅ Phase 1 Complete

### Completed Components

#### 1. Core Architecture ✅
- **MCP Server**: Full implementation with stdio transport
- **Adapter Pattern**: Unified interface for multiple RE tools
- **Tool Detection**: Automatic detection of IDA Pro and Ghidra
- **Protocol Handler**: Complete MCP protocol implementation

#### 2. IDA Pro Integration ✅
- **RPC Client**: Direct communication with IDA Pro RPC server
- **Adapter**: Full implementation with all operations
- **Methods**: Decompilation, function info, references, memory reading
- **Status**: Tested and working

#### 3. Ghidra Integration ✅
- **pyGhidraRun**: Subprocess execution for Ghidra scripts
- **Adapter**: Full Ghidra API implementation
- **Methods**: Decompilation, function info, references, memory reading
- **Status**: Implementation complete, ready for testing

#### 4. Documentation ✅
- **Setup Guides**: Complete Cursor integration guide
- **Usage Examples**: 16+ practical examples
- **Architecture Docs**: 6 ADR documents
- **Quick Start**: 5-minute setup guide

## Architecture

```
┌─────────────────┐
│  Cursor AI      │
└────────┬────────┘
         │ MCP (stdio)
┌────────▼────────────────────────┐
│  Reverse Engineering Orchestrator│
│  MCP Server                      │
│  - Protocol Handler              │
│  - Tool Detection                │
│  - Adapter Factory               │
└────────┬─────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ IDA   │ │ Ghidra  │
│Adapter│ │Adapter  │
└───┬───┘ └──┬──────┘
    │        │
┌───▼───┐ ┌──▼──────┐
│ IDA   │ │ Ghidra  │
│  Pro  │ │(pyGhidra│
│  RPC  │ │  Run)   │
└───────┘ └─────────┘
```

## Available MCP Tools

### Core Operations
- `detect_re_tool` - Detect and select available tool
- `load_binary` - Load binary file for analysis
- `decompile_function` - Decompile function at address
- `get_function_info` - Get function information
- `find_references` - Find cross-references
- `read_memory` - Read memory at address
- `set_breakpoint` - Set breakpoint (IDA Pro only)

### Resources
- `reo://tool_status` - Current tool status and connection info

## Project Structure

```
Reverse_Engineering_Orchestrator/
├── src/
│   ├── mcp_server/          # MCP server implementation
│   │   ├── server.py        # Main server
│   │   ├── protocol.py      # MCP protocol handler
│   │   ├── config.py        # Configuration
│   │   └── __main__.py      # Entry point
│   ├── adapters/            # Tool adapters
│   │   ├── base_adapter.py  # Base interface
│   │   ├── ida_adapter.py   # IDA Pro adapter
│   │   ├── ghidra_adapter.py # Ghidra adapter
│   │   └── adapter_factory.py # Factory pattern
│   ├── tool_detection/      # Tool detection system
│   │   ├── detector.py       # Main detector
│   │   ├── ida_detector.py  # IDA Pro detection
│   │   └── ghidra_detector.py # Ghidra detection
│   └── utils/               # Utilities
│       └── ida_rpc_client.py # IDA Pro RPC client
├── documentation/
│   ├── ADR-*.md            # Architecture Decision Records
│   ├── SETUP_CURSOR_MCP.md  # Cursor setup guide
│   ├── USAGE_EXAMPLES.md    # Usage examples
│   └── INTEGRATION_STATUS.md # Current status
├── tools/                   # External tools (not committed)
│   ├── ghidra/              # Ghidra installation
│   └── ida/                 # IDA Pro installation
├── test_mcp_server.py       # MCP server test
├── test_ghidra_adapter.py   # Ghidra adapter test
├── query_ida_functions.py   # IDA Pro query tool
├── locate_addresses_from_decomp.py # Address locator
└── setup_cursor_mcp.ps1     # Automated setup script
```

## Key Features

### 1. Unified Interface
- Single MCP server for both IDA Pro and Ghidra
- Tool-agnostic operations
- Automatic tool selection

### 2. Full API Coverage
- Decompilation (Hex-Rays / Ghidra decompiler)
- Function analysis
- Cross-reference finding
- Memory reading
- Breakpoint management (IDA Pro)

### 3. Easy Integration
- Automated setup script
- Clear documentation
- Comprehensive examples

### 4. Extensible Architecture
- Adapter pattern for new tools
- Factory pattern for tool creation
- Plugin-ready design

## Installation & Setup

### Quick Setup (Windows)

```powershell
# 1. Run setup script
.\setup_cursor_mcp.ps1

# 2. Restart Cursor

# 3. Test
# Ask Cursor AI: "What reverse engineering tools are available?"
```

### Manual Setup

See `documentation/SETUP_CURSOR_MCP.md` for detailed instructions.

## Testing

### Test MCP Server
```bash
python test_mcp_server.py
```

### Test IDA Pro Connection
```bash
python query_ida_functions.py --metadata
```

### Test Ghidra Adapter
```bash
python test_ghidra_adapter.py
```

## Usage Examples

### Basic Operations

**Detect Tools:**
```
What reverse engineering tools are available? Use detect_re_tool.
```

**Decompile Function:**
```
Decompile the function at address 0x401000
```

**Find References:**
```
Find all references to address 0x404000
```

See `documentation/USAGE_EXAMPLES.md` for 16+ examples.

## Next Steps (Phase 2)

### Planned Features

1. **OpenCV Visual Analyzer**
   - Screen capture and analysis
   - UI change detection
   - Coordinate extraction

2. **Memory Scanner Integration**
   - x64dbg integration
   - Memory address correlation
   - Pattern matching

3. **Component Communication**
   - TCP socket server
   - Message protocol
   - Real-time coordination

4. **Advanced Workflows**
   - Visual → Memory → Code pipeline
   - Automated analysis
   - Pattern recognition

## Dependencies

### Core
- `mcp>=1.16.0` - MCP SDK
- `pydantic` - Data validation
- `psutil` - Process detection

### Optional
- `ida-pro-mcp` - IDA Pro MCP server (reference)
- `opencv-python` - Visual analysis (Phase 2)
- `mss` - Screen capture (Phase 2)

## Documentation

- **Quick Start**: `QUICK_START.md`
- **Setup Guide**: `documentation/SETUP_CURSOR_MCP.md`
- **Usage Examples**: `documentation/USAGE_EXAMPLES.md`
- **Integration Status**: `documentation/INTEGRATION_STATUS.md`
- **Tool Requirements**: `documentation/TOOL_REQUIREMENTS.md`
- **Architecture Decisions**: `documentation/ADR-*.md`

## Contributing

This project follows ADR (Architecture Decision Records) for documenting decisions. See `documentation/ADR-*.md` for architectural decisions.

## License

[To be determined]

## Acknowledgments

- Built on Model Context Protocol (MCP)
- Integrates with IDA Pro (Hex-Rays)
- Integrates with Ghidra (NSA)
- Uses `ida-pro-mcp` as reference implementation

