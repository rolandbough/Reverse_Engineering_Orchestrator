#!/usr/bin/env python3
"""
Locate Addresses from Decompiled Code

ADR Note: Cross-references decompiled code files with IDA Pro database
to locate addresses of functions, variables, or code patterns.
This helps bridge the gap between exported decompiled code and live IDA Pro analysis.
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Import our IDA Pro RPC client
from query_ida_functions import IDAProRPC


class DecompiledCodeAnalyzer:
    """
    Analyzes decompiled code files to extract function names and patterns
    
    ADR Note: Parses decompiled C/C++ code to identify function definitions,
    variable names, and code patterns that can be matched with IDA Pro addresses.
    """
    
    def __init__(self, decomp_dir: Path):
        self.decomp_dir = Path(decomp_dir)
        self.functions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def find_decomp_files(self) -> List[Path]:
        """Find all decompiled code files"""
        files = []
        
        # Common decompiled file patterns
        patterns = ["*.c", "*.cpp", "*.h", "*.cxx", "*.hpp", "*.txt"]
        
        for pattern in patterns:
            files.extend(self.decomp_dir.rglob(pattern))
        
        return files
    
    def extract_function_names(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract function names from decompiled code
        
        ADR Note: Uses regex to find function definitions. Handles various
        C/C++ function declaration patterns.
        """
        functions = []
        
        # Pattern for function definitions
        # Matches: return_type function_name(...) {
        pattern = r'(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "line": line_num,
                "file": str(file_path.relative_to(self.decomp_dir)),
                "match": match.group(0)[:100]  # First 100 chars
            })
        
        # Also try to find function declarations with class/namespace
        # Pattern: ClassName::FunctionName or namespace::function
        namespace_pattern = r'(\w+(?:::\w+)+)\s*\([^)]*\)\s*(?:const\s*)?\{'
        for match in re.finditer(namespace_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "line": line_num,
                "file": str(file_path.relative_to(self.decomp_dir)),
                "match": match.group(0)[:100]
            })
        
        return functions
    
    def analyze_decomp_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze all decompiled files and extract function information
        
        Returns:
            Dictionary mapping function names to their occurrences
        """
        files = self.find_decomp_files()
        
        if not files:
            print(f"⚠️  No decompiled files found in {self.decomp_dir}")
            return {}
        
        print(f"Found {len(files)} decompiled files")
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                functions = self.extract_function_names(content, file_path)
                
                for func in functions:
                    self.functions[func["name"]].append(func)
            
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
        
        return dict(self.functions)


class AddressLocator:
    """
    Locates addresses in IDA Pro based on decompiled code analysis
    
    ADR Note: Cross-references function names from decompiled code with
    IDA Pro database to find corresponding addresses. This enables mapping
    between exported decompiled code and live analysis.
    """
    
    def __init__(self, rpc: IDAProRPC):
        self.rpc = rpc
        self.ida_functions: Dict[str, Dict[str, Any]] = {}
    
    def load_ida_functions(self, limit: int = 0) -> Dict[str, Dict[str, Any]]:
        """
        Load all functions from IDA Pro
        
        ADR Note: Fetches functions from IDA Pro and indexes them by name
        for fast lookup when matching with decompiled code.
        """
        print("Loading functions from IDA Pro...")
        
        offset = 0
        all_functions = []
        
        while True:
            result = self.rpc.list_functions(offset=offset, count=100)
            items = result.get("data", result.get("items", []))
            
            if not items:
                break
            
            all_functions.extend(items)
            
            next_offset = result.get("next_offset")
            if next_offset is None or next_offset <= offset:
                break
            
            offset = next_offset
        
        # Index by name
        for func in all_functions:
            name = func.get("name", "")
            if name:
                # Handle both full names and short names
                self.ida_functions[name] = func
                
                # Also index by short name (after last ::)
                if "::" in name:
                    short_name = name.split("::")[-1]
                    if short_name not in self.ida_functions:
                        self.ida_functions[short_name] = func
        
        print(f"Loaded {len(all_functions)} functions from IDA Pro")
        return self.ida_functions
    
    def locate_functions(self, decomp_functions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Locate addresses for functions found in decompiled code
        
        ADR Note: Matches function names from decompiled code with IDA Pro
        functions and returns address mappings.
        """
        matches = []
        
        for func_name, occurrences in decomp_functions.items():
            # Try exact match first
            ida_func = self.ida_functions.get(func_name)
            
            if not ida_func:
                # Try short name match
                short_name = func_name.split("::")[-1] if "::" in func_name else func_name
                ida_func = self.ida_functions.get(short_name)
            
            if ida_func:
                for occ in occurrences:
                    matches.append({
                        "function_name": func_name,
                        "address": ida_func.get("address", "N/A"),
                        "size": ida_func.get("size", "N/A"),
                        "found_in_file": occ["file"],
                        "line_number": occ["line"],
                        "ida_name": ida_func.get("name", func_name),
                        "match_type": "exact" if func_name in self.ida_functions else "short"
                    })
            else:
                # No match found
                matches.append({
                    "function_name": func_name,
                    "address": "NOT FOUND",
                    "found_in_file": occurrences[0]["file"],
                    "line_number": occurrences[0]["line"],
                    "match_type": "none"
                })
        
        return matches
    
    def search_code_pattern(self, pattern: str, decomp_dir: Path) -> List[Dict[str, Any]]:
        """
        Search for code patterns in decompiled files and locate addresses
        
        ADR Note: Searches for specific code patterns (e.g., variable names,
        string literals, API calls) and attempts to locate them in IDA Pro.
        """
        results = []
        
        files = list(decomp_dir.rglob("*.c")) + list(decomp_dir.rglob("*.cpp"))
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Search for pattern
                for match in re.finditer(re.escape(pattern), content, re.IGNORECASE):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Try to find containing function
                    # Look backwards for function definition
                    before = content[:match.start()]
                    func_match = re.search(r'(\w+(?:::\w+)*)\s*\([^)]*\)\s*\{', before)
                    
                    func_name = func_match.group(1) if func_match else "unknown"
                    
                    results.append({
                        "pattern": pattern,
                        "file": str(file_path.relative_to(decomp_dir)),
                        "line": line_num,
                        "context": content[max(0, match.start()-50):match.end()+50],
                        "function": func_name
                    })
            
            except Exception as e:
                print(f"⚠️  Error searching {file_path}: {e}")
        
        return results


