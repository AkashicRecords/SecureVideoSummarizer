#!/usr/bin/env python3
import subprocess
import os
import sys

def run_command(command, error_message=None):
    """Run a shell command and handle errors"""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if error_message:
            print(f"Error: {error_message}")
        print(f"Command failed: {' '.join(command)}")
        print(f"Error output: {e.stderr}")
        # Continue even if command fails (e.g., branch already exists)
        return False

def setup_branching_structure():
    """Set up the branching structure for the Secure Video Summarizer project"""
    print("Setting up branching structure for Secure Video Summarizer...")
    
    # Make sure git is available
    if not run_command(["git", "--version"], "Git is not installed."):
        sys.exit(1)
    
    # Make sure we're on master and up to date
    print("\nChecking out master branch...")
    run_command(["git", "checkout", "master"])
    run_command(["git", "pull"])
    
    # Create develop branch
    print("\nCreating develop branch...")
    run_command(["git", "checkout", "-b", "develop"])
    run_command(["git", "push", "-u", "origin", "develop"])
    
    # Create track branches
    print("\nCreating Python Scripts track branch...")
    run_command(["git", "checkout", "develop"])
    run_command(["git", "checkout", "-b", "track/python-scripts"])
    run_command(["git", "push", "-u", "origin", "track/python-scripts"])
    
    print("\nCreating Frontend/Extension track branch...")
    run_command(["git", "checkout", "develop"])
    run_command(["git", "checkout", "-b", "track/frontend-extension"])
    run_command(["git", "push", "-u", "origin", "track/frontend-extension"])
    
    print("\nCreating Error System track branch...")
    run_command(["git", "checkout", "develop"])
    run_command(["git", "checkout", "-b", "track/error-system"])
    run_command(["git", "push", "-u", "origin", "track/error-system"])
    
    # Create CONTRIBUTING.md file
    print("\nCreating CONTRIBUTING.md file...")
    contributing_content = """# Contributing to Secure Video Summarizer

This document outlines our branching strategy for parallel development.

## Branches

- `master` - Production code
- `develop` - Integration branch
- Track branches:
  - `track/python-scripts` - Python script enhancements
  - `track/frontend-extension` - Frontend/extension improvements
  - `track/error-system` - Error handling and documentation

## Workflow

1. Create feature branches from track branches
2. Use naming convention: `feature/[track-name]/[feature-name]`
3. Submit PRs to track branches first
4. Track branches get merged to develop weekly
5. Develop merges to master for releases
"""
    
    with open("CONTRIBUTING.md", "w") as f:
        f.write(contributing_content)
    
    # Add and commit CONTRIBUTING.md
    print("\nAdding and committing CONTRIBUTING.md...")
    run_command(["git", "add", "CONTRIBUTING.md"])
    run_command(["git", "commit", "-m", "Add contributing guidelines with branching strategy"])
    run_command(["git", "push", "origin", "develop"])
    
    print("\nBranching structure setup complete!")
    print("Next steps:")
    print("1. Set up branch protection rules in GitHub repository settings")
    print("2. Start creating feature branches from track branches")

if __name__ == "__main__":
    setup_branching_structure() 