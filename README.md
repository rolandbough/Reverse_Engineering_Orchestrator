# Reverse Engineering Orchestrator

An MCP (Model Context Protocol) server that provides AI-powered reverse engineering capabilities to Cursor IDE, supporting both IDA Pro and Ghidra.

## Features

- **MCP Server Integration**: Works seamlessly with Cursor IDE via Model Context Protocol
- **Automatic Tool Detection**: Automatically detects and selects IDA Pro or Ghidra
- **Unified Interface**: Single API works with both reverse engineering tools
- **AI-Powered Analysis**: Leverage AI to analyze decompiled code and find patterns
- **Semantic Versioning**: Automatic version management (MAJOR.MINOR.PATCH)
- **Automated Commits**: Periodically commit and push changes to GitHub

## Architecture

The Reverse Engineering Orchestrator consists of:

1. **MCP Server**: Main server that communicates with Cursor via MCP protocol
2. **Tool Detection**: Automatic detection of IDA Pro or Ghidra
3. **Tool Adapters**: Unified interface for different RE tools
4. **MCP Tools**: Reverse engineering operations exposed as MCP tools
5. **MCP Resources**: System state exposed as MCP resources

See [documentation/ADR-001-reverse-engineering-orchestrator.md](documentation/ADR-001-reverse-engineering-orchestrator.md) for detailed architecture.

## Quick Start

### Prerequisites

- Python 3.8+
- Either IDA Pro (with IDAPython) or Ghidra installed
- Cursor IDE

### Installation

```bash
# Clone the repository
git clone https://github.com/rolandbough/Reverse_Engineering_Orchestrator.git
cd Reverse_Engineering_Orchestrator

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Configuration

Set environment variables (optional):

```bash
# For IDA Pro
export IDA_PATH="/path/to/ida"

# For Ghidra
export GHIDRA_INSTALL_DIR="/path/to/ghidra"

# Server configuration
export REO_LOG_LEVEL="INFO"
export REO_PREFERRED_TOOL="ida"  # or "ghidra"
```

### Running the MCP Server

```bash
# Run the server (will be configured in Cursor)
python -m src.mcp_server.server
```

### Cursor Configuration

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "reverse-engineering-orchestrator": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "env": {
        "REO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Tool Detection

The server automatically detects available tools using multiple methods:

### IDA Pro Detection
- Environment variable: `IDA_PATH`
- Windows Registry
- Common installation paths
- Python module: `idapython`
- Running processes

### Ghidra Detection
- Environment variable: `GHIDRA_INSTALL_DIR`
- Common installation paths
- Python module: `ghidra_bridge`
- Running Java processes

## Development

### Project Structure

```
src/
├── mcp_server/          # MCP server implementation
├── tool_detection/      # Tool detection system
├── adapters/            # Tool adapters (IDA, Ghidra)
├── tools/               # MCP tools implementation
└── utils/               # Utilities

documentation/
├── ADR-*.md            # Architecture Decision Records
├── IMPLEMENTATION_PLAN.md  # Detailed implementation plan
└── agent.md            # Agent directives
```

### Running Tests

```bash
pytest tests/
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Type checking
mypy src/

# Code formatting
black src/
```

## Documentation

- [Implementation Plan](documentation/IMPLEMENTATION_PLAN.md) - Detailed step-by-step plan
- [ADR-001: System Architecture](documentation/ADR-001-reverse-engineering-orchestrator.md)
- [ADR-002: Versioning and Automation](documentation/ADR-002-versioning-and-automation.md)
- [ADR-003: MCP Server Architecture](documentation/ADR-003-mcp-server-architecture.md)

## Status

🚧 **In Development** - Currently implementing Phase 1 (Foundation)

- [x] Project structure
- [x] Tool detection system
- [x] MCP server foundation
- [ ] MCP protocol implementation
- [ ] Tool adapters
- [ ] MCP tools
- [ ] Integration testing

## Contributing

See [documentation/agent.md](documentation/agent.md) for development guidelines and agent directives.

## License

[To be determined]
