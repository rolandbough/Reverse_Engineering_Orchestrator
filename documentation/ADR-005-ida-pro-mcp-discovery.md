# ADR-005: IDA Pro MCP Package Discovery

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Discovered existing `ida-pro-mcp` package that provides MCP server functionality for IDA Pro.

## Decision

Install and evaluate `ida-pro-mcp` package as:
1. **Reference Implementation**: Learn from existing IDA Pro MCP integration
2. **Alternative Option**: May use directly if it meets requirements
3. **Integration Possibility**: Could integrate with our orchestrator

## Context

### Discovery
- Package: `ida-pro-mcp` version 1.4.0
- Provides: MCP server for IDA Pro
- Dependencies: Requires `mcp>=1.16.0` (newer than our initial requirement)

### Implications

**Positive:**
- Existing implementation we can learn from
- May provide IDA Pro integration we need
- Could simplify our IDA adapter implementation
- Proves MCP + IDA Pro integration is feasible

**Considerations:**
- Our orchestrator needs to support both IDA Pro AND Ghidra
- We want unified interface, not separate MCP servers
- May need to adapt their approach for our use case

## Architecture Impact

### Option 1: Use ida-pro-mcp Directly
- **Pros:** Ready-made solution, well-tested
- **Cons:** Only supports IDA Pro, doesn't fit our unified architecture

### Option 2: Learn and Adapt
- **Pros:** Keep our unified adapter architecture, learn best practices
- **Cons:** More work, but maintains our design goals

### Option 3: Hybrid Approach
- **Pros:** Use ida-pro-mcp for IDA Pro, our adapter for Ghidra, unified MCP server
- **Cons:** More complex integration

## Decision

**Use Option 2: Learn and Adapt**

**Rationale:**
- Our goal is a unified orchestrator supporting multiple tools
- We want consistent interface regardless of underlying tool
- Can learn from ida-pro-mcp implementation patterns
- Maintains our adapter architecture

## Action Items

1. ✅ Install ida-pro-mcp package
2. ⏳ Study ida-pro-mcp implementation
3. ⏳ Adapt best practices to our IDA adapter
4. ⏳ Update our MCP SDK version requirement (mcp>=1.16.0)
5. ⏳ Document integration patterns learned

## References

- ida-pro-mcp package: https://pypi.org/project/ida-pro-mcp/
- MCP SDK version: 1.23.1 (installed as dependency)

