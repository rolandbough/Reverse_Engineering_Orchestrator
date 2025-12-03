"""
Ghidra Detection

ADR Note: Ghidra detection focuses on installation directory and Python bridge
availability. Ghidra is Java-based, so detection is different from IDA Pro.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional

from .types import DetectionResult, ToolType

logger = logging.getLogger(__name__)


class GhidraDetector:
    """Detects Ghidra installation and availability"""
    
    def detect(self) -> DetectionResult:
        """
        Detect Ghidra using multiple methods
        
        ADR Note: Ghidra detection methods:
        1. Environment variable (GHIDRA_INSTALL_DIR)
        2. Common installation paths
        3. Python module (ghidra_bridge)
        4. Running Java process
        """
        # Method 1: Environment variable
        ghidra_dir = os.getenv("GHIDRA_INSTALL_DIR")
        if ghidra_dir and Path(ghidra_dir).exists():
            return self._create_result(
                install_path=Path(ghidra_dir),
                detection_method="environment_variable"
            )
        
        # Method 2: Common installation paths
        common_paths = self._get_common_paths()
        for path in common_paths:
            if path.exists() and self._is_ghidra_install(path):
                return self._create_result(
                    install_path=path,
                    detection_method="common_path"
                )
        
        # Method 3: Check for ghidra_bridge module
        if self._check_python_module():
            return DetectionResult(
                tool_type=ToolType.GHIDRA,
                is_available=True,
                python_module_available=True,
                detection_method="python_module",
                metadata={"note": "ghidra_bridge module found, but install path not detected"}
            )
        
        # Method 4: Check if Ghidra is running
        if self._check_running_process():
            return DetectionResult(
                tool_type=ToolType.GHIDRA,
                is_available=True,
                is_running=True,
                detection_method="running_process",
                metadata={"note": "Ghidra is running, but installation path not detected"}
            )
        
        # Not found
        return DetectionResult(
            tool_type=ToolType.GHIDRA,
            is_available=False,
            detection_method="none",
            error_message="Ghidra not found using any detection method"
        )
    
    def _get_common_paths(self) -> list[Path]:
        """
        Get common Ghidra installation paths
        
        ADR Note: Includes project-local tools directory for development.
        Checks project-relative path first, then system-wide locations.
        """
        paths = []
        
        # Project-local tools directory (for development)
        project_root = Path(__file__).parent.parent.parent.parent
        project_ghidra = project_root / "tools" / "ghidra"
        if project_ghidra.exists():
            paths.append(project_ghidra)
        
        if sys.platform == "win32":
            # Windows common paths
            paths.extend([
                Path("C:\\ghidra"),
                Path("C:\\Program Files\\ghidra"),
                Path("C:\\Program Files (x86)\\ghidra"),
                Path.home() / "ghidra",
            ])
        elif sys.platform == "darwin":
            # macOS common paths
            paths.extend([
                Path("/Applications/ghidra"),
                Path.home() / "ghidra",
            ])
        else:
            # Linux common paths
            paths.extend([
                Path("/opt/ghidra"),
                Path("/usr/local/ghidra"),
                Path.home() / "ghidra",
            ])
        
        return paths
    
    def _is_ghidra_install(self, path: Path) -> bool:
        """Check if path is a valid Ghidra installation"""
        # Look for key files/directories
        required_items = [
            path / "ghidraRun.bat",  # Windows
            path / "ghidraRun",      # Linux/macOS
            path / "support",        # Support directory
            path / "Ghidra",         # Main Ghidra directory
        ]
        
        # At least one should exist
        return any(item.exists() for item in required_items)
    
    def _check_python_module(self) -> bool:
        """Check if ghidra_bridge module is available"""
        try:
            import ghidra_bridge
            return True
        except ImportError:
            # Also check for direct Ghidra Python (if running in Ghidra)
            try:
                import ghidra
                return True
            except ImportError:
                return False
    
    def _check_running_process(self) -> bool:
        """Check if Ghidra process is running"""
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                    
                    # Check for Java process with Ghidra in command line
                    if 'java' in name and 'ghidra' in cmdline:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            logger.debug("psutil not available for process detection")
        except Exception as e:
            logger.debug(f"Process check failed: {e}")
        
        return False
    
    def _create_result(self, install_path: Path, detection_method: str) -> DetectionResult:
        """Create detection result with additional checks"""
        # Check if ghidra_bridge is available
        python_module_available = self._check_python_module()
        
        # Check if running
        is_running = self._check_running_process()
        
        # Try to get version
        version = self._get_version(install_path)
        
        return DetectionResult(
            tool_type=ToolType.GHIDRA,
            is_available=True,
            install_path=install_path,
            version=version,
            python_module_available=python_module_available,
            is_running=is_running,
            detection_method=detection_method
        )
    
    def _get_version(self, install_path: Path) -> Optional[str]:
        """Try to determine Ghidra version"""
        # Check for version in application.properties or similar
        app_props = install_path / "Ghidra" / "application.properties"
        if app_props.exists():
            try:
                with open(app_props, 'r') as f:
                    for line in f:
                        if 'application.version' in line.lower():
                            version = line.split('=')[1].strip()
                            return version
            except Exception:
                pass
        
        # Check directory name for version
        parent = install_path.parent
        if 'ghidra' in install_path.name.lower():
            # Look for version in path
            parts = install_path.name.split('_')
            for part in parts:
                if part.replace('.', '').isdigit():
                    return part
        
        return None

