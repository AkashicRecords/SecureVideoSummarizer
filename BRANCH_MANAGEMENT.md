# Branch Management Tools

This directory contains cross-platform Python scripts for managing Git branches in the Secure Video Summarizer project.

## Overview

These tools help maintain the branching strategy for parallel development across multiple tracks:

- `python-scripts` - Python script enhancements
- `frontend-extension` - Frontend/extension improvements
- `error-system` - Error handling and documentation

## Tools

### branch_manager.py

The primary tool for branch management with multiple commands:

```bash
# View help
./branch_manager.py --help

# Set up initial branching structure
./branch_manager.py setup

# Create a feature branch
./branch_manager.py feature <track> <feature-name>
# Example:
./branch_manager.py feature python-scripts new-utility

# Create all predefined feature branches
./branch_manager.py all-features

# List all branches
./branch_manager.py list

# Create a bugfix branch
./branch_manager.py bugfix <track> <bug-description>
# Example:
./branch_manager.py bugfix frontend-extension fix-layout-issue
```

### Single-Purpose Scripts

These scripts perform specific tasks:

- `setup_branches.py` - Sets up the initial branching structure
- `create_feature_branches.py` - Creates all predefined feature branches

## Branching Strategy

Our branching strategy follows this structure:

- `master` - Production code
- `develop` - Integration branch
- Track branches:
  - `track/python-scripts`
  - `track/frontend-extension`
  - `track/error-system`
- Feature branches:
  - `feature/python-scripts/core-utilities`
  - `feature/python-scripts/startup-script`
  - `feature/python-scripts/backend-runner`
  - `feature/frontend-extension/architecture-refactor`
  - `feature/frontend-extension/ui-enhancements`
  - `feature/frontend-extension/dashboard-selfservice`
  - `feature/error-system/error-framework`
  - `feature/error-system/logging-enhancements`
  - `feature/error-system/documentation`

## Workflow

1. Developers work on feature branches
2. Feature branches get merged to track branches
3. Track branches get merged to develop weekly
4. Develop gets merged to master for releases

## Installation

These scripts require Python 3.6+ and Git.

Make sure the scripts are executable:

```bash
chmod +x branch_manager.py setup_branches.py create_feature_branches.py
``` 