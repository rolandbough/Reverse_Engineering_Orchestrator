# ADR-007: OpenCV Visual Analyzer Architecture

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Need to implement visual analysis component that monitors target application UI and detects changes, enabling the visual → memory → code analysis workflow.

## Decision

Implement OpenCV Visual Analyzer as a standalone Python process that:
1. Captures screen regions of target application
2. Detects visual changes using image comparison
3. Extracts coordinates and values (with optional OCR)
4. Communicates with Memory Scanner via TCP sockets
5. Exposes MCP tools for triggering analysis

## Context

### Requirements
- Monitor target application window/region
- Detect when UI elements change (e.g., score, health, text)
- Extract coordinates of changed elements
- Extract values (numbers, text) from changed regions
- Correlate visual changes with memory addresses

### Use Cases
1. **Game Analysis**: Monitor game UI (score, health) → find memory addresses
2. **Application Monitoring**: Track application state changes
3. **Automated Testing**: Verify UI updates
4. **Reverse Engineering**: Link visual behavior to code

## Architecture Decisions

### Component 1: Screen Capture

**Technology**: `mss` (fast, cross-platform) or `Pillow` (simpler, slower)

**Decision**: Use `mss` for performance
- Faster than Pillow
- Cross-platform
- Good for real-time capture

**Implementation**:
```python
import mss
sct = mss.mss()
monitor = {"top": y, "left": x, "width": w, "height": h}
screenshot = sct.grab(monitor)
```

### Component 2: Change Detection

**Methods**:
1. **Frame Difference**: Compare consecutive frames
2. **Template Matching**: Match known UI elements
3. **Color Detection**: Detect color changes
4. **OCR**: Extract text values

**Decision**: Multi-method approach
- Frame difference for general change detection
- Template matching for specific UI elements
- OCR for text extraction (optional, requires pytesseract)

**Implementation**:
```python
import cv2
import numpy as np

# Frame difference
diff = cv2.absdiff(frame1, frame2)
changed_pixels = np.sum(diff > threshold)
```

### Component 3: Value Extraction

**Methods**:
1. **OCR**: Extract text/numbers (pytesseract)
2. **Pixel Analysis**: Count pixels, detect patterns
3. **Template Matching**: Match known value displays

**Decision**: Start with pixel analysis, add OCR later
- Pixel analysis is faster and more reliable
- OCR requires additional dependencies
- Can combine both methods

### Component 4: Communication

**Options**:
- TCP Sockets (chosen)
- Message Queue (Redis/RabbitMQ)
- File-based (simpler but less real-time)

**Decision**: TCP Sockets
- Real-time communication
- Simple to implement
- Good for local components

**Protocol**: JSON messages
```json
{
  "type": "change_detected",
  "timestamp": "...",
  "coordinates": {"x": 100, "y": 200},
  "value": "1234",
  "region": "score_display"
}
```

### Component 5: MCP Integration

**MCP Tools to Add**:
- `start_visual_monitoring` - Start monitoring target window
- `stop_visual_monitoring` - Stop monitoring
- `get_detected_changes` - Get recent changes
- `set_monitoring_region` - Define region to monitor
- `extract_value_from_region` - Extract value from coordinates

**MCP Resources**:
- `reo://visual_analyzer_status` - Current monitoring status
- `reo://detected_changes` - Recent changes

## Implementation Plan

### Phase 1: Basic Screen Capture
1. Install dependencies (`mss`, `opencv-python`, `numpy`)
2. Implement screen capture for window/region
3. Save screenshots for testing

### Phase 2: Change Detection
1. Implement frame difference algorithm
2. Detect changed regions
3. Extract coordinates

### Phase 3: Value Extraction
1. Implement pixel analysis
2. Add OCR support (optional)
3. Extract numeric/text values

### Phase 4: Communication
1. Implement TCP socket server
2. Define message protocol
3. Integrate with Memory Scanner

### Phase 5: MCP Integration
1. Add MCP tools for visual analysis
2. Add MCP resources
3. Test end-to-end

## File Structure

```
src/
├── visual_analyzer/
│   ├── __init__.py
│   ├── screen_capture.py      # Screen capture using mss
│   ├── change_detector.py      # Change detection algorithms
│   ├── value_extractor.py      # Value extraction (pixel/OCR)
│   ├── region_manager.py       # Manage monitoring regions
│   ├── socket_server.py        # TCP communication
│   └── analyzer.py             # Main analyzer class
```

## Dependencies

```bash
pip install opencv-python mss numpy
# Optional: pip install pytesseract
```

## Configuration

```python
{
  "target_window": "Application Name",
  "monitoring_regions": [
    {"name": "score", "x": 100, "y": 200, "w": 200, "h": 50},
    {"name": "health", "x": 300, "y": 200, "w": 100, "h": 30}
  ],
  "change_threshold": 0.1,
  "capture_interval": 0.1,  # seconds
  "socket_port": 8888
}
```

## Performance Considerations

- **Capture Rate**: 10 FPS should be sufficient for most use cases
- **Change Threshold**: Configurable sensitivity
- **Memory Usage**: Store only recent frames (last 2-3)
- **CPU Usage**: Optimize image processing operations

## Security Considerations

- Only capture specified regions (not full screen)
- No data persistence (unless explicitly configured)
- Local communication only (TCP on localhost)

## Future Enhancements

1. **Machine Learning**: Train models to recognize UI elements
2. **Multi-Window**: Monitor multiple applications
3. **Recording**: Record sessions for later analysis
4. **Pattern Recognition**: Learn common UI patterns

## References

- OpenCV documentation
- mss library documentation
- ADR-001: Reverse Engineering Orchestrator
- ADR-006: Tool Integration Strategy

