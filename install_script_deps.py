#!/usr/bin/env python3
"""
Dependency installer for cross-platform scripts.
This sets up a virtual environment specifically for our scripts and installs required packages.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, shell=False):
    """Run a command and return the result and success status"""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=shell)
        return True, result.stdout
    except subprocess.SubprocessError as e:
        return False, e.stderr

def main():
    print("\n=== Script Dependencies Installer ===\n")
    
    # Define the virtual environment path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, "scripts_venv")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment at: {venv_dir}")
        success, output = run_command([sys.executable, "-m", "venv", venv_dir])
        if not success:
            print(f"Failed to create virtual environment: {output}")
            sys.exit(1)
        print("Virtual environment created successfully.")
    else:
        print(f"Using existing virtual environment at: {venv_dir}")
    
    # Determine activation script and pip path based on platform
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_dir, "Scripts", "activate.bat")
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
    else:
        activate_script = os.path.join(venv_dir, "bin", "activate")
        pip_path = os.path.join(venv_dir, "bin", "pip")
    
    # Install packages using the virtual environment's pip
    print("\nInstalling required packages...")
    
    # Upgrade pip first
    print("Upgrading pip...")
    if platform.system() == "Windows":
        cmd = f'"{os.path.join(venv_dir, "Scripts", "python")}" -m pip install --upgrade pip'
        success, output = run_command(cmd, shell=True)
    else:
        cmd = f'source "{activate_script}" && pip install --upgrade pip'
        success, output = run_command(cmd, shell=True)
    
    if not success:
        print(f"Warning: Failed to upgrade pip: {output}")
    
    # Install dependencies
    print("Installing psutil...")
    if platform.system() == "Windows":
        cmd = f'"{os.path.join(venv_dir, "Scripts", "python")}" -m pip install psutil'
        success, output = run_command(cmd, shell=True)
    else:
        cmd = f'source "{activate_script}" && pip install psutil'
        success, output = run_command(cmd, shell=True)
    
    if not success:
        print(f"Failed to install psutil: {output}")
        sys.exit(1)
    
    print("\nDependencies installed successfully!")
    print("\nTo use these scripts with the dependencies, run:")
    if platform.system() == "Windows":
        print(f'  {os.path.join(venv_dir, "Scripts", "python")} start_svs_application.py')
    else:
        print(f'  source "{activate_script}" && ./start_svs_application.py')
    
    # Create a runner script for convenience
    create_runner_script(venv_dir)
    
    print("\nOr use the convenience script:")
    if platform.system() == "Windows":
        print("  run_app.bat")
    else:
        print("  ./run_app.sh")

def create_runner_script(venv_dir):
    """Create a convenience script to run the application with the virtual environment"""
    if platform.system() == "Windows":
        # Create Windows batch file
        with open("run_app.bat", "w") as f:
            f.write(f'@echo off\n')
            f.write(f'"{os.path.join(venv_dir, "Scripts", "python")}" start_svs_application.py %*\n')
        print("Created run_app.bat")
    else:
        # Create Unix shell script
        with open("run_app.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f'source "{os.path.join(venv_dir, "bin", "activate")}"\n')
            f.write('./start_svs_application.py "$@"\n')
        
        # Make it executable
        os.chmod("run_app.sh", 0o755)
        print("Created run_app.sh")

if __name__ == "__main__":
    main() 