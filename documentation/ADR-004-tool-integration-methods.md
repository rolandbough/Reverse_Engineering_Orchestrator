# ADR-004: Tool Integration Methods for IDA Pro and Ghidra

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Need to determine how to programmatically interact with IDA Pro and Ghidra for the MCP server. Both tools have Python APIs but different execution models.

## Decision

Use different integration methods for each tool based on their architecture:

### Ghidra Integration
- **Method:** Execute Python scripts via `pyGhidraRun` utility
- **Location:** `tools/ghidra/support/pyGhidraRun` (or `pyGhidraRun.bat` on Windows)
- **Approach:** Bridge pattern - MCP server communicates with Ghidra via subprocess calls to pyGhidraRun
- **Alternative:** ghidra_bridge for persistent connection (future enhancement)

### IDA Pro Integration
- **Method:** Direct IDAPython API access when running inside IDA Pro
- **Alternative:** IDA Pro remote debugging/scripting (if available)
- **Approach:** Plugin-based or subprocess execution depending on IDA Pro mode

## Context

### Ghidra Architecture
- **Java-based:** Ghidra runs as a Java application
- **Python Bridge:** Python scripts run via `pyGhidraRun` which sets up the Java-Python bridge
- **Execution Model:** Scripts are executed in Ghidra's context via subprocess
- **Key Discovery:** `./support/pyGhidraRun` in the Ghidra installation directory

### IDA Pro Architecture
- **Native Application:** IDA Pro is a native C++ application
- **IDAPython:** Python API embedded in IDA Pro
- **Execution Model:** Scripts run inside IDA Pro process or via remote debugging
- **Two Modes:**
  1. **Script Mode:** Run Python scripts directly in IDA Pro
  2. **Plugin Mode:** Load Python plugins into IDA Pro

## Architecture Decisions

### Component 1: Ghidra Adapter

**Execution Strategy:**
1. MCP server calls `pyGhidraRun` with Python script as argument
2. Script communicates results back via stdout/JSON
3. MCP server parses results and returns to client

**Script Template:**
```python
# Script executed via: pyGhidraRun script.py
import json
import sys
from ghidra.util.task import ConsoleTaskMonitor

# Perform operation
result = {
    "status": "success",
    "data": {...}
}

# Output JSON result
print(json.dumps(result))
sys.exit(0)
```

**Communication Pattern:**
- Request: MCP server writes Python script to temp file
- Execution: Subprocess call to `pyGhidraRun script.py`
- Response: Parse JSON from stdout

**ADR Note:** Using subprocess execution allows the MCP server to run independently
of Ghidra GUI. This is simpler than maintaining a persistent bridge connection.

### Component 2: IDA Pro Adapter

**Execution Strategy (Two Options):**

**Option A: IDA Pro Script Mode (Preferred)**
1. MCP server generates Python script
2. Script is executed in IDA Pro context (if IDA is running)
3. Results communicated via file or stdout

**Option B: IDA Pro Remote Debugging**
1. Use IDA Pro's remote debugging capabilities
2. Connect to running IDA Pro instance
3. Execute commands via remote interface

**Decision:** Start with Option A (script mode), add Option B if needed.

**Script Template:**
```python
# Script executed in IDA Pro context
import idc
import idaapi
import json

# Perform operation
result = {
    "status": "success",
    "data": {...}
}

# Write result to file or stdout
with open("result.json", "w") as f:
    json.dump(result, f)
```

**ADR Note:** IDA Pro integration is more complex because scripts must run
within IDA Pro's process. This may require IDA Pro to be running, or
we need to use IDA Pro's command-line mode.

### Component 3: Unified Adapter Interface

**Base Adapter Methods:**
```python
class BaseAdapter:
    def execute_script(self, script: str, args: dict) -> dict:
        """Execute Python script in tool context"""
        pass
    
    def load_binary(self, path: str) -> dict:
        """Load binary file"""
        pass
    
    def decompile(self, address: int) -> dict:
        """Decompile function at address"""
        pass
    
    def set_breakpoint(self, address: int, type: str) -> dict:
        """Set breakpoint"""
        pass
```

**ADR Note:** Unified interface allows MCP tools to work with either tool
transparently. Each adapter implements the interface using tool-specific methods.

## Implementation Details

### Ghidra Script Execution

**Command Format:**
```bash
# Linux/macOS
./tools/ghidra/support/pyGhidraRun script.py

# Windows
tools\ghidra\support\pyGhidraRun.bat script.py
```

**Script Generation:**
- MCP server generates Python scripts dynamically
- Scripts use Ghidra API to perform operations
- Results serialized as JSON

**Error Handling:**
- Check pyGhidraRun exists
- Handle subprocess errors
- Parse JSON output safely
- Handle Ghidra-specific errors

### IDA Pro Script Execution

**Command Format (if command-line mode available):**
```bash
ida64.exe -A -Sscript.py binary.exe
```

**Or if IDA Pro is running:**
- Use IDA Pro's script execution interface
- May require IDA Pro plugin or remote connection

**ADR Note:** IDA Pro integration requires more research. May need to
support both running IDA Pro instance and command-line execution.

## Consequences

### Positive
- **Ghidra:** Simple subprocess execution model
- **Unified Interface:** Both tools work through same adapter pattern
- **Flexible:** Can add more tools later with same pattern
- **Independent:** MCP server doesn't need tools running initially

### Negative
- **Performance:** Subprocess overhead for each operation
- **State Management:** Each script execution is independent (may need state files)
- **Error Handling:** More complex error handling across process boundaries

### Risks
- **Ghidra:** pyGhidraRun may not be available in all installations
- **IDA Pro:** May require IDA Pro to be running or have specific configuration
- **Platform Differences:** Windows vs Linux path handling
- **Script Security:** Executing dynamically generated scripts

## Mitigation Strategies

1. **Ghidra:**
   - Check pyGhidraRun exists before use
   - Provide clear error messages if missing
   - Document installation requirements

2. **IDA Pro:**
   - Support multiple execution modes
   - Graceful degradation if IDA not available
   - Clear documentation of requirements

3. **State Management:**
   - Use temporary files for state persistence
   - Consider persistent bridge connections (future)

4. **Security:**
   - Validate script inputs
   - Sanitize file paths
   - Limit script execution scope

## Future Enhancements

1. **Ghidra Bridge:** Use ghidra_bridge for persistent connection
2. **IDA Pro Remote:** Implement remote debugging connection
3. **Caching:** Cache results to reduce subprocess calls
4. **Async Operations:** Support long-running operations

## References

- Ghidra Python API documentation
- IDA Pro IDAPython API documentation
- pyGhidraRun usage examples
- IDA Pro command-line options

