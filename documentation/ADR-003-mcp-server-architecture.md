# ADR-003: MCP Server Architecture for Reverse Engineering Orchestrator

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Building the Reverse Engineering Orchestrator as an MCP (Model Context Protocol) server that can be used in Cursor IDE. Need to support both IDA Pro and Ghidra with automatic detection.

## Decision

Build the Reverse Engineering Orchestrator as a **standalone MCP server** using Python that:
1. Automatically detects available reverse engineering tools (IDA Pro or Ghidra)
2. Exposes reverse engineering operations as MCP tools/resources
3. Acts as a unified interface for Cursor AI to interact with RE tools
4. Uses Python as the integration layer between MCP, RE tools, and other components

## Context

### Requirements
- Must work as an MCP server for Cursor IDE
- Must support both IDA Pro and Ghidra
- Must automatically detect which tool is available
- Must use Python as the primary language
- Must provide a unified API regardless of underlying tool

### Key Questions

**Q1: Should we support both tools simultaneously or one at a time?**
- **Answer:** One at a time, with automatic selection based on availability
- **Rationale:** Simpler architecture, avoids conflicts, most users have one tool
- **Future Consideration:** Could add multi-tool support later if needed

**Q2: How should tool detection work?**
- **Answer:** Multi-method detection: environment variables, registry (Windows), file system paths, process detection
- **Rationale:** Different installation methods require multiple detection strategies

**Q3: Should the MCP server be a separate process or integrated?**
- **Answer:** Separate process that Cursor connects to via stdio or HTTP
- **Rationale:** MCP standard requires separate server process. Allows independent development and testing.

**Q4: What MCP tools/resources should be exposed?**
- **Answer:** 
  - Tools: detect_tool, load_binary, decompile_function, set_breakpoint, read_memory, analyze_code
  - Resources: current_tool_status, loaded_binaries, breakpoints, memory_regions
- **Rationale:** Cover core reverse engineering operations that AI agents need

## Architecture Decisions

### Component 1: MCP Server Core
- **Technology:** Python with `mcp` SDK (or stdio-based implementation)
- **Protocol:** Model Context Protocol over stdio (standard for Cursor)
- **Purpose:** Main server that handles MCP protocol, routes requests to tool adapters

### Component 2: Tool Detection System
- **Purpose:** Automatically detect IDA Pro or Ghidra availability
- **Detection Methods:**
  1. Environment variables (IDA_PATH, GHIDRA_INSTALL_DIR)
  2. Windows Registry (for IDA Pro)
  3. Common installation paths
  4. Process detection (check if tool is running)
  5. Python module availability (idapython, ghidra_bridge)
- **Output:** Selected tool type and configuration

### Component 3: Tool Adapters (Abstraction Layer)
- **IDA Pro Adapter:** Wraps IDAPython API
- **Ghidra Adapter:** Wraps Ghidra Python API (via ghidra_bridge or direct)
- **Purpose:** Provide unified interface regardless of underlying tool
- **Pattern:** Adapter pattern to abstract tool-specific differences

### Component 4: MCP Tools (Operations)
Expose reverse engineering operations as MCP tools:
- `detect_re_tool` - Detect and select available tool
- `load_binary` - Load a binary file for analysis
- `decompile_function` - Decompile function at address
- `set_breakpoint` - Set hardware/software breakpoint
- `read_memory` - Read memory at address
- `analyze_code` - AI-driven code analysis
- `find_address` - Find address from visual change (future)

### Component 5: MCP Resources (State)
Expose system state as MCP resources:
- `tool_status` - Current tool and connection status
- `loaded_binaries` - List of loaded binary files
- `breakpoints` - Active breakpoints
- `memory_regions` - Memory regions being monitored

## Implementation Strategy

### Phase 1: Foundation (Current)
1. Create MCP server structure
2. Implement tool detection system
3. Create basic MCP protocol handler
4. Test with Cursor connection

### Phase 2: Tool Adapters
1. Create IDA Pro adapter (if available)
2. Create Ghidra adapter (if available)
3. Implement unified interface
4. Test with actual RE tools

### Phase 3: MCP Tools Implementation
1. Implement core tools (load, decompile, breakpoint)
2. Add error handling and validation
3. Test each tool individually

### Phase 4: Integration
1. Connect to OpenCV analyzer (future)
2. Connect to memory scanner (future)
3. End-to-end testing

## Consequences

### Positive
- Single MCP server provides unified interface
- Automatic tool detection simplifies setup
- Works seamlessly with Cursor IDE
- Python provides easy integration with other components

### Negative
- Requires MCP SDK knowledge
- Need to maintain adapters for multiple tools
- Tool detection may be complex across platforms

### Risks
- MCP protocol changes
- Tool API changes (IDA Pro, Ghidra updates)
- Detection failures if tools installed in non-standard locations

## Detection Strategy Details

### IDA Pro Detection
1. Check `IDA_PATH` environment variable
2. Windows: Check registry `HKEY_CURRENT_USER\Software\Hex-Rays\IDA`
3. Common paths: `C:\Program Files\IDA Pro`, `C:\Program Files (x86)\IDA Pro`
4. Check for `idapython` Python module
5. Check for running `ida.exe` or `ida64.exe` process

### Ghidra Detection
1. Check `GHIDRA_INSTALL_DIR` environment variable
2. Common paths: `C:\ghidra`, `C:\Program Files\ghidra`
3. Check for `ghidra_bridge` Python module
4. Check for `ghidraRun.bat` or `ghidraRun` script
5. Check for running `ghidra` Java process

## References

- Model Context Protocol specification
- Cursor MCP integration documentation
- IDA Pro IDAPython API documentation
- Ghidra scripting and API documentation
- Python MCP SDK (if available)

