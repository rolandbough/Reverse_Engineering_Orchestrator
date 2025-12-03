#!/usr/bin/env python3
"""
Test Ghidra Adapter

Tests the Ghidra adapter connection and basic functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.ghidra_adapter import GhidraAdapter
from src.tool_detection import ToolDetector

def main():
    print("Testing Ghidra Adapter\n")
    
    # Detect Ghidra
    detector = ToolDetector()
    detected = detector.detect_available()
    
    if not detected or detected.tool_type.value != "ghidra":
        print("❌ Ghidra not detected")
        print("   Please ensure Ghidra is installed in tools/ghidra/")
        return 1
    
    if not detected.install_path:
        print("❌ Ghidra detected but install path not found")
        return 1
    
    print(f"✅ Ghidra detected at: {detected.install_path}\n")
    
    # Create adapter
    adapter = GhidraAdapter(detected.install_path)
    
    # Test connection
    print("Testing connection...")
    result = adapter.connect()
    
    if result.success:
        print("✅ Connection successful")
        print(f"   Data: {result.data}")
    else:
        print(f"❌ Connection failed: {result.error}")
        return 1
    
    print("\n✅ Ghidra adapter is working!")
    print("\nNote: Full functionality requires a program to be loaded in Ghidra.")
    print("      Use Ghidra GUI or headless analyzer to load a binary first.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

