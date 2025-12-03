# Implementation Plan: Reverse Engineering Orchestrator MCP Server

## Overview

This document provides a detailed, step-by-step plan for building the Reverse Engineering Orchestrator as an MCP server that integrates with Cursor IDE and supports both IDA Pro and Ghidra.

## Project Structure

```
Reverse_Engineering_Orchestrator/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py              # Main MCP server
│   │   ├── protocol.py            # MCP protocol handling
│   │   └── config.py               # Server configuration
│   ├── tool_detection/
│   │   ├── __init__.py
│   │   ├── detector.py             # Main detection logic
│   │   ├── ida_detector.py         # IDA Pro detection
│   │   └── ghidra_detector.py      # Ghidra detection
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py         # Base class for adapters
│   │   ├── ida_adapter.py          # IDA Pro adapter
│   │   └── ghidra_adapter.py       # Ghidra adapter
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── binary_loader.py        # Load binary tool
│   │   ├── decompiler.py           # Decompile function tool
│   │   ├── breakpoint.py           # Breakpoint management
│   │   └── memory_reader.py        # Memory reading tool
│   └── utils/
│       ├── __init__.py
│       └── logging.py               # Logging utilities
├── tests/
│   ├── test_detection.py
│   ├── test_adapters.py
│   └── test_tools.py
├── requirements.txt
├── setup.py
└── README.md
```

## Phase 1: Foundation Setup

### Step 1.1: Project Structure and Dependencies

**Tasks:**
1. Create project directory structure
2. Create `requirements.txt` with initial dependencies:
   - `mcp` (MCP SDK) or implement stdio-based protocol
   - `pydantic` (for data validation)
   - `typing-extensions` (for type hints)
3. Create `setup.py` for package installation
4. Set up basic logging configuration

**Deliverables:**
- Complete directory structure
- `requirements.txt` with version pins
- Basic `setup.py`
- Logging configuration

### Step 1.2: MCP Server Foundation

**Tasks:**
1. Research MCP protocol specification
2. Implement basic stdio-based MCP server
3. Create server class with:
   - Request/response handling
   - Tool registration
   - Resource registration
   - Error handling
4. Test server can start and accept connections

**Deliverables:**
- Working MCP server that responds to basic requests
- Protocol handler implementation
- Configuration management

**ADR Notes:**
- Using stdio for MCP communication (standard for Cursor)
- Server runs as separate process
- JSON-RPC 2.0 protocol for MCP

### Step 1.3: Tool Detection System

**Tasks:**
1. Create `ToolDetector` base class
2. Implement `IDADetector`:
   - Check environment variables
   - Check Windows registry
   - Check common installation paths
   - Check for idapython module
   - Check running processes
3. Implement `GhidraDetector`:
   - Check environment variables
   - Check common installation paths
   - Check for ghidra_bridge module
   - Check for Ghidra scripts
4. Create unified detection interface
5. Add detection result caching

**Deliverables:**
- `ToolDetector` class with detection methods
- `IDADetector` implementation
- `GhidraDetector` implementation
- Detection result structure (tool type, path, version, status)

**ADR Notes:**
- Detection runs on server startup
- Results cached to avoid repeated checks
- Detection can be manually triggered via MCP tool
- Graceful degradation if no tools found

## Phase 2: Tool Adapters

### Step 2.1: Base Adapter Interface

**Tasks:**
1. Define `BaseAdapter` abstract class with methods:
   - `connect()` - Connect to tool
   - `disconnect()` - Disconnect from tool
   - `is_connected()` - Check connection status
   - `load_binary(path)` - Load binary file
   - `decompile(address)` - Decompile at address
   - `set_breakpoint(address, type)` - Set breakpoint
   - `read_memory(address, size)` - Read memory
   - `get_function_at(address)` - Get function info
2. Define common data structures (Address, Function, Breakpoint)
3. Create adapter factory pattern

**Deliverables:**
- `BaseAdapter` abstract class
- Common data structures
- Adapter factory

**ADR Notes:**
- Adapter pattern provides unified interface
- Each tool implements adapter interface
- Factory selects appropriate adapter based on detection

### Step 2.2: IDA Pro Adapter

**Tasks:**
1. Research IDAPython API
2. Implement `IDAAdapter` extending `BaseAdapter`:
   - Connection via IDAPython
   - Binary loading using IDA API
   - Decompilation using Hex-Rays (if available) or disassembly
   - Breakpoint management
   - Memory reading
3. Handle IDA Pro specific quirks
4. Add error handling for missing Hex-Rays decompiler

**Deliverables:**
- `IDAAdapter` implementation
- IDA Pro connection handling
- Basic operations working

**ADR Notes:**
- Requires IDAPython to be available
- Hex-Rays decompiler is optional (fallback to disassembly)
- Connection may require IDA Pro to be running

### Step 2.3: Ghidra Adapter

