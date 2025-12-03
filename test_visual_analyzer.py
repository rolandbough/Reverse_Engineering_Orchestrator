#!/usr/bin/env python3
"""
Test Visual Analyzer

Tests the OpenCV visual analyzer components.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_screen_capture():
    """Test screen capture"""
    print("Testing Screen Capture...")
    
    try:
        from src.visual_analyzer import ScreenCapture
        
        capture = ScreenCapture()
        
        # Test full screen capture
        print("  Capturing full screen...")
        screenshot = capture.capture_full_screen()
        
        if screenshot is not None:
            print(f"  ✅ Captured screenshot: {screenshot.shape}")
            
            # Test region capture
            print("  Capturing region (100x100 at 0,0)...")
            region = capture.capture_region(0, 0, 100, 100)
            if region is not None:
                print(f"  ✅ Captured region: {region.shape}")
                return True
            else:
                print("  ❌ Failed to capture region")
                return False
        else:
            print("  ❌ Failed to capture screenshot")
            return False
    
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  Install dependencies: pip install opencv-python mss numpy")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_change_detector():
    """Test change detection"""
    print("\nTesting Change Detector...")
    
    try:
        from src.visual_analyzer import ScreenCapture, ChangeDetector
        import numpy as np
        
        capture = ScreenCapture()
        detector = ChangeDetector(threshold=0.01)
        
        # Capture two frames
        print("  Capturing frame 1...")
        frame1 = capture.capture_region(0, 0, 200, 200)
        
        if frame1 is None:
            print("  ❌ Failed to capture frame 1")
            return False
        
        print("  Waiting 1 second...")
        time.sleep(1)
        
        print("  Capturing frame 2...")
        frame2 = capture.capture_region(0, 0, 200, 200)
        
        if frame2 is None:
            print("  ❌ Failed to capture frame 2")
            return False
        
        # Detect changes
        print("  Detecting changes...")
        result = detector.detect_changes(frame2, frame1)
        
        print(f"  ✅ Change detection result:")
        print(f"     Changed: {result.get('changed')}")
        print(f"     Change %: {result.get('change_percentage', 0):.2%}")
        print(f"     Regions: {len(result.get('changed_regions', []))}")
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_visual_analyzer():
    """Test main visual analyzer"""
    print("\nTesting Visual Analyzer...")
    
    try:
        from src.visual_analyzer import VisualAnalyzer
        
        analyzer = VisualAnalyzer(change_threshold=0.05, capture_interval=0.5)
        
        # Test single region analysis
        print("  Analyzing region (100x100 at 0,0)...")
        result = analyzer.analyze_region(0, 0, 100, 100, "test_region")
        
        print(f"  ✅ Analysis result:")
        print(f"     Region: {result.get('region_name')}")
        print(f"     Changed: {result.get('changed')}")
        print(f"     Change %: {result.get('change_percentage', 0):.2%}")
        
        # Test status
        status = analyzer.get_status()
        print(f"  ✅ Status: {status}")
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Visual Analyzer Test Suite\n")
    print("=" * 50)
    
    results = []
    
    results.append(("Screen Capture", test_screen_capture()))
    results.append(("Change Detector", test_change_detector()))
    results.append(("Visual Analyzer", test_visual_analyzer()))
    
    print("\n" + "=" * 50)
    print("Summary:")
    all_passed = all(result[1] for result in results)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        print("\nInstall dependencies:")
        print("  pip install opencv-python mss numpy")
        return 1

if __name__ == "__main__":
    sys.exit(main())

