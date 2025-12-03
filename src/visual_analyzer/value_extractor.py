"""
Value Extraction Module

ADR Note: Extracts numeric and text values from screen regions.
Uses pixel analysis and optional OCR for text extraction.
"""

import logging
from typing import Optional, Dict, Any
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.debug("pytesseract not available. OCR features disabled.")

logger = logging.getLogger(__name__)


class ValueExtractor:
    """
    Extract values from screen regions
    
    ADR Note: Supports both pixel analysis (fast) and OCR (slower but more accurate).
    Pixel analysis is preferred for numeric displays, OCR for text.
    """
    
    def __init__(self, use_ocr: bool = False):
        """
        Initialize value extractor
        
        Args:
            use_ocr: Enable OCR for text extraction (requires pytesseract)
        """
        self.use_ocr = use_ocr and TESSERACT_AVAILABLE
        if use_ocr and not TESSERACT_AVAILABLE:
            logger.warning("OCR requested but pytesseract not available")
    
    def extract_value(
        self,
        image: np.ndarray,
        region: Optional[tuple] = None,
        value_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extract value from image region
        
        Args:
            image: Image (BGR numpy array)
            region: (x, y, w, h) region to extract from (None for full image)
            value_type: "auto", "number", "text", "pixel_count"
        
        Returns:
            Dictionary with extracted value:
            {
                "value": extracted value (str or int),
                "confidence": confidence score (0.0-1.0),
                "method": "pixel" or "ocr",
                "raw": raw extracted text
            }
        """
        # Crop to region if specified
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
        
        if value_type == "auto":
            # Try number first, then text
            result = self._extract_number(image)
            if result["value"] is None:
                result = self._extract_text(image)
        elif value_type == "number":
            result = self._extract_number(image)
        elif value_type == "text":
            result = self._extract_text(image)
        elif value_type == "pixel_count":
            result = self._extract_pixel_count(image)
        else:
            result = {"value": None, "confidence": 0.0, "method": "unknown", "raw": ""}
        
        return result
    
    def _extract_number(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract numeric value using OCR
        
        ADR Note: OCR is used for number extraction. For better performance
        with known number displays, could use template matching.
        """
        if not CV2_AVAILABLE:
            return {"value": None, "confidence": 0.0, "method": "pixel", "raw": ""}
        
        # Preprocess image for better OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Enhance contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
        
        # Try OCR if available
        if self.use_ocr:
            try:
                # OCR with digits-only config
                text = pytesseract.image_to_string(gray, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                text = text.strip()
                
                if text:
                    try:
                        value = int(text)
                        return {
                            "value": value,
                            "confidence": 0.8,  # OCR confidence estimation
                            "method": "ocr",
                            "raw": text
                        }
                    except ValueError:
                        pass
            except Exception as e:
                logger.debug(f"OCR extraction failed: {e}")
        
        # Fallback: pixel-based estimation
        # This is a simplified approach - could be improved
        return {"value": None, "confidence": 0.0, "method": "pixel", "raw": ""}
    
    def _extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using OCR"""
        if not self.use_ocr or not CV2_AVAILABLE:
            return {"value": None, "confidence": 0.0, "method": "ocr", "raw": ""}
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
            
            text = pytesseract.image_to_string(gray)
            text = text.strip()
            
            if text:
                return {
                    "value": text,
                    "confidence": 0.7,  # OCR confidence estimation
                    "method": "ocr",
                    "raw": text
                }
        except Exception as e:
            logger.debug(f"OCR text extraction failed: {e}")
        
        return {"value": None, "confidence": 0.0, "method": "ocr", "raw": ""}
    
    def _extract_pixel_count(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Count pixels (useful for progress bars, health bars, etc.)
        
        ADR Note: Counts non-black pixels. Useful for estimating
        progress/health percentages.
        """
        if not CV2_AVAILABLE:
            return {"value": None, "confidence": 0.0, "method": "pixel", "raw": ""}
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Count non-zero pixels
        total_pixels = gray.size
        non_zero = np.count_nonzero(gray)
        percentage = (non_zero / total_pixels) * 100
        
        return {
            "value": int(percentage),
            "confidence": 1.0,  # Pixel counting is deterministic
            "method": "pixel",
            "raw": f"{non_zero}/{total_pixels} pixels"
        }
    
    def extract_color_value(
        self,
        image: np.ndarray,
        region: Optional[tuple] = None,
        color: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Extract value based on color presence
        
        ADR Note: Useful for color-coded displays (e.g., red = danger, green = safe).
        """
        if not CV2_AVAILABLE:
            return {"value": None, "confidence": 0.0, "method": "color", "raw": ""}
        
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
        
        if color:
            # Count pixels matching color
            lower = np.array([max(0, c - 10) for c in color])
            upper = np.array([min(255, c + 10) for c in color])
            mask = cv2.inRange(image, lower, upper)
            count = np.sum(mask > 0)
            total = mask.size
            percentage = (count / total) * 100
            
            return {
                "value": int(percentage),
                "confidence": 0.9,
                "method": "color",
                "raw": f"{count}/{total} matching pixels"
            }
        
        # Extract dominant color
        # Reshape image to list of pixels
        pixels = image.reshape(-1, 3)
        # Get most common color
        unique, counts = np.unique(pixels, axis=0, return_counts=True)
        dominant_color = unique[np.argmax(counts)]
        
        return {
            "value": tuple(dominant_color),
            "confidence": 0.8,
            "method": "color",
            "raw": f"RGB{dominant_color}"
        }

