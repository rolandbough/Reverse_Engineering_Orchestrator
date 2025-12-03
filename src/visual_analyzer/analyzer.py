"""
Main Visual Analyzer

ADR Note: Coordinates screen capture, change detection, and value extraction.
Main entry point for visual analysis operations.
"""

import logging
import threading
import time
from typing import Optional, Dict, List, Any
from pathlib import Path

from .screen_capture import ScreenCapture
from .change_detector import ChangeDetector
from .value_extractor import ValueExtractor

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """
    Main visual analyzer class
    
    ADR Note: Coordinates all visual analysis components. Can run in
    background thread for continuous monitoring or on-demand for single captures.
    """
    
    def __init__(
        self,
        change_threshold: float = 0.1,
        capture_interval: float = 0.1,
        use_ocr: bool = False
    ):
        """
        Initialize visual analyzer
        
        Args:
            change_threshold: Change detection threshold (0.0-1.0)
            capture_interval: Time between captures (seconds)
            use_ocr: Enable OCR for text extraction
        """
        self.screen_capture = ScreenCapture()
        self.change_detector = ChangeDetector(threshold=change_threshold)
        self.value_extractor = ValueExtractor(use_ocr=use_ocr)
        
        self.capture_interval = capture_interval
        self.monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        self.monitoring_regions: List[Dict[str, Any]] = []
        self.detected_changes: List[Dict[str, Any]] = []
        self.max_changes_history = 100
    
    def start_monitoring(
        self,
        regions: List[Dict[str, Any]],
        callback: Optional[callable] = None
    ) -> bool:
        """
        Start continuous monitoring
        
        Args:
            regions: List of regions to monitor:
                [{"name": "score", "x": 100, "y": 200, "w": 200, "h": 50}, ...]
            callback: Optional callback function for detected changes
        
        Returns:
            True if monitoring started successfully
        """
        if self.monitoring:
            logger.warning("Monitoring already in progress")
            return False
        
        self.monitoring_regions = regions
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    for region in self.monitoring_regions:
                        result = self.analyze_region(
                            region["x"],
                            region["y"],
                            region["w"],
                            region["h"],
                            region.get("name", "unknown")
                        )
                        
                        if result.get("changed") and callback:
                            callback(result)
                        
                        if result.get("changed"):
                            self.detected_changes.append(result)
                            # Keep only recent changes
                            if len(self.detected_changes) > self.max_changes_history:
                                self.detected_changes.pop(0)
                    
                    time.sleep(self.capture_interval)
                
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(self.capture_interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"Started monitoring {len(regions)} regions")
        return True
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        self.change_detector.reset()
        logger.info("Stopped monitoring")
    
    def analyze_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        region_name: str = "region"
    ) -> Dict[str, Any]:
        """
        Analyze a single region
        
        Args:
            x, y, width, height: Region coordinates
            region_name: Name for this region
        
        Returns:
            Dictionary with analysis results:
            {
                "region_name": str,
                "coordinates": {"x": int, "y": int, "w": int, "h": int},
                "changed": bool,
                "change_percentage": float,
                "extracted_value": {...},
                "timestamp": str
            }
        """
        # Capture region
        frame = self.screen_capture.capture_region(x, y, width, height)
        if frame is None:
            return {
                "region_name": region_name,
                "error": "Failed to capture region",
                "changed": False
            }
        
        # Detect changes
        change_info = self.change_detector.detect_changes(frame)
        
        # Extract value if changed
        extracted_value = None
        if change_info.get("changed"):
            extracted_value = self.value_extractor.extract_value(frame)
        
        result = {
            "region_name": region_name,
            "coordinates": {"x": x, "y": y, "w": width, "h": height},
            "changed": change_info.get("changed", False),
            "change_percentage": change_info.get("change_percentage", 0.0),
            "changed_regions": change_info.get("changed_regions", []),
            "extracted_value": extracted_value,
            "timestamp": time.time()
        }
        
        return result
    
    def get_detected_changes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of detected changes"""
        changes = self.detected_changes
        if limit:
            changes = changes[-limit:]
        return changes
    
    def clear_history(self):
        """Clear detected changes history"""
        self.detected_changes = []
    
    def capture_process_window(
        self,
        process_name: Optional[str] = None,
        process_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Capture full window of a process
        
        ADR Note: Captures the entire window of a target process.
        Returns screenshot and window information.
        
        Args:
            process_name: Process name (e.g., "game.exe")
            process_id: Process ID (PID)
        
        Returns:
            Dictionary with screenshot data and window info, or None on error
        """
        screenshot = self.screen_capture.capture_window(
            process_name=process_name,
            process_id=process_id
        )
        
        if screenshot is None:
            return None
        
        # Convert to base64 for transmission
        screenshot_base64 = self.screen_capture.screenshot_to_base64(screenshot)
        
        return {
            "screenshot_base64": screenshot_base64,
            "width": screenshot.shape[1],
            "height": screenshot.shape[0],
            "process_name": process_name,
            "process_id": process_id,
            "format": "png"
        }
    
    def save_screenshot(self, image: np.ndarray, path: Path) -> bool:
        """Save screenshot to file"""
        return self.screen_capture.save_screenshot(image, path)
    
    def select_region_interactive(
        self,
        screenshot_base64: Optional[str] = None,
        image: Optional[np.ndarray] = None,
        window_name: str = "Select Region - Click and drag, then press SPACE or ENTER"
    ) -> Optional[Dict[str, Any]]:
        """
        Interactively select a region from a screenshot
        
        ADR Note: Uses OpenCV's selectROI to display image and allow user to
        drag a rectangle to select region. This is more user-friendly than
        manually entering coordinates.
        
        Args:
            screenshot_base64: Base64-encoded screenshot (alternative to image)
            image: NumPy array image (alternative to screenshot_base64)
            window_name: Name of the selection window
        
        Returns:
            Dictionary with selected region coordinates, or None if cancelled
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available, cannot show interactive selector")
            return None
        
        import cv2
        import base64
        
        # Get image from either source
        if image is not None:
            img = image.copy()
        elif screenshot_base64:
            try:
                img_data = base64.b64decode(screenshot_base64)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    logger.error("Failed to decode screenshot")
                    return None
            except Exception as e:
                logger.error(f"Failed to decode screenshot: {e}")
                return None
        else:
            logger.error("No image or screenshot_base64 provided")
            return None
        
        # Use OpenCV's selectROI for interactive selection
        try:
            # selectROI returns (x, y, width, height) or empty tuple if cancelled
            roi = cv2.selectROI(window_name, img, showCrosshair=True, fromCenter=False)
            
            if roi == (0, 0, 0, 0):
                # User pressed ESC or closed window
                logger.info("Region selection cancelled")
                return None
            
            x, y, width, height = roi
            
            # Destroy the window
            cv2.destroyAllWindows()
            
            return {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
                "region_name": "interactive_selection",
                "ready_for_monitoring": True
            }
        
        except Exception as e:
            logger.error(f"Error in interactive region selection: {e}")
            cv2.destroyAllWindows()
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current analyzer status"""
        return {
            "monitoring": self.monitoring,
            "regions_count": len(self.monitoring_regions),
            "changes_detected": len(self.detected_changes),
            "capture_interval": self.capture_interval,
            "change_threshold": self.change_detector.threshold
        }

