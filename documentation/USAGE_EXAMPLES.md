# Usage Examples

Practical examples of using the Reverse Engineering Orchestrator MCP server in Cursor.

## Basic Operations

### 1. Detect Available Tools

**Prompt:**
```
What reverse engineering tools are available? Use the detect_re_tool MCP tool.
```

**Expected Response:**
The AI will call `detect_re_tool` and report which tools (IDA Pro or Ghidra) are available.

### 2. Get Tool Status

**Prompt:**
```
What's the current status of the reverse engineering tool? Check the tool_status resource.
```

**Expected Response:**
Returns connection status, current tool, and database information.

## Working with Functions

### 3. Decompile a Function

**Prompt:**
```
Decompile the function at address 0x401000
```

**What Happens:**
1. AI calls `detect_re_tool` to ensure tool is available
2. AI calls `decompile_function` with address `0x401000`
3. Returns decompiled C-like code

**Example Response:**
```
Decompiled code for function at 0x401000:

int __cdecl main(int argc, char **argv)
{
  // ... decompiled code ...
}
```

### 4. Get Function Information

**Prompt:**
```
Get detailed information about the function at address 0x404000
```

**What Happens:**
- Calls `get_function_info` with the address
- Returns function name, size, parameters, return type, etc.

### 5. Find References to a Function

**Prompt:**
```
Find all places that call or reference the function at 0x401000
```

**What Happens:**
- Calls `find_references` with the address
- Returns list of all code/data references

## Working with Binaries

### 6. Load a Binary

**Prompt:**
```
Load the binary file at C:\path\to\binary.exe for analysis
```

**What Happens:**
- Calls `load_binary` with the file path
- For IDA Pro: Checks if already loaded
- For Ghidra: Attempts to import into project

### 7. Read Memory

**Prompt:**
```
Read 16 bytes of memory starting at address 0x404000
```

**What Happens:**
- Calls `read_memory` with address and size
- Returns hex dump of memory contents

## Advanced Workflows

### 8. Analyze a Function Call Chain

**Prompt:**
```
Analyze the function at 0x401000. Show me:
1. What functions it calls
2. What functions call it
3. Decompile the main function
```

**What Happens:**
- Multiple MCP tool calls:
  1. `get_function_info` - Get function details
  2. `find_references` - Find callers
  3. `decompile_function` - Get source code

### 9. Cross-Reference Analysis

**Prompt:**
```
Find all references to address 0x404000 and decompile each function that references it
```

**What Happens:**
- Calls `find_references` to get all references
- For each reference, calls `get_function_info` and `decompile_function`

### 10. Memory Pattern Search

**Prompt:**
```
Read memory at 0x401000, 0x402000, and 0x403000. Compare the patterns.
```

**What Happens:**
- Multiple `read_memory` calls
- AI analyzes and compares the results

## IDA Pro Specific

### 11. Set Breakpoint (IDA Pro Only)

**Prompt:**
```
Set a software breakpoint at address 0x401000 in IDA Pro
```

**Note**: Requires IDA Pro with debugger. Ghidra doesn't support breakpoints (static analysis only).

### 12. Switch Between Tools

**Prompt:**
```
Switch to using Ghidra instead of IDA Pro
```

**What Happens:**
- Calls `detect_re_tool` with `preferred_tool: "ghidra"`
- Server switches to Ghidra adapter

## Integration with Decompiled Code

### 13. Locate Address from Decompiled Code

**Prompt:**
```
I have decompiled code in the ./decomp directory. Find the addresses of all functions.
```

**What Happens:**
- Uses `locate_addresses_from_decomp.py` script
- Cross-references decompiled function names with IDA Pro/Ghidra database
- Returns address mappings

### 14. Search for Code Pattern

**Prompt:**
```
Search for the pattern "GetWindowText" in the decompiled code and find its address
```

**What Happens:**
- Uses `locate_addresses_from_decomp.py --pattern "GetWindowText"`
- Finds occurrences in decompiled files
- Maps to addresses in IDA Pro/Ghidra

## Error Handling Examples

### 15. Handle Missing Tool

**Prompt:**
```
Decompile function at 0x401000
```

**If no tool available:**
```
Error: No reverse engineering tools detected. Please install IDA Pro or Ghidra.
```

**Solution Prompt:**
```
Check what tools are available and guide me through installation
```

### 16. Handle Connection Issues

**Prompt:**
```
Decompile function at 0x401000
```

**If IDA Pro not running:**
```
Error: Cannot connect to IDA Pro RPC server. Make sure IDA Pro is running with MCP plugin loaded.
```

**Solution Prompt:**
```
How do I start the IDA Pro MCP server?
```

## Best Practices

### 1. Always Detect Tool First

**Good:**
```
First detect available tools, then decompile function at 0x401000
```

**Better:**
The AI should automatically call `detect_re_tool` if not already done.

### 2. Use Specific Addresses

**Good:**
```
Decompile the function
```

**Better:**
```
Decompile the function at address 0x401000
```

### 3. Chain Operations

**Good:**
```
Get function info, then decompile, then find references
```

**Better:**
```
Analyze the function at 0x401000: get its info, decompile it, and find all references to it
```

## Tips for Effective Use

1. **Be Specific**: Provide exact addresses when possible
2. **Chain Operations**: Ask for multiple related operations in one prompt
3. **Use Resources**: Check `tool_status` resource for current state
4. **Handle Errors**: Ask the AI to help troubleshoot errors
5. **Explore**: Try different combinations of tools to discover capabilities

## Future Enhancements

As we add more tools, examples will include:
- OpenCV visual analysis
- Memory scanner integration
- Automated reverse engineering workflows
- Pattern recognition and analysis

