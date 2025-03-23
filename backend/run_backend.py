#!/usr/bin/env python3
"""
Cross-platform backend startup script for the Secure Video Summarizer application.
This script provides OS-agnostic functionality equivalent to run_backend.sh.
"""

import os
import sys
import subprocess
import platform
import argparse
import time
import signal

# ANSI colors for Unix terminals
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# For Windows, we'll use empty strings
if platform.system() == 'Windows':
    for attr in dir(Colors):
        if not attr.startswith('__'):
            setattr(Colors, attr, '')

# Default settings
class Config:
    PORT = 8081
    DEBUG = True
    CONFIG_MODE = "development"
    FORCE_INSTALL = False
    UPDATE_PACKAGES = False
    OFFLINE_MODE = False
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(color, message):
    """Print colored log messages"""
    print(f"{color}{message}{Colors.NC}")

def create_virtualenv():
    """Create a Python virtual environment if it doesn't exist"""
    venv_dir = os.path.join(Config.SCRIPT_DIR, "venv")
    
    if not os.path.exists(venv_dir):
        log(Colors.YELLOW, "Creating virtual environment...")
        python_cmd = "python" if platform.system() == "Windows" else "python3"
        
        try:
            subprocess.run([python_cmd, "-m", "venv", venv_dir], check=True)
            log(Colors.GREEN, "Virtual environment created successfully!")
            return True
        except subprocess.SubprocessError as e:
            log(Colors.RED, f"Failed to create virtual environment: {e}")
            return False
    else:
        return True

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    venv_dir = os.path.join(Config.SCRIPT_DIR, "venv")
    
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")

