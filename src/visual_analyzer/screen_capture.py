"""
Screen Capture Module

ADR Note: Uses mss for fast, cross-platform screen capture.
Captures specific regions or full windows of target applications.
"""

import logging
from typing import Optional, Dict, Tuple
from pathlib import Path
import numpy as np

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logging.warning("mss not available. Install with: pip install mss")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python not available. Install with: pip install opencv-python")

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Screen capture using mss library
    
    ADR Note: mss is faster than Pillow and works cross-platform.
    Captures specific screen regions for analysis.
    """
    
    def __init__(self):
        """Initialize screen capture"""
        if not MSS_AVAILABLE:
            raise ImportError("mss library not installed. Install with: pip install mss")
        
        self.sct = mss.mss()
        self.last_screenshot: Optional[np.ndarray] = None
    
    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        monitor: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Capture a specific screen region
        
        Args:
            x: Left coordinate
            y: Top coordinate
            width: Region width
            height: Region height
            monitor: Monitor number (None for primary)
        
        Returns:
            NumPy array (BGR format for OpenCV) or None on error
        """
        try:
            if monitor is None:
                monitor = self.sct.monitors[0]  # Primary monitor
            
            # mss uses different coordinate system
            monitor_dict = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            # Capture screenshot
            screenshot = self.sct.grab(monitor_dict)
            
            # Convert to numpy array (BGR for OpenCV)
            img = np.array(screenshot)
            # mss returns BGRA, convert to BGR
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) if CV2_AVAILABLE else img[:, :, :3]
            
            self.last_screenshot = img
            return img
        
        except Exception as e:
            logger.error(f"Failed to capture region: {e}")
            return None
    
    def capture_window(
        self,
        window_title: Optional[str] = None,
        window_handle: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Capture a specific window
        
        ADR Note: Window capture requires platform-specific code.
        For now, this is a placeholder. Full implementation would use
        win32gui (Windows) or xdotool (Linux) to get window coordinates.
        
        Args:
            window_title: Window title to find
            window_handle: Window handle (Windows)
        
        Returns:
            NumPy array or None on error
        """
        # TODO: Implement window capture
        # Would need:
        # - Windows: win32gui to get window rect
        # - Linux: xdotool or similar
        # - macOS: AppleScript or similar
        
        logger.warning("Window capture not yet implemented. Use capture_region instead.")
        return None
    
    def capture_full_screen(self, monitor: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Capture full screen
        
        Args:
            monitor: Monitor number (None for primary)
        
        Returns:
            NumPy array or None on error
        """
        try:
            if monitor is None:
                monitor = self.sct.monitors[0]
            
            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) if CV2_AVAILABLE else img[:, :, :3]
            
            return img
        
        except Exception as e:
            logger.error(f"Failed to capture full screen: {e}")
            return None
    
    def save_screenshot(self, image: np.ndarray, path: Path) -> bool:
        """Save screenshot to file"""
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available, cannot save screenshot")
            return False
        
        try:
            cv2.imwrite(str(path), image)
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return False
    
    def get_monitors(self) -> list:
        """Get list of available monitors"""
        return self.sct.monitors

