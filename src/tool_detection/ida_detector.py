"""
IDA Pro Detection

ADR Note: Multiple detection methods ensure IDA Pro is found regardless of
installation method. Checks environment variables, registry, common paths,
Python modules, and running processes.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional

from .detector import DetectionResult, ToolType

logger = logging.getLogger(__name__)


class IDADetector:
    """Detects IDA Pro installation and availability"""
    
    def detect(self) -> DetectionResult:
        """
        Detect IDA Pro using multiple methods
        
        ADR Note: Tries methods in order of reliability:
        1. Environment variable (most reliable, user-set)
        2. Windows registry (standard installation)
        3. Common paths (typical installations)
        4. Python module (idapython available)
        5. Running process (IDA is currently running)
        """
        # Method 1: Environment variable
        ida_path = os.getenv("IDA_PATH")
        if ida_path and Path(ida_path).exists():
            return self._create_result(
                install_path=Path(ida_path),
                detection_method="environment_variable"
            )
        
        # Method 2: Windows registry (Windows only)
        if sys.platform == "win32":
            registry_path = self._check_registry()
            if registry_path:
                return self._create_result(
                    install_path=Path(registry_path),
                    detection_method="windows_registry"
                )
        
        # Method 3: Common installation paths
        common_paths = self._get_common_paths()
        for path in common_paths:
            if path.exists():
                return self._create_result(
                    install_path=path,
                    detection_method="common_path"
                )
        
        # Method 4: Check for idapython module
        if self._check_python_module():
            return DetectionResult(
                tool_type=ToolType.IDA_PRO,
                is_available=True,
                python_module_available=True,
                detection_method="python_module",
                metadata={"note": "IDAPython module found, but IDA path not detected"}
            )
        
        # Method 5: Check if IDA is running
        if self._check_running_process():
            return DetectionResult(
                tool_type=ToolType.IDA_PRO,
                is_available=True,
                is_running=True,
                detection_method="running_process",
                metadata={"note": "IDA Pro is running, but installation path not detected"}
            )
        
        # Not found
        return DetectionResult(
            tool_type=ToolType.IDA_PRO,
            is_available=False,
            detection_method="none",
            error_message="IDA Pro not found using any detection method"
        )
    
    def _check_registry(self) -> Optional[str]:
        """Check Windows registry for IDA Pro installation"""
        try:
            import winreg
            # Common registry keys for IDA Pro
            registry_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Hex-Rays\IDA"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Hex-Rays\IDA"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Hex-Rays\IDA"),
            ]
            
            for hkey, key_path in registry_keys:
                try:
                    with winreg.OpenKey(hkey, key_path) as key:
                        # Try to get installation path
                        try:
                            install_path = winreg.QueryValueEx(key, "InstallDir")[0]
                            if Path(install_path).exists():
                                return install_path
                        except FileNotFoundError:
                            pass
                except FileNotFoundError:
                    continue
        except ImportError:
            logger.debug("winreg not available (not Windows)")
        except Exception as e:
            logger.debug(f"Registry check failed: {e}")
        
        return None
    
    def _get_common_paths(self) -> list[Path]:
        """Get common IDA Pro installation paths"""
        paths = []
        
        if sys.platform == "win32":
            # Windows common paths
            program_files = os.getenv("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.getenv("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            paths.extend([
                Path(program_files) / "IDA Pro",
                Path(program_files) / "IDA Pro 8.0",
                Path(program_files) / "IDA Pro 8.1",
                Path(program_files) / "IDA Pro 8.2",
                Path(program_files) / "IDA Pro 8.3",
                Path(program_files_x86) / "IDA Pro",
                Path(program_files_x86) / "IDA Pro 8.0",
                Path(program_files_x86) / "IDA Pro 8.1",
                Path(program_files_x86) / "IDA Pro 8.2",
                Path(program_files_x86) / "IDA Pro 8.3",
            ])
        elif sys.platform == "darwin":
            # macOS common paths
            paths.extend([
                Path("/Applications/IDA Pro.app"),
                Path.home() / "Applications" / "IDA Pro.app",
            ])
        else:
            # Linux common paths
            paths.extend([
                Path("/opt/ida"),
                Path("/usr/local/ida"),
                Path.home() / "ida",
            ])
        
        return paths
    
    def _check_python_module(self) -> bool:
        """Check if idapython module is available"""
        try:
            import idaapi
            return True
        except ImportError:
            return False
    
    def _check_running_process(self) -> bool:
        """Check if IDA Pro process is running"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name'].lower()
                    if 'ida' in name and ('exe' in name or 'app' in name):
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
        # Check if idapython is available
        python_module_available = self._check_python_module()
        
        # Check if running
        is_running = self._check_running_process()
        
        # Try to get version
        version = self._get_version(install_path)
        
        return DetectionResult(
            tool_type=ToolType.IDA_PRO,
            is_available=True,
            install_path=install_path,
            version=version,
            python_module_available=python_module_available,
            is_running=is_running,
            detection_method=detection_method
        )
    
    def _get_version(self, install_path: Path) -> Optional[str]:
        """Try to determine IDA Pro version"""
        # Check for version file or executable
        ida_exe = install_path / "ida.exe"
        ida64_exe = install_path / "ida64.exe"
        
        if ida_exe.exists() or ida64_exe.exists():
            # Try to get version from executable
            try:
                import subprocess
                exe = ida64_exe if ida64_exe.exists() else ida_exe
                result = subprocess.run(
                    [str(exe), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        
        return None

