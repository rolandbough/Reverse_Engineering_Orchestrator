# ADR-001: Reverse Engineering Orchestrator - System Architecture

**Status:** Proposed  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Building an AI-powered reverse engineering system that integrates visual analysis, dynamic memory reading, and automated decompilation.

## Decision

Build a **Reverse Engineering Orchestrator** that combines:
1. OpenCV-based visual UI analysis
2. Dynamic memory scanning and reading
3. AI-driven decompilation and code analysis via IDE integration
4. Model Context Protocol (MCP) for AI agent control

## Context

### Original Requirement
The user wants Cursor (the IDE) empowered to:
- Decompile code in real-time
- Read memory in real-time
- Use OpenCV to analyze UI changes
- Find memory addresses that correspond to visual changes
- Automate the entire reverse engineering workflow

### Key Questions Asked

**Q1: Is there an existing tool that does this?**
- **Answer:** No single off-the-shelf tool exists. Need to build integration layer.
- **Rationale:** This is a highly specialized workflow combining three distinct domains (visual analysis, dynamic analysis, static analysis) that don't typically integrate.

**Q2: What about AI integration?**
- **Answer:** Use Model Context Protocol (MCP) to connect AI agents to reverse engineering tools (IDA Pro, Ghidra).
- **Rationale:** MCP allows AI to control IDE functions, decompile code, set breakpoints, and analyze memory programmatically.

**Q3: What's the missing piece?**
- **Answer:** The OpenCV UI analysis → Memory address correlation layer needs to be custom-built.
- **Rationale:** While decompilers and debuggers have AI integration, the visual-to-memory bridge is custom.

### Architecture Components

#### Component 1: OpenCV Visual Analyzer
- **Purpose:** Monitor target application UI and detect visual changes
- **Technology:** Python, OpenCV (cv2), screen capture libraries (mss/Pillow)
- **Output:** Screen coordinates and changed values
- **Decision Rationale:** OpenCV is the industry standard for computer vision tasks. Python provides easy integration with other components.

#### Component 2: Dynamic Memory Scanner
- **Purpose:** Find memory addresses corresponding to visual changes
- **Technology:** x64dbg with Python plugin, or Cheat Engine API
- **Workflow:** 
  1. Receive value from Visual Analyzer
  2. Perform initial memory scan
  3. Filter scan on subsequent changes
  4. Identify candidate memory addresses
- **Decision Rationale:** Need programmatic control over memory scanning. x64dbg and Cheat Engine provide Python APIs.

#### Component 3: Reverse Engineering IDE Integration
- **Purpose:** Set breakpoints, decompile code, enable AI analysis
- **Technology Options:**
  - IDA Pro with IDAPython (commercial, industry standard)
  - Ghidra with Python/Jython scripting (free, open-source)
- **Decision Rationale:** Both support programmatic control. Ghidra is free but IDA Pro has more mature tooling. Choice depends on licensing.

#### Component 4: AI Agent (MCP Integration)
- **Purpose:** Orchestrate the entire workflow, analyze decompiled code
- **Technology:** Model Context Protocol (MCP) server for IDE
- **Workflow:**
  1. Receive memory address from Memory Scanner
  2. Set hardware write breakpoint at address
  3. When breakpoint hits, get Program Counter (PC) address
  4. Decompile function containing PC
  5. Analyze code to understand why value changed
- **Decision Rationale:** MCP allows natural language control of complex tools. AI can handle the analysis that would be tedious for humans.

### Communication Architecture

**Decision:** Use TCP sockets or message queues for inter-component communication.

**Rationale:** 
- Components run as separate processes
- Need reliable, low-latency communication
- Sockets provide simple request/response pattern
- Alternative: File-based communication (simpler but less real-time)

### Integration Flow

```
UI Change (Visual) 
  → OpenCV Analyzer detects change
  → Memory Scanner receives value
  → Memory Scanner finds address
  → IDE Plugin receives address
  → IDE sets write breakpoint
  → Breakpoint triggers on next change
  → AI Agent receives PC address
  → AI decompiles and analyzes code
  → Results presented in IDE cursor
```

## Consequences

### Positive
- Fully automated reverse engineering workflow
- AI can handle complex analysis
- Real-time correlation between visual and memory changes
- Reduces manual work significantly

### Negative
- Complex integration requiring multiple tools
- Requires expertise in multiple domains (CV, RE, AI)
- Potential licensing costs (if using IDA Pro)
- Debugging multi-component system is challenging

### Risks
- Components may not communicate reliably
- Performance overhead from multiple processes
- False positives in memory scanning
- OpenCV may miss subtle UI changes

## Implementation Notes

### Phase 1: Core Components
1. Set up IDE (Ghidra or IDA Pro) with Python scripting
2. Create OpenCV visual analyzer
3. Create memory scanner integration
4. Establish communication protocol

### Phase 2: Integration
1. Connect Visual Analyzer → Memory Scanner
2. Connect Memory Scanner → IDE Plugin
3. Test end-to-end flow

### Phase 3: AI Integration
1. Set up MCP server for IDE
2. Create AI agent prompts
3. Test AI-driven analysis

### Phase 4: Refinement
1. Error handling
2. Performance optimization
3. User interface/feedback

## References

- Model Context Protocol (MCP) documentation
- IDA Pro IDAPython API
- Ghidra scripting documentation
- OpenCV Python tutorials
- x64dbg Python plugin documentation

