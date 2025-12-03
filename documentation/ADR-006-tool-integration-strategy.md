# ADR-006: Tool Integration Strategy for Reverse Engineering Orchestrator

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Both IDA Pro (via ida-pro-mcp) and Ghidra (via pyGhidraRun) are now installed. Need to integrate them into the unified Reverse Engineering Orchestrator MCP server.

## Decision

Integrate both tools into the Reverse Engineering Orchestrator using a **hybrid approach**:
1. **IDA Pro**: Use direct RPC client (like query_ida_functions.py) integrated into our adapter
2. **Ghidra**: Complete adapter using pyGhidraRun subprocess execution
3. **Unified MCP Server**: Our orchestrator MCP server routes to appropriate adapter
4. **Tool Selection**: Automatic detection and selection, with manual override

## Context

### Current State
- ✅ IDA Pro: ida-pro-mcp installed and working in Cursor
- ✅ Ghidra: Installed in tools/ghidra/ with pyGhidraRun available
- ✅ Our MCP Server: Structure built, needs tool integration
- ✅ Adapters: Base structure created, need implementation

### Integration Options

**Option A: Proxy Through ida-pro-mcp**
- Use ida-pro-mcp as sub-server
- Our MCP server proxies requests to ida-pro-mcp
- **Pros**: Leverages existing, tested implementation
- **Cons**: Adds complexity, dependency on external server

**Option B: Direct RPC Integration (Chosen)**
- Use IDA Pro RPC directly (like query_ida_functions.py)
- Implement in our IDAAdapter
- **Pros**: Full control, no external dependencies, simpler architecture
- **Cons**: Need to implement all functionality ourselves

**Option C: Hybrid - Use ida-pro-mcp for IDA, Our adapter for Ghidra**
- Keep ida-pro-mcp separate for IDA Pro
- Our server only handles Ghidra
- **Pros**: Simplest integration
- **Cons**: Not unified, user needs to know which tool to use

## Architecture Decisions

### Component 1: IDA Pro Integration

**Implementation:**
- Use direct RPC client (based on query_ida_functions.py)
- Integrate into IDAAdapter class
- Reuse RPC communication code
- Map RPC methods to adapter interface

**Key Methods:**
- `load_binary`: Not applicable (IDA loads via GUI)
- `decompile_function`: Use `decompile_function` RPC method
- `set_breakpoint`: Use IDA debugger RPC methods
- `read_memory`: Use `read_memory_bytes` RPC method
- `get_function_at`: Use `get_function_by_address` RPC method

**ADR Note:** IDA Pro binary loading happens through GUI, not programmatically.
Our adapter will work with already-loaded databases. This is acceptable as
most workflows start with IDA Pro already open.

### Component 2: Ghidra Integration

**Implementation:**
- Complete GhidraAdapter using pyGhidraRun
- Generate Python scripts dynamically
- Execute via subprocess
- Parse JSON responses

**Key Methods:**
- `load_binary`: Generate script to import binary into Ghidra project
- `decompile_function`: Use Ghidra Decompiler API
- `set_breakpoint`: Not supported (static analysis tool)
- `read_memory`: Read from binary file, not runtime memory
- `get_function_at`: Use Ghidra FunctionManager API

**ADR Note:** Ghidra is static analysis only. Breakpoints and runtime memory
reading are not applicable. Our adapter will return appropriate errors for
these operations.

### Component 3: Unified MCP Server

**Architecture:**
```
Cursor AI
    ↓
Our MCP Server (reverse-engineering-orchestrator)
    ↓
Tool Detector → Selects IDAAdapter or GhidraAdapter
    ↓
Adapter → IDA Pro RPC or Ghidra pyGhidraRun
    ↓
Tool (IDA Pro or Ghidra)
```

**Tool Selection:**
- Auto-detect on startup
- Allow manual selection via MCP tool
- Support switching between tools
- Cache adapter instances

### Component 4: MCP Tools Enhancement

**Additional Tools Needed:**
- `switch_tool` - Switch between IDA Pro and Ghidra
- `get_tool_capabilities` - Query what operations are supported
- `export_decompiled_code` - Export decompiled code to files
- `search_code` - Search for code patterns across functions

## Next Steps

### Phase 1: Complete Adapter Implementation (Current)

1. **IDA Adapter:**
   - Integrate RPC client code from query_ida_functions.py
   - Implement all BaseAdapter methods using RPC
   - Handle IDA Pro specific quirks
   - Test with real IDA Pro database

2. **Ghidra Adapter:**
   - Complete pyGhidraRun script generation
   - Implement binary loading
   - Implement decompilation
   - Test with real Ghidra installation

### Phase 2: MCP Server Integration

1. **Update MCP Protocol Handler:**
   - Connect adapters to MCP tools
   - Handle tool selection/switching
   - Add error handling and validation
   - Test end-to-end with Cursor

2. **Tool Detection Integration:**
   - Auto-select tool on startup
   - Provide tool status resource
   - Allow manual tool selection

### Phase 3: Additional Tools (Future)

1. **OpenCV Visual Analyzer:**
   - Screen capture and analysis
   - UI change detection
   - Coordinate extraction

2. **Memory Scanner Integration:**
   - x64dbg integration
   - Cheat Engine API
   - Memory address correlation

3. **Advanced Features:**
   - Code pattern search
   - Cross-reference analysis
   - Automated reverse engineering workflows

## Tool Requirements

### Already Available
- ✅ IDA Pro (with ida-pro-mcp)
- ✅ Ghidra (with pyGhidraRun)
- ✅ Python 3.8+
- ✅ MCP SDK

### Needed for Full System

1. **OpenCV Visual Analyzer:**
   - `opencv-python` - Computer vision
   - `mss` or `Pillow` - Screen capture
   - `pytesseract` (optional) - OCR for text extraction

2. **Memory Scanner:**
   - x64dbg with Python plugin, OR
   - Cheat Engine with API, OR
   - Custom memory scanning solution

3. **Communication Layer:**
   - Message queue or socket server
   - For coordinating between components

## Implementation Priority

1. **High Priority (Now):**
   - Complete IDA adapter with RPC
   - Complete Ghidra adapter with pyGhidraRun
   - Integrate both into MCP server
   - Test unified interface

2. **Medium Priority (Next):**
   - OpenCV visual analyzer
   - Memory scanner integration
   - Component communication

3. **Low Priority (Future):**
   - Advanced analysis features
   - Automated workflows
   - Performance optimization

## Consequences

### Positive
- Unified interface for both tools
- Single MCP server for Cursor
- Tool-agnostic operations
- Easy to add more tools later

### Negative
- Need to maintain adapters for both tools
- Some operations tool-specific (breakpoints in IDA only)
- Complexity in handling tool differences

### Risks
- Tool API changes
- Performance overhead from subprocess (Ghidra)
- RPC connection failures (IDA Pro)

## References

- query_ida_functions.py - IDA Pro RPC client implementation
- ida-pro-mcp source code - Reference implementation
- Ghidra Python API documentation
- ADR-004: Tool Integration Methods

