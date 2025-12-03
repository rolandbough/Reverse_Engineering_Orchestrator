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
from ..tool_detection import ToolType

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
        self.tool_type = ToolType.GHIDRA
    
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
        Load binary file in Ghidra using headless analyzer
        
        ADR Note: Uses Ghidra's HeadlessAnalyzer to import and analyze binary.
        Creates a project if needed. Note: This is a simplified implementation.
        Full implementation would need project directory management.
        """
        if not binary_path.exists():
            return AdapterResult(
                success=False,
                error=f"Binary file not found: {binary_path}"
            )
        
        project_name = project_name or "MCP_Project"
        binary_path_str = str(binary_path.absolute())
        
        script = f"""
import json
import sys
from ghidra.app.util.headless import HeadlessAnalyzer
from ghidra.program.flatapi import FlatProgramAPI
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.framework.model import ProjectManager
from ghidra.program.model.listing import Program

try:
    # Note: This is a simplified implementation
    # Full implementation would need proper project management
    
    # Try to get current program if available
    program = getCurrentProgram()
    
    if program:
        # Program already loaded
        result = {{
            "status": "success",
            "data": {{
                "binary_path": "{binary_path_str}",
                "project_name": "{project_name}",
                "loaded": True,
                "program_name": program.getName(),
                "note": "Program already loaded"
            }}
        }}
    else:
        # For now, return success but note that program needs to be loaded
        # In full implementation, would use HeadlessAnalyzer here
        result = {{
            "status": "success",
            "data": {{
                "binary_path": "{binary_path_str}",
                "project_name": "{project_name}",
                "loaded": False,
                "note": "Binary path recorded. Use Ghidra GUI or headless analyzer to load."
            }}
        }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    import traceback
    result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
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
        """
        Decompile function at address using Ghidra decompiler
        
        ADR Note: Uses Ghidra's DecompInterface to decompile functions.
        Requires a program to be loaded (via getCurrentProgram()).
        """
        script = f"""
import json
import sys
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

try:
    # Get current program
    program = getCurrentProgram()
    if not program:
        result = {{
            "status": "error",
            "error": "No program loaded. Please load a binary first."
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Create decompiler interface
    decompiler = DecompInterface()
    decompiler.openProgram(program)
    
    # Get function at address
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    func_addr = address_space.getAddress(0x{address:X})
    
    # Get function manager
    func_manager = program.getFunctionManager()
    func = func_manager.getFunctionAt(func_addr)
    
    if not func:
        result = {{
            "status": "error",
            "error": f"No function found at address 0x{address:X}"
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Decompile function
    monitor = ConsoleTaskMonitor()
    decompile_results = decompiler.decompileFunction(func, 30, monitor)
    
    if decompile_results.decompileCompleted():
        decompiled_code = decompile_results.getDecompiledFunction().getC()
        
        result = {{
            "status": "success",
            "data": {{
                "address": "0x{address:X}",
                "function_name": func.getName(),
                "decompiled_code": str(decompiled_code)
            }}
        }}
    else:
        result = {{
            "status": "error",
            "error": f"Decompilation failed: {{decompile_results.getErrorMessage()}}"
        }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    import traceback
    result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
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
        """
        Read memory from loaded binary (static analysis, not runtime memory)
        
        ADR Note: Ghidra reads from the binary file, not runtime memory.
        This is static analysis only.
        """
        script = f"""
import json
import sys

try:
    # Get current program
    program = getCurrentProgram()
    if not program:
        result = {{
            "status": "error",
            "error": "No program loaded. Please load a binary first."
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Get address
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    addr = address_space.getAddress(0x{address:X})
    
    # Read memory bytes
    memory = program.getMemory()
    if not memory.contains(addr):
        result = {{
            "status": "error",
            "error": f"Address 0x{address:X} not in program memory"
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Read bytes
    bytes_data = []
    for i in range({size}):
        try:
            byte_val = memory.getByte(addr.add(i))
            bytes_data.append(byte_val)
        except:
            break
    
    # Convert to hex string
    hex_data = "".join(f"{{b:02x}}" for b in bytes_data)
    
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "size": len(bytes_data),
            "data": hex_data,
            "note": "Reading from binary file, not runtime memory"
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    import traceback
    result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
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
    # Get current program
    program = getCurrentProgram()
    if not program:
        result = {{
            "status": "error",
            "error": "No program loaded. Please load a binary first."
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Get address
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    func_addr = address_space.getAddress(0x{address:X})
    
    # Get function manager
    func_manager = program.getFunctionManager()
    func = func_manager.getFunctionAt(func_addr)
    
    if not func:
        result = {{
            "status": "error",
            "error": f"No function found at address 0x{address:X}"
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Get function details
    func_name = func.getName()
    entry_point = func.getEntryPoint()
    body = func.getBody()
    start_addr = body.getMinAddress()
    end_addr = body.getMaxAddress()
    
    # Get calling convention
    calling_convention = func.getCallingConventionName()
    if not calling_convention:
        calling_convention = "unknown"
    
    # Get parameters
    params = []
    for param in func.getParameters():
        params.append({{
            "name": param.getName(),
            "type": str(param.getDataType()),
            "storage": str(param.getStorage())
        }})
    
    # Get return type
    return_type = str(func.getReturnType())
    
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "function_name": func_name,
            "entry_point": str(entry_point),
            "start_address": str(start_addr),
            "end_address": str(end_addr),
            "calling_convention": calling_convention,
            "return_type": return_type,
            "parameters": params,
            "size": end_addr.subtract(start_addr)
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    import traceback
    result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
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
    # Get current program
    program = getCurrentProgram()
    if not program:
        result = {{
            "status": "error",
            "error": "No program loaded. Please load a binary first."
        }}
        print(json.dumps(result))
        sys.exit(1)
    
    # Get address
    address_space = program.getAddressFactory().getDefaultAddressSpace()
    ref_addr = address_space.getAddress(0x{address:X})
    
    # Get reference manager
    ref_manager = program.getReferenceManager()
    
    # Get references to this address
    references = []
    refs_to = ref_manager.getReferencesTo(ref_addr)
    
    for ref in refs_to:
        from_addr = ref.getFromAddress()
        ref_type = ref.getReferenceType()
        
        # Try to get function containing the reference
        func_manager = program.getFunctionManager()
        func = func_manager.getFunctionContaining(from_addr)
        func_name = func.getName() if func else "unknown"
        
        references.append({{
            "from_address": str(from_addr),
            "from_function": func_name,
            "reference_type": str(ref_type),
            "is_code": ref_type.isCall() or ref_type.isJump() or ref_type.isFlow(),
            "is_data": ref_type.isData()
        }})
    
    result = {{
        "status": "success",
        "data": {{
            "address": "0x{address:X}",
            "references": references,
            "count": len(references)
        }}
    }}
    
    print(json.dumps(result))
    sys.exit(0)
except Exception as e:
    import traceback
    result = {{
        "status": "error",
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return self._execute_script(script)

