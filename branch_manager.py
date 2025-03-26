#!/usr/bin/env python3
"""
Branch Manager for Secure Video Summarizer

A cross-platform Python script to manage Git branches for parallel development.
Provides functionalities for setting up the branching structure, creating feature branches,
and performing common branch operations.
"""

import subprocess
import sys
import os
import argparse

def run_command(command, error_message=None, exit_on_error=False):
    """Run a shell command and handle errors"""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if error_message:
            print(f"Error: {error_message}")
        print(f"Command failed: {' '.join(command)}")
        print(f"Error output: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return False, e.stderr

def setup_branching_structure():
    """Set up the initial branching structure"""
    print("Setting up branching structure for Secure Video Summarizer...")
    
    # Make sure git is available
    run_command(["git", "--version"], "Git is not installed.", exit_on_error=True)
    
    # Make sure we're on master and up to date
    print("\nChecking out master branch...")
    run_command(["git", "checkout", "master"])
    run_command(["git", "pull"])
    
    # Create develop branch
    print("\nCreating develop branch...")
    run_command(["git", "checkout", "-b", "develop"])
    run_command(["git", "push", "-u", "origin", "develop"])
    
    # Create track branches
    tracks = ["python-scripts", "frontend-extension", "error-system"]
    for track in tracks:
        print(f"\nCreating {track} track branch...")
        run_command(["git", "checkout", "develop"])
        run_command(["git", "checkout", "-b", f"track/{track}"])
        run_command(["git", "push", "-u", "origin", f"track/{track}"])
    
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
    run_command(["git", "checkout", "develop"])
    run_command(["git", "push", "origin", "develop"])
    
    print("\nBranching structure setup complete!")

def create_feature_branch(track, feature, base_branch=None):
    """Create a feature branch for a specific track"""
    if not base_branch:
        base_branch = f"track/{track}"
    
    branch_name = f"feature/{track}/{feature}"
    
    # Checkout the base branch
    success, _ = run_command(["git", "checkout", base_branch])
    if not success:
        print(f"Could not checkout {base_branch}. Make sure it exists.")
        return False
    
    # Create the feature branch
    success, _ = run_command(["git", "checkout", "-b", branch_name])
    if not success:
        print(f"Could not create branch {branch_name}.")
        return False
    
    # Push to origin
    success, _ = run_command(["git", "push", "-u", "origin", branch_name])
    if not success:
        print(f"Could not push branch {branch_name} to origin.")
        return False
    
    print(f"Successfully created feature branch: {branch_name}")
    return True

def create_all_feature_branches():
    """Create all feature branches for each track"""
    print("Creating feature branches for Secure Video Summarizer...\n")
    
    # Define all features by track
    features = {
        "python-scripts": [
            "core-utilities",
            "startup-script",
            "backend-runner"
        ],
        "frontend-extension": [
            "architecture-refactor",
            "ui-enhancements",
            "dashboard-selfservice"
        ],
        "error-system": [
            "error-framework",
            "logging-enhancements",
            "documentation"
        ]
    }
    
    # Create branches for each track and feature
    for track, track_features in features.items():
        print(f"\nCreating feature branches for {track} track...")
        for feature in track_features:
            create_feature_branch(track, feature)
    
    # Return to develop branch
    run_command(["git", "checkout", "develop"])
    
    print("\nFeature branches created successfully!")

def list_branches():
    """List all branches and their tracking information"""
    print("Listing all branches for Secure Video Summarizer...\n")
    
    # List local branches
    print("Local branches:")
    run_command(["git", "branch"])
    
    # List remote branches
    print("\nRemote branches:")
    run_command(["git", "branch", "-r"])
    
    # Show tracking branches
    print("\nLocal branches with tracking information:")
    run_command(["git", "branch", "-vv"])

def create_bugfix_branch(track, bug_description):
    """Create a bugfix branch for a specific track"""
    branch_name = f"bugfix/{track}/{bug_description}"
    
    # Checkout the track branch
    success, _ = run_command(["git", "checkout", f"track/{track}"])
    if not success:
        print(f"Could not checkout track/{track}. Make sure it exists.")
        return False
    
    # Create the bugfix branch
    success, _ = run_command(["git", "checkout", "-b", branch_name])
    if not success:
        print(f"Could not create branch {branch_name}.")
        return False
    
    # Push to origin
    success, _ = run_command(["git", "push", "-u", "origin", branch_name])
    if not success:
        print(f"Could not push branch {branch_name} to origin.")
        return False
    
    print(f"Successfully created bugfix branch: {branch_name}")
    return True

def main():
    """Main function to parse arguments and call appropriate functions"""
    parser = argparse.ArgumentParser(description='Branch Manager for Secure Video Summarizer')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Setup branching structure command
    setup_parser = subparsers.add_parser('setup', help='Set up the initial branching structure')
    
    # Create feature branch command
    feature_parser = subparsers.add_parser('feature', help='Create a feature branch')
    feature_parser.add_argument('track', choices=['python-scripts', 'frontend-extension', 'error-system'], 
                                help='The track to create the feature branch for')
    feature_parser.add_argument('name', help='Name of the feature')
    
    # Create all feature branches command
    all_features_parser = subparsers.add_parser('all-features', help='Create all predefined feature branches')
    
    # List branches command
    list_parser = subparsers.add_parser('list', help='List all branches')
    
    # Create bugfix branch command
    bugfix_parser = subparsers.add_parser('bugfix', help='Create a bugfix branch')
    bugfix_parser.add_argument('track', choices=['python-scripts', 'frontend-extension', 'error-system'], 
                               help='The track to create the bugfix branch for')
    bugfix_parser.add_argument('description', help='Description of the bug')
    
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'setup':
        setup_branching_structure()
    elif args.command == 'feature':
        create_feature_branch(args.track, args.name)
    elif args.command == 'all-features':
        create_all_feature_branches()
    elif args.command == 'list':
        list_branches()
    elif args.command == 'bugfix':
        create_bugfix_branch(args.track, args.description)
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main() 