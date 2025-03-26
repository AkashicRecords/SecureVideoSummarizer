#!/usr/bin/env python3
import subprocess
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
        # Continue even if command fails
        return False

def create_feature_branch(track, feature):
    """Create a feature branch for a specific track"""
    branch_name = f"feature/{track}/{feature}"
    
    # Checkout the track branch
    run_command(["git", "checkout", f"track/{track}"])
    
    # Create the feature branch
    run_command(["git", "checkout", "-b", branch_name])
    
    # Push to origin
    run_command(["git", "push", "-u", "origin", branch_name])

def create_feature_branches():
    """Create all feature branches for the Secure Video Summarizer project"""
    print("Creating feature branches for Secure Video Summarizer...\n")
    
    # Make sure git is available
    if not run_command(["git", "--version"], "Git is not installed."):
        sys.exit(1)
    
    # Python Scripts track - feature branches
    print("\nCreating feature branches for Python Scripts track...")
    python_features = [
        "core-utilities",
        "startup-script",
        "backend-runner"
    ]
    
    for feature in python_features:
        create_feature_branch("python-scripts", feature)
    
    # Frontend/Extension track - feature branches
    print("\nCreating feature branches for Frontend/Extension track...")
    frontend_features = [
        "architecture-refactor",
        "ui-enhancements",
        "dashboard-selfservice"
    ]
    
    for feature in frontend_features:
        create_feature_branch("frontend-extension", feature)
    
    # Error System track - feature branches
    print("\nCreating feature branches for Error System track...")
    error_features = [
        "error-framework",
        "logging-enhancements",
        "documentation"
    ]
    
    for feature in error_features:
        create_feature_branch("error-system", feature)
    
    # Return to develop branch
    run_command(["git", "checkout", "develop"])
    
    print("\nFeature branches created successfully!")
    print("Next steps:")
    print("1. Assign developers to specific feature branches")
    print("2. Begin implementation of high-priority components")

if __name__ == "__main__":
    create_feature_branches() 