def format_matches(matches: List[Dict[str, Any]]) -> str:
    """Format address matches for display"""
    if not matches:
        return "No matches found."
    
    lines = ["Address Location Results:\n"]
    lines.append(f"{'Function Name':<50} {'Address':<12} {'File':<30} {'Line':<6}")
    lines.append("-" * 100)
    
    found_count = 0
    for match in matches:
        if match["address"] != "NOT FOUND":
            found_count += 1
            addr = match["address"]
            if isinstance(addr, int):
                addr = f"0x{addr:X}"
            elif isinstance(addr, str) and not addr.startswith("0x"):
                addr = f"0x{addr}"
            
            func_name = match["function_name"][:48]
            file_name = match["found_in_file"][:28]
            line = match["line_number"]
            
            lines.append(f"{func_name:<50} {addr:<12} {file_name:<30} {line:<6}")
        else:
            func_name = match["function_name"][:48]
            file_name = match["found_in_file"][:28]
            line = match["line_number"]
            lines.append(f"{func_name:<50} {'NOT FOUND':<12} {file_name:<30} {line:<6}")
    
    lines.append(f"\nFound {found_count}/{len(matches)} functions in IDA Pro")
    return "\n".join(lines)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Locate addresses in IDA Pro from decompiled code"
    )
    parser.add_argument("decomp_dir", type=Path,
                       help="Directory containing decompiled code files")
    parser.add_argument("--rpc-url", default="http://127.0.0.1:13337",
                       help="IDA Pro RPC server URL")
    parser.add_argument("--pattern", type=str,
                       help="Search for specific code pattern instead of functions")
    parser.add_argument("--output", type=Path,
                       help="Output JSON file for results")
    parser.add_argument("--json", action="store_true",
                       help="Output results as JSON")
    
    args = parser.parse_args()
    
    if not args.decomp_dir.exists():
        print(f"❌ Decompiled code directory not found: {args.decomp_dir}")
        sys.exit(1)
    
    # Connect to IDA Pro
    print("Connecting to IDA Pro...")
    rpc = IDAProRPC(args.rpc_url)
    
    if not rpc.check_connection():
        print("❌ Failed to connect to IDA Pro RPC server")
        sys.exit(1)
    
    print("✅ Connected to IDA Pro\n")
    
    # Create analyzer and locator
    analyzer = DecompiledCodeAnalyzer(args.decomp_dir)
    locator = AddressLocator(rpc)
    
    # Load IDA functions
    locator.load_ida_functions()
    print()
    
    # Analyze decompiled code
    if args.pattern:
        print(f"Searching for pattern: {args.pattern}")
        results = locator.search_code_pattern(args.pattern, args.decomp_dir)
        
        if args.json:
            output = json.dumps(results, indent=2)
        else:
            output = f"Found {len(results)} occurrences of pattern '{args.pattern}':\n"
            for result in results:
                output += f"\nFile: {result['file']}:{result['line']}\n"
                output += f"Function: {result['function']}\n"
                output += f"Context: ...{result['context']}...\n"
        
        print(output)
    
    else:
        print("Analyzing decompiled code files...")
        decomp_functions = analyzer.analyze_decomp_files()
        print(f"Found {len(decomp_functions)} unique function names in decompiled code\n")
        
        # Locate addresses
        print("Locating addresses in IDA Pro...")
        matches = locator.locate_functions(decomp_functions)
        
        if args.json or args.output:
            output = json.dumps(matches, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"\nResults saved to {args.output}")
            else:
                print(output)
        else:
            print(format_matches(matches))


if __name__ == "__main__":
    main()

