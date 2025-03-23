#!/usr/bin/env python3
"""
Cross-platform dashboard startup script for the Secure Video Summarizer application.
This script provides OS-agnostic functionality equivalent to run_dashboard.sh.
"""

import os
import sys
import subprocess
import platform
import argparse
import time
import signal
import logging
import datetime

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"dashboard_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SVS_Dashboard")

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
    PORT = 8080
    DEBUG = True
    FORCE_INSTALL = False
    UPDATE_PACKAGES = False
    OFFLINE_MODE = False
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DASHBOARD_VENV = os.path.join(SCRIPT_DIR, "dashboard_venv")

def log(color, message):
    """Print colored log messages"""
    print(f"{color}{message}{Colors.NC}")
    logger.info(message)

def verify_directory():
    """Verify the script is being run from the correct directory"""
    logger.info("Verifying directory structure")
    
    if not os.path.isdir(Config.SCRIPT_DIR):
        error_msg = f"Script directory not found at {Config.SCRIPT_DIR}"
        logger.error(error_msg)
        log(Colors.RED, f"Error: {error_msg}")
        return False
    
    # Check for app/dashboard directory
    dashboard_dir = os.path.join(Config.SCRIPT_DIR, "app", "dashboard")
    if not os.path.isdir(dashboard_dir):
        error_msg = f"Dashboard directory not found at {dashboard_dir}"
        logger.error(error_msg)
        log(Colors.RED, f"Error: {error_msg}")
        return False
    
    logger.info("Directory structure verified successfully")
    return True

def create_virtualenv():
    """Create a Python virtual environment if it doesn't exist"""
    logger.info("Checking dashboard virtual environment")
    
    if not os.path.exists(Config.DASHBOARD_VENV):
        log(Colors.YELLOW, "Creating dashboard virtual environment...")
        logger.info("Creating dashboard virtual environment")
        python_cmd = "python" if platform.system() == "Windows" else "python3"
        
        try:
            subprocess.run([python_cmd, "-m", "venv", Config.DASHBOARD_VENV], check=True)
            log(Colors.GREEN, "Dashboard virtual environment created successfully!")
            logger.info("Dashboard virtual environment created successfully")
            return True
        except subprocess.SubprocessError as e:
            error_msg = f"Failed to create dashboard virtual environment: {e}"
            logger.error(error_msg)
            log(Colors.RED, f"Error: {error_msg}")
            return False
    else:
        logger.info("Dashboard virtual environment already exists")
        return True

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(Config.DASHBOARD_VENV, "Scripts", "python.exe")
    else:
        return os.path.join(Config.DASHBOARD_VENV, "bin", "python")

