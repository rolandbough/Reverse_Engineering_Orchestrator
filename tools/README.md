# External Tools Directory

This directory contains external reverse engineering tools that are not committed to the repository.

## Structure

- `ghidra/` - Ghidra installation directory
- `ida/` - IDA Pro installation directory (optional)

## Why Not Committed?

These tools are:
- Large binary distributions (100MB+)
- Platform-specific
- Licensed software (IDA Pro requires license)
- Should be installed per-developer

## Installation

See individual tool directories for installation instructions:
- [Ghidra README](ghidra/README.md)

## Detection

The Reverse Engineering Orchestrator will automatically detect tools installed in these directories. You can also set environment variables:

- `GHIDRA_INSTALL_DIR` - Path to Ghidra installation
- `IDA_PATH` - Path to IDA Pro installation