**Tasks:**
1. Research Ghidra Python API and ghidra_bridge
2. Implement `GhidraAdapter` extending `BaseAdapter`:
   - Connection via ghidra_bridge or direct API
   - Binary loading using Ghidra API
   - Decompilation using Ghidra decompiler
   - Breakpoint management (if supported)
   - Memory reading
3. Handle Ghidra-specific requirements (Java bridge)
4. Add error handling

**Deliverables:**
- `GhidraAdapter` implementation
- Ghidra connection handling
- Basic operations working

**ADR Notes:**
- May require ghidra_bridge for Python integration
- Ghidra runs as Java process, requires bridge
- Free alternative to IDA Pro

## Phase 3: MCP Tools Implementation

### Step 3.1: Core Tools

**Tasks:**
1. Implement `detect_re_tool` MCP tool:
   - Run detection
   - Return tool information
   - Update server state
2. Implement `load_binary` MCP tool:
   - Validate file path
   - Call adapter's load_binary
   - Return binary information
3. Implement `decompile_function` MCP tool:
   - Validate address
   - Call adapter's decompile
   - Return decompiled code
4. Implement `set_breakpoint` MCP tool:
   - Validate address and type
   - Call adapter's set_breakpoint
   - Return breakpoint info
5. Implement `read_memory` MCP tool:
   - Validate address and size
   - Call adapter's read_memory
   - Return memory data

**Deliverables:**
- All core MCP tools implemented
- Tool parameter validation
- Error handling and reporting

**ADR Notes:**
- Tools use adapter interface (tool-agnostic)
- Validation happens before adapter calls
- Errors returned as MCP error responses

### Step 3.2: Advanced Tools

**Tasks:**
1. Implement `analyze_code` MCP tool:
   - Get decompiled code
   - Perform basic analysis
   - Return analysis results
2. Implement `find_references` MCP tool:
   - Find references to address
   - Return reference list
3. Implement `get_function_info` MCP tool:
   - Get function details
   - Return function information

**Deliverables:**
- Advanced analysis tools
- Reference finding
- Function information extraction

## Phase 4: MCP Resources

### Step 4.1: State Resources

**Tasks:**
1. Implement `tool_status` resource:
   - Current tool type
   - Connection status
   - Tool version
2. Implement `loaded_binaries` resource:
   - List of loaded binaries
   - Binary information
3. Implement `breakpoints` resource:
   - Active breakpoints
   - Breakpoint details
4. Implement `memory_regions` resource:
   - Monitored memory regions
   - Region information

**Deliverables:**
- All resources implemented
- Resource update mechanisms
- Resource change notifications

## Phase 5: Testing and Integration

### Step 5.1: Unit Tests

**Tasks:**
1. Test tool detection (mocked)
2. Test adapters (mocked tool APIs)
3. Test MCP tools
4. Test error handling

**Deliverables:**
- Comprehensive test suite
- Test coverage > 80%

### Step 5.2: Integration Testing

**Tasks:**
1. Test with actual IDA Pro (if available)
2. Test with actual Ghidra (if available)
3. Test MCP server with Cursor
4. End-to-end workflow testing

**Deliverables:**
- Integration test results
- Known issues document
- Performance benchmarks

### Step 5.3: Documentation

**Tasks:**
1. API documentation
2. Setup instructions
3. Usage examples
4. Troubleshooting guide

**Deliverables:**
- Complete documentation
- Example workflows
- FAQ

## Phase 6: Future Enhancements

### Step 6.1: OpenCV Integration
- Connect visual analyzer
- Memory address correlation
- UI change detection

### Step 6.2: Memory Scanner Integration
- x64dbg integration
- Cheat Engine integration
- Memory scanning workflows

### Step 6.3: Advanced AI Features
- Code analysis improvements
- Pattern recognition
- Automated reverse engineering workflows

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all public APIs
- Add ADR comments for decisions

### Error Handling
- Always handle tool-specific errors
- Provide meaningful error messages
- Log errors for debugging
- Graceful degradation when possible

### Testing
- Write tests before implementation (TDD where possible)
- Mock external dependencies
- Test error cases
- Integration tests with real tools

## Timeline Estimate

- **Phase 1:** 1-2 weeks (Foundation)
- **Phase 2:** 2-3 weeks (Adapters)
- **Phase 3:** 2 weeks (Tools)
- **Phase 4:** 1 week (Resources)
- **Phase 5:** 2 weeks (Testing)
- **Total:** 8-10 weeks for MVP

## Success Criteria

1. MCP server connects to Cursor successfully
2. Tool detection works for both IDA Pro and Ghidra
3. Core tools (load, decompile, breakpoint) work with at least one tool
4. Server handles errors gracefully
5. Documentation is complete
6. Basic tests pass

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP protocol changes | High | Follow MCP spec closely, version pin |
| Tool API changes | Medium | Abstract behind adapters, test regularly |
| Detection failures | Medium | Multiple detection methods, manual override |
| Performance issues | Low | Profile and optimize, caching |
| Tool licensing | Low | Support both free (Ghidra) and paid (IDA) |

