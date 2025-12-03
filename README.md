# Reverse Engineering Orchestrator

Automated versioning and commit system for managing project changes and GitHub synchronization.

## Features

- **Semantic Versioning**: Automatic version management (MAJOR.MINOR.PATCH)
- **Automated Commits**: Periodically commit and push changes to GitHub
- **GitHub Actions**: CI/CD workflow for automated versioning
- **Windows Task Scheduler**: Local automation support for Windows

## Quick Start

### Manual Operations

```bash
# Run automated commit and push
python version_manager.py --auto

# Bump version (patch, minor, or major)
python version_manager.py --bump patch

# Commit changes manually
python version_manager.py --commit --message "Your commit message"

# Push changes
python version_manager.py --push

# Create and push version tag
python version_manager.py --tag
```

### Automated Scheduling

#### Windows Task Scheduler

1. Run the setup script (as Administrator for best results):
   ```powershell
   .\setup_scheduler.ps1
   ```

2. Or manually run the automation script:
   ```powershell
   .\automate.ps1
   ```

#### GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/auto-commit.yml`) that:
- Runs every hour automatically
- Commits and pushes changes
- Creates version tags when the version file changes

## Configuration

Edit `automation_config.json` to customize:
- Auto-commit and auto-push settings
- Commit message templates
- Minimum changes required for commit
- Excluded file paths

## Version Management

The current version is stored in `VERSION` file. Use the version manager to bump versions:

- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

## Files

- `version_manager.py` - Main automation script
- `VERSION` - Current version number
- `automation_config.json` - Configuration settings
- `automate.ps1` / `automate.bat` - Windows automation scripts
- `setup_scheduler.ps1` - Task Scheduler setup script
- `.github/workflows/auto-commit.yml` - GitHub Actions workflow

## Requirements

- Python 3.7+
- Git
- GitHub CLI (optional, for manual operations)
