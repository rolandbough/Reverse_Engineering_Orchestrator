# Using Decompiled Code to Locate Addresses

This tool helps you locate addresses in IDA Pro by cross-referencing exported decompiled code with the live IDA Pro database.

## Overview

The `locate_addresses_from_decomp.py` script:
1. Analyzes decompiled C/C++ files in a directory
2. Extracts function names and patterns
3. Matches them with functions in IDA Pro
4. Returns the corresponding addresses

## Usage

### Basic Usage

```bash
# Locate addresses for all functions in decompiled code
python locate_addresses_from_decomp.py <decomp_dir>

# Example:
python locate_addresses_from_decomp.py ./decomp
```

### Options

```bash
# Search for specific code pattern
python locate_addresses_from_decomp.py ./decomp --pattern "GetWindowText"

# Output results to JSON file
python locate_addresses_from_decomp.py ./decomp --output addresses.json

# Output as JSON to stdout
python locate_addresses_from_decomp.py ./decomp --json

# Use different IDA Pro RPC server
python locate_addresses_from_decomp.py ./decomp --rpc-url http://127.0.0.1:13337
```

## Finding Your Decomp Directory

If you're not sure where your decompiled code is:

```bash
python find_decomp_directory.py
```

This will search for common decompiled code directory names.

## How It Works

1. **Analyze Decompiled Files**: Scans `.c`, `.cpp`, `.h` files for function definitions
2. **Extract Function Names**: Uses regex to identify function names (including C++ namespaces/classes)
3. **Load IDA Functions**: Fetches all functions from IDA Pro via RPC
4. **Match and Map**: Matches function names and returns addresses

## Output Format

The script outputs a table showing:
- Function name (from decompiled code)
- Address in IDA Pro (hex)
- File and line number where found in decompiled code
- Match status (exact, short name, or not found)

## Example Output

```
Address Location Results:

Function Name                                    Address      File                           Line  
----------------------------------------------------------------------------------------------------
RemoveStarterDeckPrefixConverter::Convert        0x10         file1.c                       45    
Shiny.App::CheckForOurMinimumFramework           0x110        file2.c                        120   
SomeFunction                                      NOT FOUND    file3.c                        200   

Found 2/3 functions in IDA Pro
```

## Integration with IDA Pro

This works alongside:
- `query_ida_functions.py` - Direct IDA Pro RPC queries
- `ida-pro-mcp` - MCP server for Cursor integration
- Our Reverse Engineering Orchestrator MCP server

## Use Cases

1. **Function Address Mapping**: Find addresses of functions you see in decompiled code
2. **Code Pattern Location**: Search for specific code patterns and locate them
3. **Cross-Reference**: Bridge between exported decompiled code and live analysis
4. **Automation**: Generate address mappings for scripts or tools

## Requirements

- IDA Pro running with MCP plugin loaded
- Decompiled code files (C/C++ source files)
- Python 3.8+
- `requests` library (for RPC communication)

