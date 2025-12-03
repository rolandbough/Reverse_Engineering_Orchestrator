# ADR-008: Memory Scanner Architecture

**Status:** Accepted  
**Date:** 2025-12-02  
**Deciders:** User, AI Agent  
**Context:** Need to find memory addresses corresponding to visual changes detected by OpenCV analyzer.

## Decision

Implement a **Memory Scanner** component with support for multiple backends:
1. **x64dbg** (primary) - Free, open-source debugger with Python plugin
2. **Cheat Engine** (alternative) - Memory scanner with Lua/Python API
3. **Custom Scanner** (fallback) - Using Windows API via `pymem` or `ctypes`

## Context

### Requirement
The memory scanner must:
- Receive values from the Visual Analyzer
- Perform initial memory scans for those values
- Filter scans on subsequent value changes
- Identify candidate memory addresses
- Communicate addresses to the IDE plugin for breakpoint setting

### Architecture Decision

**Multi-Backend Support:**
- Abstract base class `BaseMemoryScanner` defines the interface
- Concrete implementations: `X64dbgScanner`, `CheatEngineScanner`, `CustomScanner`
- Scanner factory selects appropriate backend based on availability
- Graceful fallback if preferred scanner unavailable

**Communication:**
- Memory Scanner receives values via TCP socket from Visual Analyzer
- Memory Scanner sends addresses via TCP socket to MCP Server
- JSON message protocol for structured communication

## Implementation

### Component Structure

```
src/memory_scanner/
├── __init__.py
├── base_scanner.py          # Abstract base class
├── x64dbg_scanner.py        # x64dbg integration
├── cheat_engine_scanner.py  # Cheat Engine integration
├── custom_scanner.py        # Windows API custom scanner
├── scanner_factory.py       # Factory for scanner selection
└── types.py                 # Common types and data structures
```

### Core Interface

```python
class BaseMemoryScanner:
    def connect(self) -> ScannerResult
    def disconnect(self) -> ScannerResult
    def initial_scan(self, value: Any, value_type: str) -> List[str]  # Returns addresses
    def filter_scan(self, value: Any, value_type: str) -> List[str]   # Returns filtered addresses
    def read_memory(self, address: str, size: int) -> bytes
    def write_memory(self, address: str, data: bytes) -> ScannerResult
    def get_scan_results(self) -> List[ScanResult]
    def clear_scan(self) -> ScannerResult
```

### Workflow

1. **Initial Scan:**
   - Visual Analyzer detects value change (e.g., score = 100)
   - Sends value to Memory Scanner via socket
   - Memory Scanner performs initial scan for value
   - Returns list of candidate addresses

2. **Filtered Scan:**
   - Visual Analyzer detects new value (e.g., score = 150)
   - Sends new value to Memory Scanner
   - Memory Scanner filters previous results for new value
   - Returns reduced list of addresses

3. **Address Identification:**
   - After multiple filtered scans, few addresses remain
   - Memory Scanner sends final addresses to MCP Server
   - MCP Server sets breakpoints at addresses
   - When breakpoint hits, decompile and analyze code

## Consequences

### Positive
- Flexible architecture supports multiple tools
- Can work with free tools (x64dbg, Cheat Engine)
- Fallback to custom scanner if needed
- Clear separation of concerns

### Negative
- Requires external tool installation (x64dbg or Cheat Engine)
- Custom scanner more complex to implement
- Multiple backends increase maintenance

### Risks
- x64dbg Python plugin may have API changes
- Cheat Engine API may be undocumented
- Custom scanner may have permission issues
- Performance overhead from multiple scans

## Implementation Phases

### Phase 1: Base Architecture
- Create base scanner interface
- Implement scanner factory
- Create types and data structures
- Add MCP integration

### Phase 2: x64dbg Integration
- Research x64dbg Python API
- Implement X64dbgScanner
- Test memory scanning workflow
- Handle errors gracefully

### Phase 3: Alternative Backends
- Implement CheatEngineScanner (if needed)
- Implement CustomScanner (fallback)
- Test all backends
- Document usage

### Phase 4: Communication Layer
- TCP socket server for Visual Analyzer → Scanner
- TCP socket client for Scanner → MCP Server
- JSON message protocol
- Error handling and reconnection

## References

- x64dbg Python plugin documentation
- Cheat Engine Lua/Python API
- Windows Debug API documentation
- pymem library documentation

