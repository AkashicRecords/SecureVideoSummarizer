#!/bin/bash

# Script to create initial feature branches for the Secure Video Summarizer project
echo "Creating feature branches for Secure Video Summarizer..."

# Python Scripts track - feature branches
echo "Creating feature branches for Python Scripts track..."
git checkout track/python-scripts
git checkout -b feature/python-scripts/core-utilities
git push -u origin feature/python-scripts/core-utilities

git checkout track/python-scripts
git checkout -b feature/python-scripts/startup-script
git push -u origin feature/python-scripts/startup-script

git checkout track/python-scripts
git checkout -b feature/python-scripts/backend-runner
git push -u origin feature/python-scripts/backend-runner

# Frontend/Extension track - feature branches
echo "Creating feature branches for Frontend/Extension track..."
git checkout track/frontend-extension
git checkout -b feature/frontend-extension/architecture-refactor
git push -u origin feature/frontend-extension/architecture-refactor

git checkout track/frontend-extension
git checkout -b feature/frontend-extension/ui-enhancements
git push -u origin feature/frontend-extension/ui-enhancements

git checkout track/frontend-extension
git checkout -b feature/frontend-extension/dashboard-selfservice
git push -u origin feature/frontend-extension/dashboard-selfservice

# Error System track - feature branches
echo "Creating feature branches for Error System track..."
git checkout track/error-system
git checkout -b feature/error-system/error-framework
git push -u origin feature/error-system/error-framework

git checkout track/error-system
git checkout -b feature/error-system/logging-enhancements
git push -u origin feature/error-system/logging-enhancements

git checkout track/error-system
git checkout -b feature/error-system/documentation
git push -u origin feature/error-system/documentation

# Return to develop branch
git checkout develop

echo "Feature branches created successfully!"
echo "Next steps:"
echo "1. Assign developers to specific feature branches"
echo "2. Begin implementation of high-priority components" 