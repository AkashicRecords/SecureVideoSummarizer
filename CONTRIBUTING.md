# Contributing to Secure Video Summarizer

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
