#!/usr/bin/env python3
"""
Version Manager and Automated Commit System
Manages versioning and automatically commits changes to GitHub
"""

import os
import sys
import subprocess
import json
import datetime
from pathlib import Path
from typing import Optional, Tuple


class VersionManager:
    """
    Manages semantic versioning for the project
    
    ADR Note: Using semantic versioning (MAJOR.MINOR.PATCH) as it's the industry
    standard and provides clear meaning for version bumps. The version is stored
    in a simple text file (VERSION) rather than in code to allow easy editing
    and to avoid requiring code changes for version updates.
    """
    
    def __init__(self, version_file: str = "VERSION"):
        self.version_file = Path(version_file)
        self.version = self._read_version()
    
    def _read_version(self) -> str:
        """
        Read current version from file
        
        ADR Note: Defaults to "0.1.0" if VERSION file doesn't exist. This allows
        the system to work even if the version file is missing, providing a safe
        fallback rather than failing completely.
        """
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return "0.1.0"
    
    def _write_version(self, version: str):
        """Write version to file"""
        self.version_file.write_text(f"{version}\n")
        self.version = version
    
    def bump_patch(self) -> str:
        """Bump patch version (0.1.0 -> 0.1.1)"""
        major, minor, patch = map(int, self.version.split('.'))
        new_version = f"{major}.{minor}.{patch + 1}"
        self._write_version(new_version)
        return new_version
    
    def bump_minor(self) -> str:
        """Bump minor version (0.1.0 -> 0.2.0)"""
        major, minor, patch = map(int, self.version.split('.'))
        new_version = f"{major}.{minor + 1}.0"
        self._write_version(new_version)
        return new_version
    
    def bump_major(self) -> str:
        """Bump major version (0.1.0 -> 1.0.0)"""
        major, minor, patch = map(int, self.version.split('.'))
        new_version = f"{major + 1}.0.0"
        self._write_version(new_version)
        return new_version
    
    def get_version(self) -> str:
        """Get current version"""
        return self.version


class GitAutomation:
    """
    Handles git operations for automated commits
    
    ADR Note: Using subprocess to call git commands rather than a git library
    (like GitPython) to minimize dependencies and ensure compatibility with
    any git installation. The subprocess approach also provides better error
    handling and visibility into git operations.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """
        Load configuration from config file
        
        ADR Note: Configuration is stored in JSON for human readability and easy
        editing. Defaults are provided inline to ensure the system works even
        without a config file. This follows the "sensible defaults" principle.
        """
        config_file = self.repo_path / "automation_config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {
            "auto_commit": True,
            "auto_push": True,
            "commit_message_template": "Auto-commit: {timestamp}",
            "min_changes_for_commit": 1,
            "excluded_paths": [".git", "__pycache__", ".venv", "venv", "node_modules"]
        }
    
    def has_changes(self) -> bool:
        """Check if there are uncommitted changes"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def get_changed_files(self) -> list:
        """Get list of changed files"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    status, filepath = line.split(maxsplit=1)
                    if not any(excluded in filepath for excluded in self.config.get("excluded_paths", [])):
                        files.append(filepath)
            return files
        except subprocess.CalledProcessError:
            return []
    
    def commit_changes(self, message: Optional[str] = None) -> bool:
        """
        Commit all changes
        
        ADR Note: Uses "git add -A" to stage all changes including deletions.
        This ensures the automated system captures all modifications. The commit
        message uses a template with timestamp by default, but can be overridden
        for version bumps or manual commits. Errors are caught and logged rather
        than crashing, allowing the automation to continue even if one commit fails.
        """
        if not self.has_changes():
            return False
        
        if message is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            template = self.config.get("commit_message_template", "Auto-commit: {timestamp}")
            message = template.format(timestamp=timestamp)
        
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error committing changes: {e}", file=sys.stderr)
            return False
    
    def push_changes(self) -> bool:
        """
        Push changes to remote
        
        ADR Note: Hardcoded to push to "origin master" branch. This assumes the
        default branch name. In the future, this could be made configurable or
        auto-detected using "git symbolic-ref refs/remotes/origin/HEAD" to support
        repositories using "main" or other branch names.
        """
        try:
            subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing changes: {e}", file=sys.stderr)
            return False
    
    def create_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Create a git tag for the version"""
        tag_name = f"v{version}"
        if message is None:
            message = f"Version {version}"
        
        try:
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_tags(self) -> bool:
        """Push tags to remote"""
        try:
            subprocess.run(
                ["git", "push", "origin", "--tags"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing tags: {e}", file=sys.stderr)
            return False


def main():
    """Main automation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Version manager and automated commit system")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], help="Bump version")
    parser.add_argument("--commit", action="store_true", help="Commit changes")
    parser.add_argument("--push", action="store_true", help="Push changes")
    parser.add_argument("--tag", action="store_true", help="Create and push version tag")
    parser.add_argument("--auto", action="store_true", help="Run full automation (commit + push)")
    parser.add_argument("--message", help="Custom commit message")
    
    args = parser.parse_args()
    
    version_manager = VersionManager()
    git_automation = GitAutomation()
    
    # Handle version bumping
    if args.bump:
        old_version = version_manager.get_version()
        if args.bump == "patch":
            new_version = version_manager.bump_patch()
        elif args.bump == "minor":
            new_version = version_manager.bump_minor()
        else:
            new_version = version_manager.bump_major()
        
        print(f"Version bumped: {old_version} -> {new_version}")
        
        # Auto-commit version change
        if git_automation.config.get("auto_commit", True):
            git_automation.commit_changes(f"Bump version to {new_version}")
    
    # Handle auto mode
    # ADR Note: The --auto flag provides a single command that handles the full
    # automation workflow: check for changes, commit if threshold met, push if
    # configured. This is designed for scheduled execution (cron, Task Scheduler,
    # GitHub Actions) where a single command should handle everything.
    if args.auto:
        if git_automation.has_changes():
            changed_files = git_automation.get_changed_files()
            if len(changed_files) >= git_automation.config.get("min_changes_for_commit", 1):
                if git_automation.commit_changes(args.message):
                    print(f"Committed {len(changed_files)} changed file(s)")
                    if git_automation.config.get("auto_push", True):
                        if git_automation.push_changes():
                            print("Pushed changes to remote")
                        else:
                            print("Failed to push changes")
                else:
                    print("Failed to commit changes")
            else:
                print(f"Not enough changes (minimum: {git_automation.config.get('min_changes_for_commit', 1)})")
        else:
            print("No changes to commit")
        return
    
    # Handle individual operations
    if args.commit:
        if git_automation.commit_changes(args.message):
            print("Changes committed successfully")
        else:
            print("No changes to commit or commit failed")
    
    if args.push:
        if git_automation.push_changes():
            print("Changes pushed successfully")
        else:
            print("Failed to push changes")
    
    if args.tag:
        version = version_manager.get_version()
        if git_automation.create_tag(version):
            print(f"Tag v{version} created")
            if git_automation.push_tags():
                print("Tag pushed to remote")
        else:
            print("Failed to create tag")


if __name__ == "__main__":
    main()

