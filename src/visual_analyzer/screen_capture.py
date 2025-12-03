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
        window_handle: Optional[int] = None,
        process_name: Optional[str] = None,
        process_id: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Capture a specific window
        
        ADR Note: Window capture uses platform-specific APIs to find windows.
        On Windows, uses win32gui to get window coordinates by process name/ID.
        
        Args:
            window_title: Window title to find
            window_handle: Window handle (Windows)
            process_name: Process name (e.g., "game.exe")
            process_id: Process ID (PID)
        
        Returns:
            NumPy array or None on error
        """
        import sys
        
        if sys.platform == "win32":
            return self._capture_window_windows(
                window_title, window_handle, process_name, process_id
            )
        else:
            logger.warning("Window capture by process not yet implemented for this platform")
            return None
    
    def _capture_window_windows(
        self,
        window_title: Optional[str],
        window_handle: Optional[int],
        process_name: Optional[str],
        process_id: Optional[int]
    ) -> Optional[np.ndarray]:
        """Capture window on Windows using win32gui"""
        try:
            import win32gui
            import win32process
        except ImportError:
            logger.error("win32gui not available. Install with: pip install pywin32")
            return None
        
        hwnd = None
        
        # Find window by process name or ID
        if process_name or process_id:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if process_id and pid == process_id:
                            windows.append(hwnd)
                        elif process_name:
                            # Get process name
                            try:
                                import psutil
                                proc = psutil.Process(pid)
                                if proc.name().lower() == process_name.lower():
                                    windows.append(hwnd)
                            except Exception:
                                pass
                    except Exception:
                        pass
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd = windows[0]  # Use first matching window
            else:
                logger.warning(f"Window not found for process: {process_name or process_id}")
                return None
        
        # Find window by title
        elif window_title:
            hwnd = win32gui.FindWindow(None, window_title)
            if not hwnd:
                logger.warning(f"Window not found with title: {window_title}")
                return None
        
        # Use provided handle
        elif window_handle:
            hwnd = window_handle
        
        if not hwnd:
            logger.error("No window handle found")
            return None
        
        # Get window rectangle
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Capture the window region
            return self.capture_region(left, top, width, height)
        
        except Exception as e:
            logger.error(f"Failed to capture window: {e}")
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
    
    def screenshot_to_base64(self, image: np.ndarray) -> Optional[str]:
        """
        Convert screenshot to base64 string for transmission
        
        ADR Note: Useful for sending screenshots via MCP or other protocols.
        Returns base64-encoded PNG image.
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available, cannot encode screenshot")
            return None
        
        try:
            import base64
            import io
            
            # Encode image as PNG
            success, buffer = cv2.imencode('.png', image)
            if not success:
                logger.error("Failed to encode image")
                return None
            
            # Convert to base64
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return img_base64
        
        except Exception as e:
            logger.error(f"Failed to convert screenshot to base64: {e}")
            return None
    
    def get_monitors(self) -> list:
        """Get list of available monitors"""
        return self.sct.monitors

