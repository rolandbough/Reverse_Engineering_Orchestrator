# Tool Requirements for Reverse Engineering Orchestrator

## Current Status

### ✅ Installed and Working
- **IDA Pro**: Installed with ida-pro-mcp MCP server
  - RPC server running on port 13337
  - MCP plugin loaded
  - Integration: Direct RPC client in IDAAdapter

- **Ghidra**: Installed in `tools/ghidra/`
  - pyGhidraRun available at `tools/ghidra/support/pyGhidraRun`
  - Integration: Subprocess execution via GhidraAdapter

### ⏳ In Progress
- **IDA Adapter**: RPC integration complete, needs testing
- **Ghidra Adapter**: Structure complete, needs full Ghidra API implementation
- **MCP Server**: Protocol complete, needs adapter integration

### 📋 Needed for Complete System

## Required Tools

### 1. OpenCV Visual Analyzer
**Purpose**: Monitor target application UI and detect visual changes

**Requirements:**
- `opencv-python` - Computer vision library
- `mss` or `Pillow` - Screen capture
- `pytesseract` (optional) - OCR for text extraction
- `numpy` - Array operations

**Installation:**
```bash
pip install opencv-python mss numpy
# Optional: pip install pytesseract
```

**Functionality:**
- Screen capture of target application window
- Image analysis to detect changes
- Coordinate extraction for UI elements
- Value extraction (OCR or pixel analysis)

**Integration:**
- Standalone Python process
- Communicates with Memory Scanner via socket/file
- Outputs: coordinates, changed values, timestamps

### 2. Memory Scanner
**Purpose**: Find memory addresses corresponding to visual changes

**Options:**

#### Option A: x64dbg with Python Plugin
- **Tool**: x64dbg (free, open-source debugger)
- **Plugin**: x64dbg Python plugin
- **Pros**: Free, powerful, good Python API
- **Cons**: Requires x64dbg installation and plugin setup

#### Option B: Cheat Engine API
- **Tool**: Cheat Engine (free memory scanner)
- **API**: Cheat Engine Lua/Python API
- **Pros**: Excellent memory scanning capabilities
- **Cons**: May require Cheat Engine to be running

#### Option C: Custom Memory Scanner
- **Tool**: Build custom scanner using Windows API
- **Libraries**: `pymem`, `ctypes`, Windows Debug API
- **Pros**: Full control, no external dependencies
- **Cons**: More complex to implement

**Recommended**: Start with x64dbg Python plugin (Option A)

**Functionality:**
- Initial memory scan for value
- Filtered scans on value changes
- Address identification
- Memory reading/writing

**Integration:**
- Python script using x64dbg API
- Receives values from OpenCV Analyzer
- Outputs memory addresses to IDE Plugin

### 3. Communication Layer
**Purpose**: Coordinate between components

**Options:**

#### Option A: TCP Sockets
- Simple request/response
- Low latency
- Easy to implement

#### Option B: Message Queue (Redis/RabbitMQ)
- More robust
- Better for multiple components
- Overkill for current needs

#### Option C: File-based Communication
- Simplest
- Less real-time
- Good for testing

**Recommended**: Start with TCP sockets (Option A)

**Components:**
- OpenCV Analyzer → Memory Scanner
- Memory Scanner → IDE Plugin
- IDE Plugin → MCP Server

## Architecture Overview

```
┌─────────────────┐
│  Cursor AI      │
└────────┬────────┘
         │ MCP
┌────────▼────────────────────────┐
│  Reverse Engineering Orchestrator│
│  MCP Server                      │
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

Future Components:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ OpenCV       │───▶│ Memory       │───▶│ IDE Plugin   │
│ Analyzer     │    │ Scanner      │    │ (Breakpoint) │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Implementation Phases

### Phase 1: Core Tool Integration (Current)
- ✅ IDA Pro RPC client
- ✅ Ghidra pyGhidraRun structure
- ⏳ Complete IDA adapter implementation
- ⏳ Complete Ghidra adapter implementation
- ⏳ Integrate both into MCP server
- ⏳ Test unified interface

### Phase 2: Advanced Features
- ⏳ OpenCV visual analyzer
- ⏳ Memory scanner integration
- ⏳ Component communication layer
- ⏳ Address correlation system

### Phase 3: Full Workflow
- ⏳ End-to-end visual → memory → code analysis
- ⏳ Automated reverse engineering workflows
- ⏳ Pattern recognition and analysis

## Next Steps

1. **Complete Adapter Implementation**
   - Finish IDA adapter with all RPC methods
   - Complete Ghidra adapter with full API
   - Test both adapters

2. **MCP Server Integration**
   - Connect adapters to MCP tools
   - Test tool switching
   - Verify Cursor integration

3. **OpenCV Analyzer** (Phase 2)
   - Install OpenCV dependencies
   - Implement screen capture
   - Implement change detection

4. **Memory Scanner** (Phase 2)
   - Choose scanner tool (x64dbg recommended)
   - Implement Python integration
   - Test memory scanning workflow

## Dependencies Summary

### Current
```bash
pip install mcp pydantic typing-extensions psutil
```

### For OpenCV Analyzer
```bash
pip install opencv-python mss numpy
# Optional: pip install pytesseract
```

### For Memory Scanner (x64dbg)
- Install x64dbg
- Install x64dbg Python plugin
- Use x64dbg Python API

### For Memory Scanner (Custom)
```bash
pip install pymem ctypes
```

## Tool Selection Matrix

| Feature | IDA Pro | Ghidra | Notes |
|---------|---------|--------|-------|
| Static Analysis | ✅ | ✅ | Both excellent |
| Decompilation | ✅ (Hex-Rays) | ✅ (Built-in) | Both support |
| Dynamic Analysis | ✅ | ❌ | IDA Pro only |
| Breakpoints | ✅ | ❌ | IDA Pro only |
| Runtime Memory | ✅ | ❌ | IDA Pro only |
| Free | ❌ | ✅ | Ghidra is free |
| Python API | ✅ (IDAPython) | ✅ (pyGhidraRun) | Both support |

## Recommendations

1. **For Static Analysis**: Use either tool, Ghidra is free
2. **For Dynamic Analysis**: Use IDA Pro (debugger required)
3. **For Full Workflow**: Use IDA Pro (supports both static and dynamic)
4. **For Budget-Conscious**: Use Ghidra for static, IDA Pro for dynamic