def install_pip_packages():
    """Install required pip packages directly"""
    log(Colors.YELLOW, "Installing required packages directly with pip...")
    
    venv_python = get_venv_python()
    requirements_file = os.path.join(Config.SCRIPT_DIR, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        log(Colors.RED, f"Error: requirements.txt not found at {requirements_file}")
        return False
    
    try:
        # Install packages
        if Config.OFFLINE_MODE:
            vendor_dir = os.path.join(Config.SCRIPT_DIR, "vendor")
            if not os.path.exists(vendor_dir):
                log(Colors.RED, f"Error: Vendor directory not found at {vendor_dir}")
                return False
                
            cmd = [venv_python, "-m", "pip", "install", "--no-index", f"--find-links={vendor_dir}", "-r", requirements_file]
        else:
            cmd = [venv_python, "-m", "pip", "install", "-r", requirements_file]
        
        subprocess.run(cmd, check=True)
        
        # Create installed flag
        with open(os.path.join(Config.SCRIPT_DIR, "venv", "installed.flag"), "w") as f:
            f.write("Dependencies installed on " + time.strftime("%Y-%m-%d %H:%M:%S"))
        
        log(Colors.GREEN, "Dependencies installed successfully!")
        return True
    except subprocess.SubprocessError as e:
        log(Colors.RED, f"Failed to install dependencies: {e}")
        return False

def check_for_updates():
    """Check for package updates"""
    if Config.UPDATE_PACKAGES:
        log(Colors.YELLOW, "Checking for package updates...")
        
        update_script = os.path.join(Config.SCRIPT_DIR, "scripts", 
                                     "check_updates.py" if os.path.exists(os.path.join(Config.SCRIPT_DIR, "scripts", "check_updates.py")) 
                                     else "check_updates.sh")
        
        if platform.system() == "Windows" and update_script.endswith(".sh"):
            log(Colors.RED, "Error: Windows does not support shell scripts. Please use the Python version.")
            return False
        
        try:
            # Make the script executable on Unix systems
            if platform.system() != "Windows" and update_script.endswith(".sh"):
                subprocess.run(["chmod", "+x", update_script], check=True)
                subprocess.run([update_script], check=True, cwd=Config.SCRIPT_DIR)
            elif update_script.endswith(".py"):
                python_cmd = "python" if platform.system() == "Windows" else "python3"
                subprocess.run([python_cmd, update_script], check=True, cwd=Config.SCRIPT_DIR)
            
            log(Colors.GREEN, "Update check completed successfully!")
            return True
        except subprocess.SubprocessError as e:
            log(Colors.RED, f"Failed to check for updates: {e}")
            return False
    
    return True

def install_dependencies():
    """Install requirements if needed or forced"""
    venv_dir = os.path.join(Config.SCRIPT_DIR, "venv")
    installed_flag = os.path.join(venv_dir, "installed.flag")
    
    if not os.path.exists(installed_flag) or Config.FORCE_INSTALL:
        log(Colors.YELLOW, "Installing requirements...")
        
        # First try using the script if it exists
        install_script = os.path.join(Config.SCRIPT_DIR, "scripts", 
                                     "install_dependencies.py" if os.path.exists(os.path.join(Config.SCRIPT_DIR, "scripts", "install_dependencies.py")) 
                                     else "install_dependencies.sh")
        
        if platform.system() == "Windows" and install_script.endswith(".sh"):
            log(Colors.YELLOW, "Windows doesn't support shell scripts. Using direct pip installation instead.")
            return install_pip_packages()
        
        try:
            # Make the script executable on Unix systems
            if platform.system() != "Windows" and install_script.endswith(".sh"):
                subprocess.run(["chmod", "+x", install_script], check=True)
                
                if Config.OFFLINE_MODE:
                    result = subprocess.run([install_script, "--offline"], cwd=Config.SCRIPT_DIR)
                else:
                    result = subprocess.run([install_script], cwd=Config.SCRIPT_DIR)
                
                if result.returncode != 0:
                    log(Colors.YELLOW, "Installation script failed. Trying direct pip installation...")
                    return install_pip_packages()
            elif install_script.endswith(".py"):
                python_cmd = "python" if platform.system() == "Windows" else "python3"
                
                if Config.OFFLINE_MODE:
                    result = subprocess.run([python_cmd, install_script, "--offline"], cwd=Config.SCRIPT_DIR)
                else:
                    result = subprocess.run([python_cmd, install_script], cwd=Config.SCRIPT_DIR)
                
                if result.returncode != 0:
                    log(Colors.YELLOW, "Installation script failed. Trying direct pip installation...")
                    return install_pip_packages()
            else:
                # If script doesn't exist, use direct pip installation
                return install_pip_packages()
            
            log(Colors.GREEN, "Dependencies installed successfully!")
            return True
        except Exception as e:
            log(Colors.RED, f"Failed to install dependencies via script: {e}")
            log(Colors.YELLOW, "Trying direct pip installation...")
            return install_pip_packages()
    else:
        log(Colors.GREEN, "Dependencies already installed!")
        # Verify that Flask is actually installed
        venv_python = get_venv_python()
        try:
            result = subprocess.run([venv_python, "-c", "import flask_sqlalchemy"], stderr=subprocess.PIPE)
            if result.returncode != 0:
                log(Colors.YELLOW, "Flask-SQLAlchemy not found despite the installed flag. Reinstalling dependencies...")
                return install_pip_packages()
        except Exception:
            log(Colors.YELLOW, "Error checking installed packages. Reinstalling dependencies...")
            return install_pip_packages()
    
    return True

def start_app():
    """Start the Flask application"""
    log(Colors.BLUE, f"Starting backend server on port {Config.PORT}...")
    
    # Get the path to the Python executable in the virtual environment
    venv_python = get_venv_python()
    
    # Prepare the command to run the Flask application
    if Config.DEBUG:
        cmd = [venv_python, "-m", "app.main", "--port", str(Config.PORT), "--debug", "--config", Config.CONFIG_MODE]
    else:
        cmd = [venv_python, "-m", "app.main", "--port", str(Config.PORT), "--config", Config.CONFIG_MODE]
    
    # Start the process and return it
    try:
        # Use Popen to get a process that we can wait on
        process = subprocess.Popen(cmd, cwd=Config.SCRIPT_DIR)
        
        # Give the server a moment to start or fail
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            log(Colors.GREEN, f"Backend server started successfully on port {Config.PORT}!")
            return process
        else:
            log(Colors.RED, f"Backend server failed to start with exit code {process.returncode}")
            return None
    except Exception as e:
        log(Colors.RED, f"Error starting application: {e}")
        return None

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Secure Video Summarizer backend server")
    parser.add_argument("--install-deps", action="store_true", help="Force reinstallation of dependencies")
    parser.add_argument("--update", action="store_true", help="Check for package updates")
    parser.add_argument("--port", type=int, default=Config.PORT, help="Port for the backend server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    parser.add_argument("--config", default=Config.CONFIG_MODE, 
                        choices=["development", "production", "testing"], 
                        help="Configuration mode")
    parser.add_argument("--offline", action="store_true", help="Enable offline mode")
    
    args = parser.parse_args()
    
    # Update configuration from command line arguments
    Config.PORT = args.port
    Config.CONFIG_MODE = args.config
    Config.FORCE_INSTALL = args.install_deps
    Config.UPDATE_PACKAGES = args.update
    Config.OFFLINE_MODE = args.offline
    
    # Handle debug flag precedence
    if args.debug:
        Config.DEBUG = True
    elif args.no_debug:
        Config.DEBUG = False
    
    # Create virtual environment if needed
    if not create_virtualenv():
        sys.exit(1)
    
    # Check for updates if requested
    if Config.UPDATE_PACKAGES and not check_for_updates():
        log(Colors.YELLOW, "Continuing despite update check failure...")
    
    # Install dependencies if needed
    if not install_dependencies():
        sys.exit(1)
    
    # Start the application
    process = start_app()
    
    if process:
        # Keep the script running and handle Ctrl+C
        try:
            process.wait()
        except KeyboardInterrupt:
            log(Colors.YELLOW, "Shutting down backend server...")
            # Terminate the process
            process.terminate()
            try:
                # Wait for up to 5 seconds for the process to terminate
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it doesn't terminate within 5 seconds, kill it
                log(Colors.RED, "Server not responding to termination. Forcefully killing...")
                process.kill()
    else:
        log(Colors.RED, "Failed to start backend server!")
        sys.exit(1)

if __name__ == "__main__":
    main() 