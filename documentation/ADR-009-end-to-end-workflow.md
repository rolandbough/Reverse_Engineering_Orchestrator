# ADR-009: End-to-End Workflow Integration

**Status:** Accepted  
**Date:** 2025-12-02  
**Deciders:** User, AI Agent  
**Context:** Need to connect all components (Visual Analyzer, Memory Scanner, RE Tools) into a complete automated workflow.

## Decision

Implement a **Workflow Orchestrator** that coordinates the complete reverse engineering workflow:
1. Visual Analyzer detects UI changes
2. Memory Scanner finds corresponding memory addresses
3. RE Tool sets breakpoints and decompiles code
4. AI analyzes the decompiled code

## Context

### Requirement
The system must provide an end-to-end workflow that:
- Automatically detects visual changes in target application
- Finds memory addresses corresponding to those changes
- Sets breakpoints at those addresses
- Decompiles and analyzes code when breakpoints hit
- Presents results to the AI agent for analysis

### Architecture Decision

**Workflow Orchestrator:**
- Central coordinator that manages all components
- Handles communication between Visual Analyzer, Memory Scanner, and RE Tools
- Maintains workflow state and coordinates operations
- Exposes workflow control via MCP tools

**MCP Integration:**
- New MCP tools for workflow control:
  - `start_workflow` - Start the complete workflow
  - `stop_workflow` - Stop the workflow
  - `get_workflow_status` - Get current status
  - `set_breakpoints_at_addresses` - Set breakpoints at found addresses

**Communication Flow:**
```
Visual Analyzer (detects change)
  ↓ (via TCP socket)
Workflow Orchestrator
  ↓ (triggers scan)
Memory Scanner (finds addresses)
  ↓ (returns addresses)
Workflow Orchestrator
  ↓ (sets breakpoints)
RE Tool Adapter (sets breakpoints)
  ↓ (breakpoint hits)
RE Tool Adapter (decompiles code)
  ↓ (returns code)
AI Agent (analyzes code)
```

## Implementation

### Component Structure

```
src/orchestrator/
├── __init__.py
└── workflow_orchestrator.py  # Main orchestrator
```

### Workflow Steps

1. **Start Workflow:**
   - Initialize Visual Analyzer
   - Initialize Memory Scanner
   - Start visual monitoring
   - Begin listening for changes

2. **Visual Change Detected:**
   - Visual Analyzer detects UI change
   - Sends message to Orchestrator
   - Orchestrator extracts value

3. **Memory Scan:**
   - If first change: Perform initial scan
   - If subsequent change: Perform filter scan
   - Narrow down candidate addresses

4. **Breakpoint Setting:**
   - When few addresses remain (≤5), suggest breakpoints
   - Set hardware write breakpoints at addresses
   - Wait for breakpoint hits

5. **Code Analysis:**
   - When breakpoint hits, get Program Counter (PC)
   - Decompile function containing PC
   - Analyze decompiled code
   - Present results to AI

### State Management

The orchestrator maintains:
- Workflow running state
- Detected values history
- Current scan addresses
- Breakpoint status
- Component availability

## Consequences

### Positive
- Complete automated workflow
- No manual intervention required
- Real-time correlation between visual and memory
- AI can analyze code automatically

### Negative
- Complex state management
- Multiple components to coordinate
- Potential failure points in chain
- Requires all components to be available

### Risks
- Components may fail independently
- Memory scanning may be slow
- False positives in address detection
- Breakpoint overhead may affect performance

## Usage Example

```python
# Via MCP tool call
{
  "name": "start_workflow",
  "arguments": {
    "process_name": "game.exe",
    "regions": [
      {"x": 100, "y": 100, "width": 200, "height": 50}
    ],
    "value_type": "int32"
  }
}

# Workflow automatically:
# 1. Monitors screen region
# 2. Detects value changes
# 3. Scans memory
# 4. Sets breakpoints
# 5. Decompiles code
```

## Future Enhancements

1. **Pattern Recognition:**
   - Learn common patterns
   - Auto-suggest breakpoints
   - Optimize scan strategies

2. **Multi-Value Tracking:**
   - Track multiple values simultaneously
   - Correlate related values
   - Find data structures

3. **Advanced Analysis:**
   - Code flow analysis
   - Data dependency tracking
   - Automated reverse engineering

## References

- ADR-001: System Architecture
- ADR-007: OpenCV Visual Analyzer
- ADR-008: Memory Scanner Architecture

