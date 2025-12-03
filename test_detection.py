#!/usr/bin/env python3
"""
Quick test script for tool detection

ADR Note: This script allows testing the detection system without running
the full MCP server. Useful for development and debugging.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tool_detection import ToolDetector, ToolType

def main():
    print("Reverse Engineering Orchestrator - Tool Detection Test")
    print("=" * 60)
    
    detector = ToolDetector()
    
    # Detect all tools
    print("\nDetecting all tools...")
    all_results = detector.detect_all()
    
    for tool_type, result in all_results.items():
        print(f"\n{tool_type.value.upper()}:")
        print(f"  Available: {result.is_available}")
        if result.install_path:
            print(f"  Path: {result.install_path}")
        if result.version:
            print(f"  Version: {result.version}")
        if result.detection_method:
            print(f"  Detection Method: {result.detection_method}")
        if result.python_module_available:
            print(f"  Python Module: Available")
        if result.is_running:
            print(f"  Status: Running")
        if result.error_message:
            print(f"  Error: {result.error_message}")
    
    # Get available tool
    print("\n" + "=" * 60)
    print("Selecting available tool...")
    available = detector.detect_available()
    
    if available:
        print(f"\n✓ Selected: {available.tool_type.value}")
        print(f"  Path: {available.install_path}")
        print(f"  Version: {available.version or 'Unknown'}")
    else:
        print("\n✗ No reverse engineering tools detected")
        print("\nPlease ensure either IDA Pro or Ghidra is installed.")
        print("You can set environment variables:")
        print("  - IDA_PATH=/path/to/ida")
        print("  - GHIDRA_INSTALL_DIR=/path/to/ghidra")

if __name__ == "__main__":
    main()