def install_dependencies():
    """Install dashboard dependencies"""
    logger.info("Installing dashboard dependencies")
    
    venv_python = get_venv_python()
    requirements_file = os.path.join(Config.SCRIPT_DIR, "app", "dashboard", "requirements.txt")
    installed_flag = os.path.join(Config.DASHBOARD_VENV, "installed.flag")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        # Try to use a package.json instead (for Node.js dependencies)
        package_json = os.path.join(Config.SCRIPT_DIR, "app", "dashboard", "package.json")
        if os.path.exists(package_json):
            log(Colors.YELLOW, "Using package.json for Node.js dependencies")
            logger.info("Using package.json for Node.js dependencies")
            
            # Check if npm is installed
            try:
                subprocess.run(["npm", "--version"], check=True, capture_output=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                error_msg = "Error: npm is not installed or not in PATH. Please install Node.js and npm."
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                return False
            
            # Install Node.js dependencies
            try:
                if Config.OFFLINE_MODE:
                    # For offline mode, assume node_modules are already installed or use npm ci
                    if os.path.exists(os.path.join(Config.SCRIPT_DIR, "app", "dashboard", "node_modules")):
                        log(Colors.GREEN, "Using existing node_modules in offline mode")
                        logger.info("Using existing node_modules in offline mode")
                        
                        # Create flag file
                        with open(installed_flag, 'w') as f:
                            f.write(f"Dependencies installed on {datetime.datetime.now()}")
                        
                        return True
                    else:
                        error_msg = "Error: Cannot install Node.js dependencies in offline mode without existing node_modules"
                        logger.error(error_msg)
                        log(Colors.RED, error_msg)
                        return False
                else:
                    # For online mode, use npm install
                    log(Colors.YELLOW, "Installing Node.js dependencies...")
                    logger.info("Installing Node.js dependencies with npm install")
                    result = subprocess.run(["npm", "install"], 
                                          cwd=os.path.join(Config.SCRIPT_DIR, "app", "dashboard"),
                                          check=True)
                    
                    if result.returncode == 0:
                        log(Colors.GREEN, "Node.js dependencies installed successfully!")
                        logger.info("Node.js dependencies installed successfully")
                        
                        # Create flag file
                        with open(installed_flag, 'w') as f:
                            f.write(f"Dependencies installed on {datetime.datetime.now()}")
                        
                        return True
                    else:
                        error_msg = "Failed to install Node.js dependencies"
                        logger.error(error_msg)
                        log(Colors.RED, error_msg)
                        return False
            except subprocess.SubprocessError as e:
                error_msg = f"Error installing Node.js dependencies: {e}"
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                return False
        else:
            error_msg = f"Neither requirements.txt nor package.json found for dashboard"
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return False
    
    # If we're here, we have a requirements.txt to install
    if not os.path.exists(installed_flag) or Config.FORCE_INSTALL:
        log(Colors.YELLOW, "Installing Python dependencies...")
        logger.info("Installing Python dependencies")
        
        try:
            if Config.OFFLINE_MODE:
                vendor_dir = os.path.join(Config.SCRIPT_DIR, "vendor")
                if not os.path.exists(vendor_dir):
                    error_msg = f"Error: Vendor directory not found at {vendor_dir}"
                    logger.error(error_msg)
                    log(Colors.RED, error_msg)
                    return False
                
                # Install from vendor directory
                cmd = [venv_python, "-m", "pip", "install", "--no-index", 
                       f"--find-links={vendor_dir}", "-r", requirements_file]
            else:
                # Standard online installation
                cmd = [venv_python, "-m", "pip", "install", "-r", requirements_file]
            
            logger.debug(f"Running pip command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            
            if result.returncode == 0:
                log(Colors.GREEN, "Python dependencies installed successfully!")
                logger.info("Python dependencies installed successfully")
                
                # Create flag file
                with open(installed_flag, 'w') as f:
                    f.write(f"Dependencies installed on {datetime.datetime.now()}")
                
                return True
            else:
                error_msg = "Failed to install Python dependencies"
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                return False
        except subprocess.SubprocessError as e:
            error_msg = f"Error installing Python dependencies: {e}"
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return False
    else:
        log(Colors.GREEN, "Dependencies already installed!")
        logger.info("Dependencies already installed")
        return True

def check_for_updates():
    """Check for package updates"""
    if not Config.UPDATE_PACKAGES:
        return True
    
    logger.info("Checking for package updates")
    log(Colors.YELLOW, "Checking for package updates...")
    
    update_script = os.path.join(Config.SCRIPT_DIR, "scripts", 
                                "check_updates.py" if os.path.exists(os.path.join(Config.SCRIPT_DIR, "scripts", "check_updates.py")) 
                                else "check_updates.sh")
    
    if not os.path.exists(update_script):
        logger.warning("Update script not found, skipping update check")
        log(Colors.YELLOW, "Update script not found, skipping update check")
        return True
    
    if platform.system() == "Windows" and update_script.endswith(".sh"):
        logger.warning("Windows doesn't support shell scripts, skipping update check")
        log(Colors.YELLOW, "Windows doesn't support shell scripts, skipping update check")
        return True
    
    try:
        # Make the script executable on Unix systems
        if platform.system() != "Windows" and update_script.endswith(".sh"):
            logger.debug("Making update script executable")
            subprocess.run(["chmod", "+x", update_script], check=True)
        
        # Run the update script
        if update_script.endswith(".py"):
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            logger.debug(f"Running update script with {python_cmd}")
            result = subprocess.run([python_cmd, update_script], check=True)
        else:
            logger.debug("Running update shell script")
            result = subprocess.run([update_script], check=True)
        
        if result.returncode == 0:
            log(Colors.GREEN, "Update check completed successfully!")
            logger.info("Update check completed successfully")
            return True
        else:
            error_msg = f"Update check failed with exit code {result.returncode}"
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return False
    except subprocess.SubprocessError as e:
        error_msg = f"Error checking for updates: {e}"
        logger.error(error_msg)
        log(Colors.RED, error_msg)
        return False

def start_dashboard():
    """Start the dashboard server"""
    logger.info(f"Starting dashboard server on port {Config.PORT}")
    log(Colors.BLUE, f"Starting dashboard server on port {Config.PORT}...")
    
    dashboard_dir = os.path.join(Config.SCRIPT_DIR, "app", "dashboard")
    if not os.path.isdir(dashboard_dir):
        error_msg = f"Dashboard directory not found at {dashboard_dir}"
        logger.error(error_msg)
        log(Colors.RED, error_msg)
        return None
    
    # Look for start script (package.json npm start or similar)
    package_json = os.path.join(dashboard_dir, "package.json")
    if os.path.exists(package_json):
        # Using Node.js dashboard
        logger.info("Using Node.js dashboard")
        
        try:
            env = os.environ.copy()
            env["PORT"] = str(Config.PORT)
            
            if Config.DEBUG:
                env["DEBUG"] = "true"
            
            logger.debug("Starting npm process")
            process = subprocess.Popen(["npm", "start"], 
                                     cwd=dashboard_dir,
                                     env=env,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     bufsize=1)
            
            # Start threads to read output
            import threading
            threading.Thread(target=log_process_output, 
                            args=(process, "dashboard", "stdout"), 
                            daemon=True).start()
            threading.Thread(target=log_process_output, 
                            args=(process, "dashboard", "stderr"), 
                            daemon=True).start()
            
            # Give the server time to start
            time.sleep(5)
            
            if process.poll() is None:
                log(Colors.GREEN, f"Dashboard server started successfully on port {Config.PORT}!")
                logger.info(f"Dashboard server started successfully on port {Config.PORT}")
                return process
            else:
                error_msg = f"Dashboard process exited with code {process.poll()}"
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                return None
        except Exception as e:
            error_msg = f"Error starting Node.js dashboard: {e}"
            logger.error(error_msg, exc_info=True)
            log(Colors.RED, error_msg)
            return None
    else:
        # Check for a Flask dashboard or similar Python-based dashboard
        app_py = os.path.join(dashboard_dir, "app.py")
        if os.path.exists(app_py):
            logger.info("Using Python Flask dashboard")
            
            try:
                venv_python = get_venv_python()
                
                # Prepare the command
                cmd = [venv_python, app_py, "--port", str(Config.PORT)]
                if Config.DEBUG:
                    cmd.append("--debug")
                
                logger.debug(f"Running command: {' '.join(cmd)}")
                process = subprocess.Popen(cmd,
                                         cwd=dashboard_dir,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True,
                                         bufsize=1)
                
                # Start threads to read output
                import threading
                threading.Thread(target=log_process_output, 
                                args=(process, "dashboard", "stdout"), 
                                daemon=True).start()
                threading.Thread(target=log_process_output, 
                                args=(process, "dashboard", "stderr"), 
                                daemon=True).start()
                
                # Give the server time to start
                time.sleep(3)
                
                if process.poll() is None:
                    log(Colors.GREEN, f"Dashboard server started successfully on port {Config.PORT}!")
                    logger.info(f"Dashboard server started successfully on port {Config.PORT}")
                    return process
                else:
                    error_msg = f"Dashboard process exited with code {process.poll()}"
                    logger.error(error_msg)
                    log(Colors.RED, error_msg)
                    return None
            except Exception as e:
                error_msg = f"Error starting Python dashboard: {e}"
                logger.error(error_msg, exc_info=True)
                log(Colors.RED, error_msg)
                return None
        else:
            error_msg = "Could not find dashboard entry point (package.json or app.py)"
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return None

def log_process_output(process, name, stream_name):
    """Log the output from a process stream"""
    stream = process.stdout if stream_name == "stdout" else process.stderr
    
    for line in iter(stream.readline, ''):
        if not line:
            break
        line = line.strip()
        if stream_name == "stderr":
            logger.error(f"{name}: {line}")
        else:
            logger.info(f"{name}: {line}")

def main():
    """Main function"""
    logger.info(f"Starting dashboard script on {platform.system()} {platform.release()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script directory: {Config.SCRIPT_DIR}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Secure Video Summarizer dashboard")
    parser.add_argument("--install-deps", action="store_true", help="Force reinstallation of dependencies")
    parser.add_argument("--update", action="store_true", help="Check for package updates")
    parser.add_argument("--port", type=int, default=Config.PORT, help="Port for the dashboard server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--offline", action="store_true", help="Enable offline mode")
    
    args = parser.parse_args()
    logger.debug(f"Command line arguments: {args}")
    
    # Update configuration from command line arguments
    Config.PORT = args.port
    Config.DEBUG = args.debug
    Config.FORCE_INSTALL = args.install_deps
    Config.UPDATE_PACKAGES = args.update
    Config.OFFLINE_MODE = args.offline
    
    # Set logging level based on debug mode
    if Config.DEBUG:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled - verbose logging activated")
    
    # Verify we're in the right directory
    if not verify_directory():
        logger.error("Directory verification failed. Exiting.")
        sys.exit(1)
    
    # Create virtual environment if needed
    if not create_virtualenv():
        logger.error("Virtual environment creation failed. Exiting.")
        sys.exit(1)
    
    # Check for updates if requested
    if Config.UPDATE_PACKAGES and not check_for_updates():
        logger.warning("Update check failed, continuing anyway")
        log(Colors.YELLOW, "Update check failed, continuing anyway")
    
    # Install dependencies if needed
    if not install_dependencies():
        logger.error("Dependency installation failed. Exiting.")
        sys.exit(1)
    
    # Start the dashboard
    process = start_dashboard()
    
    if process:
        log(Colors.GREEN, f"Dashboard server running at http://localhost:{Config.PORT}")
        logger.info(f"Dashboard server running at http://localhost:{Config.PORT}")
        
        def handle_exit(sig, frame):
            """Handle graceful shutdown on exit signal"""
            logger.info("Received shutdown signal")
            log(Colors.YELLOW, "Shutting down dashboard server...")
            
            # First try gentle termination
            process.terminate()
            
            try:
                # Wait up to 5 seconds for the process to terminate
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated within timeout
                logger.warning("Dashboard not responding to termination, force killing")
                log(Colors.RED, "Dashboard not responding to termination, force killing")
                process.kill()
            
            logger.info("Dashboard server shutdown complete")
            log(Colors.GREEN, "Dashboard server shutdown complete")
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
        
        try:
            # Wait for the process to complete
            process.wait()
        except KeyboardInterrupt:
            # Will be caught by signal handler
            pass
    else:
        logger.error("Failed to start dashboard. Exiting.")
        log(Colors.RED, "Failed to start dashboard. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main() 