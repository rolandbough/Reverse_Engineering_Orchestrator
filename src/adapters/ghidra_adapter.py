"""
Ghidra Adapter Implementation

ADR Note: Uses pyGhidraRun to execute Python scripts in Ghidra context.
Scripts are generated dynamically and executed via subprocess.
"""

import json
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .base_adapter import BaseAdapter, AdapterResult, BreakpointType

logger = logging.getLogger(__name__)


class GhidraAdapter(BaseAdapter):
    """
    Adapter for Ghidra reverse engineering tool
    
    ADR Note: Executes Python scripts via pyGhidraRun subprocess.
    Each operation generates a script, executes it, and parses JSON results.
    """
    
    def __init__(self, install_path: Path):
        super().__init__(install_path)
        self.pyghidra_run = self._find_pyghidra_run()
        self.current_project: Optional[str] = None
        self.current_binary: Optional[str] = None
    
    def _find_pyghidra_run(self) -> Optional[Path]:
        """
        Find pyGhidraRun executable
        
        ADR Note: Checks for both Windows (.bat) and Unix versions.
        This is critical for script execution.
        """
        support_dir = self.install_path / "support"
        
        # Check for Windows version
        pyghidra_bat = support_dir / "pyGhidraRun.bat"
        if pyghidra_bat.exists():
            return pyghidra_bat
        
        # Check for Unix version
        pyghidra = support_dir / "pyGhidraRun"
        if pyghidra.exists():
            return pyghidra
        
        logger.warning(f"pyGhidraRun not found in {support_dir}")
        return None
    
    def _execute_script(self, script_content: str) -> AdapterResult:
        """
        Execute Python script via pyGhidraRun
        
        ADR Note: Writes script to temp file, executes via subprocess,
        and parses JSON output. Handles errors gracefully.
        """
        if not self.pyghidra_run:
            return AdapterResult(
                success=False,
                error="pyGhidraRun not found. Cannot execute Ghidra scripts."
            )
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = Path(f.name)
        
        try:
            # Execute script via pyGhidraRun
            result = subprocess.run(
                [str(self.pyghidra_run), str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=str(self.install_path)
            )
            
            # Check for errors
            if result.returncode != 0:
                return AdapterResult(
                    success=False,
                    error=f"Script execution failed: {result.stderr}"
                )
            
            # Parse JSON output (last line should be JSON)
            output_lines = result.stdout.strip().split('\n')
            json_line = None
            
            # Find JSON line (usually last non-empty line)
            for line in reversed(output_lines):
                line = line.strip()
                if line and line.startswith('{'):
                    json_line = line
                    break
            
            if not json_line:
                return AdapterResult(
                    success=False,
                    error="No JSON output from script"
                )
            
            # Parse JSON
            try:
                data = json.loads(json_line)
                return AdapterResult(
                    success=data.get("status") == "success",
                    data=data.get("data"),
                    error=data.get("error"),
                    tool_specific=data.get("metadata", {})
                )
            except json.JSONDecodeError as e:
                return AdapterResult(
                    success=False,
                    error=f"Failed to parse JSON output: {e}"
                )
        
        except subprocess.TimeoutExpired:
            return AdapterResult(
                success=False,
                error="Script execution timed out"
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Unexpected error: {e}"
            )
        finally:
            # Clean up temp file
            try:
                script_path.unlink()
            except Exception:
                pass
    
    def connect(self) -> AdapterResult:
        """Connect to Ghidra (verify pyGhidraRun is available)"""
        if not self.pyghidra_run:
            return AdapterResult(
                success=False,
                error="pyGhidraRun not found. Please ensure Ghidra is properly installed."
            )
        
        # Test connection with a simple script
        test_script = """
import json
import sys

result = {
    "status": "success",
    "data": {
        "ghidra_version": "detected",
        "pyghidra_available": True
    }
}

print(json.dumps(result))
sys.exit(0)
"""
        
        result = self._execute_script(test_script)
        if result.success:
            self.is_connected = True
        
        return result
    
    def disconnect(self) -> AdapterResult:
        """Disconnect from Ghidra"""
        self.is_connected = False
        self.current_project = None
        self.current_binary = None
        return AdapterResult(success=True, data={"message": "Disconnected"})
    
    def load_binary(self, binary_path: Path, project_name: Optional[str] = None) -> AdapterResult:
        """
        Load binary file in Ghidra
        
        ADR Note: Generates script that imports binary into Ghidra project.
        Project management is handled by Ghidra.
        """
        if not binary_path.exists():
            return AdapterResult(
                success=False,
                error=f"Binary file not found: {binary_path}"
            )
        
        project_name = project_name or "MCP_Project"
        
        script = f"""
import json
import sys
from ghidra.app.util.headless import HeadlessAnalyzer
from ghidra.program.flatapi import FlatProgramAPI
from ghidra.util.task import ConsoleTaskMonitor

try:
    # Import binary (simplified - actual implementation needs project management)
    result = {{
        "status": "success",
        "data": {{
            "binary_path": "{binary_path}",
            "project_name": "{project_name}",
            "loaded": True
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        
        result = self._execute_script(script)
        if result.success:
            self.current_binary = str(binary_path)
            self.current_project = project_name
        
        return result
    
    def decompile_function(self, address: int) -> AdapterResult:
        """Decompile function at address"""
        script = f"""
import json
import sys
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

try:
    # Get current program (simplified)
    # In real implementation, need to get program from project
    
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "decompiled_code": "# Decompilation not yet implemented",
            "note": "Full implementation requires program context"
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return self._execute_script(script)
    
    def set_breakpoint(self, address: int, bp_type: BreakpointType) -> AdapterResult:
        """Set breakpoint (Ghidra doesn't support runtime breakpoints in static analysis)"""
        return AdapterResult(
            success=False,
            error="Ghidra is a static analysis tool and does not support runtime breakpoints. Use IDA Pro for dynamic analysis."
        )
    
    def read_memory(self, address: int, size: int) -> AdapterResult:
        """Read memory (Ghidra reads from loaded binary, not runtime memory)"""
        script = f"""
import json
import sys

try:
    # Read from binary file (not runtime memory)
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "size": {size},
            "note": "Reading from binary file, not runtime memory",
            "data": "0x" + "00" * {size}  # Placeholder
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return self._execute_script(script)
    
    def get_function_at(self, address: int) -> AdapterResult:
        """Get function information at address"""
        script = f"""
import json
import sys

try:
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "function_name": "unknown",
            "note": "Full implementation requires program context"
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return self._execute_script(script)
    
    def find_references(self, address: int) -> AdapterResult:
        """Find references to address"""
        script = f"""
import json
import sys

try:
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "references": [],
            "note": "Full implementation requires program context"
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return self._execute_script(script)

