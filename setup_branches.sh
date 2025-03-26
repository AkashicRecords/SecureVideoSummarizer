#!/bin/bash

# Script to set up branching strategy for Secure Video Summarizer
echo "Setting up branching strategy for Secure Video Summarizer..."

# Make sure we're on master and up to date
echo "Checking out master branch..."
git checkout master && git pull

# Create develop branch
echo "Creating develop branch..."
git checkout -b develop
git push -u origin develop

# Create Python Scripts track branch
echo "Creating Python Scripts track branch..."
git checkout develop
git checkout -b track/python-scripts
git push -u origin track/python-scripts

# Create Frontend/Extension track branch
echo "Creating Frontend/Extension track branch..."
git checkout develop
git checkout -b track/frontend-extension
git push -u origin track/frontend-extension

# Create Error System track branch
echo "Creating Error System track branch..."
git checkout develop
git checkout -b track/error-system
git push -u origin track/error-system

# Create CONTRIBUTING.md file
echo "Creating CONTRIBUTING.md file..."
cat > CONTRIBUTING.md << 'EOF'
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
EOF

# Add and commit CONTRIBUTING.md
echo "Adding and committing CONTRIBUTING.md..."
git add CONTRIBUTING.md
git commit -m "Add contributing guidelines with branching strategy"
git push origin develop

echo "Branching strategy setup complete!"
echo "Next steps:"
echo "1. Set up branch protection rules in GitHub repository settings"
echo "2. Start creating feature branches from track branches" 