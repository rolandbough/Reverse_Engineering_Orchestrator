"""
Change Detection Module

ADR Note: Detects visual changes in captured screenshots using
frame difference and other image processing techniques.
"""

import logging
from typing import Optional, Dict, List, Tuple
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python not available")

logger = logging.getLogger(__name__)


class ChangeDetector:
    """
    Detects changes between consecutive frames
    
    ADR Note: Uses frame difference algorithm. Can be extended with
    template matching, color detection, and other methods.
    """
    
    def __init__(self, threshold: float = 0.1, min_change_area: int = 100):
        """
        Initialize change detector
        
        Args:
            threshold: Change threshold (0.0-1.0), lower = more sensitive
            min_change_area: Minimum area of changed pixels to report
        """
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python not installed. Install with: pip install opencv-python")
        
        self.threshold = threshold
        self.min_change_area = min_change_area
        self.previous_frame: Optional[np.ndarray] = None
    
    def detect_changes(
        self,
        current_frame: np.ndarray,
        previous_frame: Optional[np.ndarray] = None
    ) -> Dict[str, any]:
        """
        Detect changes between frames
        
        Args:
            current_frame: Current frame (BGR numpy array)
            previous_frame: Previous frame (None to use stored)
        
        Returns:
            Dictionary with change information:
            {
                "changed": bool,
                "change_percentage": float,
                "changed_regions": [(x, y, w, h), ...],
                "change_mask": np.ndarray
            }
        """
        if previous_frame is None:
            previous_frame = self.previous_frame
        
        if previous_frame is None:
            # First frame, no comparison
            self.previous_frame = current_frame.copy()
            return {
                "changed": False,
                "change_percentage": 0.0,
                "changed_regions": [],
                "change_mask": None
            }
        
        # Ensure frames are same size
        if current_frame.shape != previous_frame.shape:
            logger.warning("Frame size mismatch, resizing previous frame")
            previous_frame = cv2.resize(previous_frame, (current_frame.shape[1], current_frame.shape[0]))
        
        # Convert to grayscale for comparison
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_previous = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray_current, gray_previous)
        
        # Apply threshold
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calculate change percentage
        total_pixels = thresh.size
        changed_pixels = np.sum(thresh > 0)
        change_percentage = changed_pixels / total_pixels
        
        # Find changed regions (contours)
        changed_regions = []
        if change_percentage > self.threshold:
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= self.min_change_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    changed_regions.append((x, y, w, h))
        
        # Update stored frame
        self.previous_frame = current_frame.copy()
        
        return {
            "changed": change_percentage > self.threshold,
            "change_percentage": float(change_percentage),
            "changed_regions": changed_regions,
            "change_mask": thresh
        }
    
    def detect_color_change(
        self,
        current_frame: np.ndarray,
        target_color: Tuple[int, int, int],
        tolerance: int = 10
    ) -> Dict[str, any]:
        """
        Detect changes in specific color
        
        ADR Note: Useful for detecting UI elements that change color
        (e.g., health bar, status indicators).
        
        Args:
            current_frame: Current frame (BGR)
            target_color: Target color (B, G, R)
            tolerance: Color matching tolerance
        
        Returns:
            Dictionary with color change information
        """
        # Create color mask
        lower = np.array([max(0, c - tolerance) for c in target_color])
        upper = np.array([min(255, c + tolerance) for c in target_color])
        
        mask = cv2.inRange(current_frame, lower, upper)
        
        # Find regions with target color
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.min_change_area:
                x, y, w, h = cv2.boundingRect(contour)
                regions.append((x, y, w, h))
        
        return {
            "found": len(regions) > 0,
            "regions": regions,
            "mask": mask
        }
    
    def template_match(
        self,
        current_frame: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8
    ) -> List[Tuple[int, int]]:
        """
        Find template in current frame
        
        ADR Note: Template matching for finding specific UI elements.
        
        Args:
            current_frame: Current frame
            template: Template image to find
            threshold: Match threshold (0.0-1.0)
        
        Returns:
            List of (x, y) coordinates where template was found
        """
        # Convert to grayscale
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
        
        # Template matching
        result = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for pt in zip(*locations[::-1]):  # Switch x and y
            matches.append(pt)
        
        return matches
    
    def reset(self):
        """Reset detector state"""
        self.previous_frame = None

