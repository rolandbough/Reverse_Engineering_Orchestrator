# ADR-002: Versioning and Automated Commit System

**Status:** Implemented  
**Date:** 2025-01-27  
**Deciders:** User, AI Agent  
**Context:** Need automated versioning and periodic commits to GitHub repository.

## Decision

Implement a multi-layered automation system:
1. Python-based version manager with semantic versioning
2. Automated commit and push scripts
3. GitHub Actions workflow for CI/CD automation
4. Windows Task Scheduler integration for local automation

## Context

### Requirement
- Automated versioning system
- Periodic automatic commits and pushes to GitHub
- Support for both local (Windows) and cloud (GitHub Actions) automation

### Questions Asked

**Q1: What versioning scheme?**
- **Answer:** Semantic Versioning (MAJOR.MINOR.PATCH)
- **Rationale:** Industry standard, clear meaning for version bumps

**Q2: How to automate commits?**
- **Answer:** Python script that can be scheduled locally or run via GitHub Actions
- **Rationale:** Python provides cross-platform compatibility and easy integration

**Q3: What about Windows-specific automation?**
- **Answer:** Provide both PowerShell and batch scripts for Task Scheduler
- **Rationale:** Windows users may prefer native scheduling tools

## Architecture Decisions

### Component 1: Version Manager (`version_manager.py`)
- **Purpose:** Manage semantic versioning and git operations
- **Features:**
  - Read/write VERSION file
  - Bump patch/minor/major versions
  - Automated commits with configurable messages
  - Tag creation and pushing
- **Decision Rationale:** Single script handles all versioning and git operations. Command-line interface allows flexibility.

### Component 2: Configuration (`automation_config.json`)
- **Purpose:** Centralized configuration for automation behavior
- **Settings:**
  - Auto-commit and auto-push flags
  - Commit message templates
  - Minimum changes threshold
  - Excluded file paths
- **Decision Rationale:** JSON is human-readable and easy to modify. Separates configuration from code.

### Component 3: GitHub Actions Workflow (`.github/workflows/auto-commit.yml`)
- **Purpose:** Cloud-based automation that runs on schedule
- **Schedule:** Every hour via cron
- **Features:**
  - Checks for changes
  - Commits and pushes automatically
  - Creates version tags when VERSION file changes
- **Decision Rationale:** GitHub Actions provides reliable cloud execution without local machine dependencies.

### Component 4: Windows Automation Scripts
- **Files:**
  - `automate.ps1` - PowerShell script
  - `automate.bat` - Batch script for compatibility
  - `setup_scheduler.ps1` - Task Scheduler setup
- **Decision Rationale:** Multiple options accommodate different Windows environments and user preferences.

## Consequences

### Positive
- Automated versioning reduces manual errors
- Regular commits provide backup and history
- Multiple automation methods (local + cloud) provide redundancy
- Configuration file allows easy customization

### Negative
- Automated commits may create noise in git history
- Need to ensure automation doesn't commit sensitive data
- Requires Python and git to be available

### Risks
- Accidental commits of unwanted files
- Version conflicts if multiple systems run simultaneously
- GitHub Actions may have rate limits

## Implementation Notes

- Version file (`VERSION`) uses simple format: `MAJOR.MINOR.PATCH`
- Git operations use subprocess to maintain compatibility
- Excluded paths prevent committing build artifacts and logs
- Logging to `automation.log` for debugging (excluded from git)

## Future Considerations

- Add pre-commit hooks to validate changes
- Consider commit message templates based on change types
- Add notification system for failed automation
- Consider using conventional commits format

