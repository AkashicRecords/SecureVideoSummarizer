#!/usr/bin/env python3
"""
Cross-platform startup script for the Secure Video Summarizer application.
This script provides OS-agnostic functionality equivalent to start_svs_application.sh.
"""

import os
import sys
import subprocess
import platform
import socket
import time
import argparse
import signal
import shutil
from pathlib import Path
import webbrowser
import json
import atexit
import logging
import datetime

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"svs_startup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SVS")

# ANSI colors for Unix terminals
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

# For Windows, we'll use empty strings
if platform.system() == 'Windows':
    for attr in dir(Colors):
        if not attr.startswith('__'):
            setattr(Colors, attr, '')

# Default configuration
class Config:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
    BACKEND_PORT = 8081
    DASHBOARD_PORT = 8080
    RUN_BACKEND = True
    RUN_DASHBOARD = True
    RUN_TESTS = False
    INSTALL_DEPENDENCIES = True
    FORCE_UPDATE_DEPS = False
    DEBUG_MODE = False
    DEVELOPMENT_MODE = False
    OFFLINE_MODE = False
    SAVE_CONFIG = True
    COLD_START = False
    ENVIRONMENT = 'development'
    QUIET_MODE = False
    LOG_LEVEL = logging.INFO

# Global variables for process management
backend_process = None
dashboard_process = None
all_processes = []
pid_files = []

def log(color, message):
    """Print colored log messages"""
    if not Config.QUIET_MODE:
        print(f"{color}{message}{Colors.NC}")
    logger.info(message)

def show_status(message):
    """Display status message with dots"""
    if not Config.QUIET_MODE:
        dots_count = 40
        dots_length = dots_count - len(message)
        dots = '.' * dots_length
        print(f"{message}{dots}", end='', flush=True)
    logger.info(f"Status: {message}")

def show_result(success):
    """Show result of an operation"""
    if not Config.QUIET_MODE:
        if success:
            print(f"{Colors.GREEN}Done!{Colors.NC}")
            logger.info("Result: Success")
        else:
            print(f"{Colors.RED}Failed!{Colors.NC}")
            logger.error("Result: Failed")

def verify_directories():
    """Verify that necessary directories exist"""
    logger.info("Verifying directory structure")
    
    # Check if we're in the right directory
    if not os.path.isdir(Config.BACKEND_DIR):
        error_msg = f"Backend directory not found at {Config.BACKEND_DIR}"
        logger.error(error_msg)
        log(Colors.RED, f"Error: {error_msg}")
        log(Colors.RED, "Make sure you're running this script from the project root directory.")
        return False
    
    # Check for other critical directories
    required_dirs = [
        (Config.BACKEND_DIR, "Backend directory"),
        (os.path.join(Config.BACKEND_DIR, "app"), "Backend app directory"),
        (os.path.join(Config.BACKEND_DIR, "scripts"), "Backend scripts directory")
    ]
    
    for dir_path, dir_desc in required_dirs:
        if not os.path.isdir(dir_path):
            error_msg = f"{dir_desc} not found at {dir_path}"
            logger.error(error_msg)
            log(Colors.RED, f"Error: {error_msg}")
            return False
    
    logger.info("Directory structure verified successfully")
    return True

def check_venv_exists():
    """Check if virtual environments exist, create them if needed"""
    logger.info("Checking virtual environments")
    
    backend_venv = os.path.join(Config.BACKEND_DIR, "venv")
    dashboard_venv = os.path.join(Config.BACKEND_DIR, "dashboard_venv")
    
    # Check backend venv
    if not os.path.isdir(backend_venv):
        log(Colors.YELLOW, "Backend virtual environment not found. Creating...")
        logger.info("Creating backend virtual environment")
        try:
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            subprocess.run([python_cmd, "-m", "venv", backend_venv], check=True)
            log(Colors.GREEN, "Backend virtual environment created successfully!")
            logger.info("Backend virtual environment created successfully")
        except Exception as e:
            error_msg = f"Failed to create backend virtual environment: {e}"
            logger.error(error_msg)
            log(Colors.RED, f"Error: {error_msg}")
            return False
    
    # Check dashboard venv if needed
    if Config.RUN_DASHBOARD and not os.path.isdir(dashboard_venv):
        log(Colors.YELLOW, "Dashboard virtual environment not found. Creating...")
        logger.info("Creating dashboard virtual environment")
        try:
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            subprocess.run([python_cmd, "-m", "venv", dashboard_venv], check=True)
            log(Colors.GREEN, "Dashboard virtual environment created successfully!")
            logger.info("Dashboard virtual environment created successfully")
        except Exception as e:
            error_msg = f"Failed to create dashboard virtual environment: {e}"
            logger.error(error_msg)
            log(Colors.RED, f"Error: {error_msg}")
            return False
    
    logger.info("Virtual environment check completed successfully")
    return True

def is_in_virtualenv():
    """Check if we're currently running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def is_port_in_use(port):
    """Check if a port is in use"""
    logger.debug(f"Checking if port {port} is in use")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', port)) == 0
        logger.debug(f"Port {port} is {'in use' if result else 'free'}")
        return result

def kill_process_on_port(port):
    """Kill process on a given port in a cross-platform way"""
    logger.info(f"Attempting to kill process on port {port}")
    show_status(f"Checking for processes on port {port}")
    
    if is_port_in_use(port):
        show_result(False)
        show_status(f"Terminating process on port {port}")
        
        try:
            if platform.system() == 'Windows':
                logger.debug(f"Using Windows method to kill process on port {port}")
                subprocess.run(f"FOR /F \"tokens=5\" %P IN ('netstat -ano ^| findstr {port}') DO taskkill /F /PID %P", shell=True)
            else:
                # Unix systems
                logger.debug(f"Using Unix method to kill process on port {port}")
                pid_cmd = subprocess.run(f"lsof -ti:{port}", shell=True, capture_output=True, text=True)
                if pid_cmd.stdout.strip():
                    logger.debug(f"Found PID {pid_cmd.stdout.strip()} on port {port}")
                    subprocess.run(f"kill -9 {pid_cmd.stdout.strip()}", shell=True)
            
            time.sleep(2)
            if is_port_in_use(port):
                show_result(False)
                error_msg = f"Failed to terminate process on port {port}."
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                return False
            else:
                show_result(True)
                logger.info(f"Successfully terminated process on port {port}")
                return True
        except Exception as e:
            show_result(False)
            error_msg = f"Error killing process on port {port}: {e}"
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return False
    else:
        show_result(True)
        logger.info(f"No process found on port {port}")
        return True

def verify_ports_clear():
    """Verify all required ports are clear"""
    max_retries = 3
    retry_count = 0
    all_clear = False
    
    show_status("Verifying all ports are clear")
    
    while retry_count < max_retries and not all_clear:
        if is_port_in_use(Config.BACKEND_PORT):
            show_result(False)
            show_status(f"Force closing port {Config.BACKEND_PORT} (attempt {retry_count+1}/{max_retries})")
            kill_process_on_port(Config.BACKEND_PORT)
            time.sleep(2)
        elif is_port_in_use(Config.DASHBOARD_PORT):
            show_result(False)
            show_status(f"Force closing port {Config.DASHBOARD_PORT} (attempt {retry_count+1}/{max_retries})")
            kill_process_on_port(Config.DASHBOARD_PORT)
            time.sleep(2)
        else:
            all_clear = True
            show_result(True)
            break
        
        retry_count += 1
        if retry_count == max_retries and (is_port_in_use(Config.BACKEND_PORT) or is_port_in_use(Config.DASHBOARD_PORT)):
            log(Colors.RED, f"CRITICAL ERROR: Could not clear ports after {max_retries} attempts.")
            log(Colors.RED, f"Please manually check and kill processes on ports {Config.BACKEND_PORT} and {Config.DASHBOARD_PORT}.")
            sys.exit(1)
    
    if all_clear:
        show_status("Confirming all ports are clear for startup")
        show_result(True)

def check_python_available():
    """Check if Python 3 is available"""
    try:
        subprocess.run(["python3", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # On Windows, try 'python' instead
            subprocess.run(["python", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

def check_venv_module():
    """Check if the venv module is available"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(["python", "-m", "venv", "--help"], capture_output=True)
        else:
            result = subprocess.run(["python3", "-m", "venv", "--help"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False

def check_internet_connection():
    """Check internet connectivity in a cross-platform way"""
    show_status("Checking internet connection")
    hosts = ["github.com", "google.com"]
    
    for host in hosts:
        try:
            # Using socket instead of ping for better cross-platform compatibility
            socket.create_connection((host, 80), timeout=2)
            show_result(True)
            return True
        except (socket.timeout, socket.error):
            continue
    
    show_result(False)
    return False

def find_pid_by_name(process_name):
    """Find process IDs by name in a cross-platform way"""
    pids = []
    
    try:
        if platform.system() == 'Windows':
            output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                            text=True, errors='ignore')
            for line in output.strip().split('\n'):
                if process_name in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pids.append(int(parts[1]))
                        except ValueError:
                            continue
        else:
            # Unix systems
            output = subprocess.check_output(['pgrep', '-f', process_name], 
                                           text=True, errors='ignore')
            for line in output.strip().split('\n'):
                if line:
                    try:
                        pids.append(int(line))
                    except ValueError:
                        continue
    except subprocess.SubprocessError:
        pass
    
    return pids

def terminate_process(process, process_name=""):
    """Terminate a process with a proper shutdown procedure"""
    if process is None:
        return
    
    try:
        # First try gentle termination
        process.terminate()
        
        # Wait up to 5 seconds for the process to terminate
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log(Colors.YELLOW, f"Process {process_name} not responding to termination. Forcefully killing...")
            process.kill()
    except Exception as e:
        log(Colors.RED, f"Error while terminating {process_name}: {e}")

def kill_pid_file_processes():
    """Kill processes using their PID files"""
    for pid_file in pid_files:
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                show_status(f"Stopping process with PID {pid}")
                
                try:
                    if platform.system() == 'Windows':
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    else:
                        # First try a gentle SIGTERM
                        os.kill(pid, signal.SIGTERM)
                        
                        # Give it some time to shut down
                        time.sleep(2)
                        
                        # Check if it's still running
                        try:
                            os.kill(pid, 0)  # Signal 0 is used to check if process exists
                            # Process still exists, force kill
                            os.kill(pid, signal.SIGKILL)
                        except OSError:
                            # Process doesn't exist anymore
                            pass
                    
                    show_result(True)
                except Exception as e:
                    show_result(False)
                    log(Colors.RED, f"Error killing process with PID {pid}: {e}")
                
                # Remove the PID file
                os.remove(pid_file)
            except Exception as e:
                log(Colors.RED, f"Error processing PID file {pid_file}: {e}")

def cleanup():
    """Perform cleanup when the script exits"""
    log(Colors.YELLOW, "Shutting down all services...")
    
    # First terminate tracked processes
    if backend_process:
        show_status("Stopping backend server")
        terminate_process(backend_process, "backend server")
        show_result(True)
    
    if dashboard_process:
        show_status("Stopping dashboard server")
        terminate_process(dashboard_process, "dashboard server")
        show_result(True)
    
    # Then any additional processes we're tracking
    for i, process in enumerate(all_processes):
        if process and process.poll() is None:  # If process is still running
            show_status(f"Stopping additional process {i+1}")
            terminate_process(process, f"process {i+1}")
            show_result(True)
    
    # Finally, check for any processes using our ports
    if is_port_in_use(Config.BACKEND_PORT):
        kill_process_on_port(Config.BACKEND_PORT)
    
    if is_port_in_use(Config.DASHBOARD_PORT):
        kill_process_on_port(Config.DASHBOARD_PORT)
    
    # Kill processes identified by PID files
    kill_pid_file_processes()
    
    log(Colors.GREEN, "Shutdown complete. Thanks for using Secure Video Summarizer!")

def start_backend_server():
    """Start the backend server"""
    global backend_process
    
    logger.info("Starting backend server")
    log(Colors.BLUE, "=== Starting Backend Server ===")
    
    # Verify correct backend directory
    if not os.path.isdir(Config.BACKEND_DIR):
        error_msg = f"Backend directory not found at {Config.BACKEND_DIR}"
        logger.error(error_msg)
        log(Colors.RED, f"Error: {error_msg}")
        return False
    
    backend_script_path = os.path.join(Config.BACKEND_DIR, "run_backend.py" if os.path.exists(os.path.join(Config.BACKEND_DIR, "run_backend.py")) else "run_backend.sh")
    logger.debug(f"Using backend script: {backend_script_path}")
    
    if not os.path.exists(backend_script_path):
        error_msg = f"Backend script not found at {backend_script_path}"
        logger.error(error_msg)
        log(Colors.RED, f"Error: {error_msg}")
        return False
    
    cmd = [backend_script_path]
    
    # Add appropriate options
    if Config.DEBUG_MODE:
        cmd.append("--debug")
    else:
        cmd.append("--no-debug")
    
    cmd.extend(["--port", str(Config.BACKEND_PORT)])
    cmd.extend(["--config", Config.ENVIRONMENT])
    
    if Config.INSTALL_DEPENDENCIES:
        cmd.append("--install-deps")
    
    if Config.FORCE_UPDATE_DEPS:
        cmd.append("--update")
    
    if Config.OFFLINE_MODE:
        cmd.append("--offline")
    
    logger.debug(f"Backend command: {cmd}")
    
    # Start backend process
    try:
        log(Colors.YELLOW, f"Starting backend server on port {Config.BACKEND_PORT}...")
        
        # Make the script executable on Unix systems
        if platform.system() != 'Windows' and backend_script_path.endswith('.sh'):
            logger.debug("Making shell script executable")
            subprocess.run(["chmod", "+x", backend_script_path], check=True)
        
        if platform.system() == 'Windows' and backend_script_path.endswith('.sh'):
            # On Windows, if we only have .sh file, notify the user
            error_msg = "Error: Shell script not supported on Windows. Please use the Python version."
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            return False
        
        # Start backend process
        if backend_script_path.endswith('.py'):
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            logger.debug(f"Using Python command: {python_cmd}")
            backend_process = subprocess.Popen([python_cmd, backend_script_path] + cmd[1:], 
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                              text=True, bufsize=1, 
                                              cwd=Config.PROJECT_ROOT)
            
            # Start threads to read output
            threading.Thread(target=log_process_output, args=(backend_process, "backend", "stdout"), daemon=True).start()
            threading.Thread(target=log_process_output, args=(backend_process, "backend", "stderr"), daemon=True).start()
        else:
            backend_process = subprocess.Popen(cmd, shell=platform.system() == 'Windows',
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              text=True, bufsize=1,
                                              cwd=Config.PROJECT_ROOT)
            
            # Start threads to read output
            threading.Thread(target=log_process_output, args=(backend_process, "backend", "stdout"), daemon=True).start()
            threading.Thread(target=log_process_output, args=(backend_process, "backend", "stderr"), daemon=True).start()
        
        # Add to our list of processes
        all_processes.append(backend_process)
        
        # Give some time for the server to start
        time.sleep(3)
        
        # Check if the process is still running and the port is active
        if backend_process.poll() is None and is_port_in_use(Config.BACKEND_PORT):
            logger.info(f"Backend server started successfully on port {Config.BACKEND_PORT}")
            log(Colors.GREEN, f"Backend server started successfully on port {Config.BACKEND_PORT}!")
            return True
        else:
            if backend_process.poll() is not None:
                error_msg = f"Backend process exited with code {backend_process.poll()}"
            else:
                error_msg = f"Backend process started but port {Config.BACKEND_PORT} is not active"
            
            logger.error(error_msg)
            log(Colors.RED, f"Failed to start backend server. {error_msg}")
            return False
    
    except Exception as e:
        error_msg = f"Error starting backend server: {e}"
        logger.error(error_msg, exc_info=True)
        log(Colors.RED, error_msg)
        return False

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

def start_dashboard_server():
    """Start the dashboard server"""
    global dashboard_process
    
    log(Colors.BLUE, "=== Starting Dashboard Server ===")
    
    dashboard_script_path = os.path.join(Config.BACKEND_DIR, "run_dashboard.py" if os.path.exists(os.path.join(Config.BACKEND_DIR, "run_dashboard.py")) else "run_dashboard.sh")
    
    cmd = [dashboard_script_path]
    
    # Add appropriate options
    if Config.DEBUG_MODE:
        cmd.append("--debug")
    
    cmd.extend(["--port", str(Config.DASHBOARD_PORT)])
    
    if Config.INSTALL_DEPENDENCIES:
        cmd.append("--install-deps")
    
    if Config.FORCE_UPDATE_DEPS:
        cmd.append("--update")
    
    if Config.OFFLINE_MODE:
        cmd.append("--offline")
    
    # Start dashboard process
    try:
        log(Colors.YELLOW, f"Starting dashboard server on port {Config.DASHBOARD_PORT}...")
        
        # Make the script executable on Unix systems
        if platform.system() != 'Windows' and dashboard_script_path.endswith('.sh'):
            subprocess.run(["chmod", "+x", dashboard_script_path], check=True)
        
        if platform.system() == 'Windows' and dashboard_script_path.endswith('.sh'):
            # On Windows, if we only have .sh file, notify the user
            log(Colors.RED, "Error: Shell script not supported on Windows. Please use the Python version.")
            return False
        
        # Start dashboard process
        if dashboard_script_path.endswith('.py'):
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            dashboard_process = subprocess.Popen([python_cmd, dashboard_script_path] + cmd[1:])
        else:
            dashboard_process = subprocess.Popen(cmd, shell=platform.system() == 'Windows')
        
        # Add to our list of processes
        all_processes.append(dashboard_process)
        
        # Give some time for the server to start
        time.sleep(3)
        
        # Check if the process is still running and the port is active
        if dashboard_process.poll() is None and is_port_in_use(Config.DASHBOARD_PORT):
            log(Colors.GREEN, f"Dashboard server started successfully on port {Config.DASHBOARD_PORT}!")
            
            # Try to open the dashboard in the browser
            if not Config.QUIET_MODE:
                dashboard_url = f"http://localhost:{Config.DASHBOARD_PORT}"
                try:
                    webbrowser.open(dashboard_url)
                    log(Colors.BLUE, f"Dashboard opened in browser: {dashboard_url}")
                except Exception as e:
                    log(Colors.YELLOW, f"Dashboard available at: {dashboard_url}")
            
            return True
        else:
            log(Colors.RED, "Failed to start dashboard server. Check logs for details.")
            return False
    
    except Exception as e:
        log(Colors.RED, f"Error starting dashboard server: {e}")
        return False

def run_tests():
    """Run the test suite"""
    log(Colors.BLUE, "=== Running Tests ===")
    
    test_script_path = os.path.join(Config.PROJECT_ROOT, "run_tests.py" if os.path.exists(os.path.join(Config.PROJECT_ROOT, "run_tests.py")) else "run_tests.sh")
    
    try:
        # Make the script executable on Unix systems
        if platform.system() != 'Windows' and test_script_path.endswith('.sh'):
            subprocess.run(["chmod", "+x", test_script_path], check=True)
        
        if platform.system() == 'Windows' and test_script_path.endswith('.sh'):
            # On Windows, if we only have .sh file, notify the user
            log(Colors.RED, "Error: Shell script not supported on Windows. Please use the Python version.")
            return False
        
        # Run tests
        log(Colors.YELLOW, "Running test suite...")
        
        if test_script_path.endswith('.py'):
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            result = subprocess.run([python_cmd, test_script_path], capture_output=True, text=True)
        else:
            result = subprocess.run([test_script_path], capture_output=True, text=True, shell=platform.system() == 'Windows')
        
        # Output test results
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            log(Colors.GREEN, "Tests completed successfully!")
            return True
        else:
            log(Colors.RED, f"Tests failed with exit code {result.returncode}")
            return False
    
    except Exception as e:
        log(Colors.RED, f"Error running tests: {e}")
        return False

def summarize_options():
    """Display a summary of the current configuration"""
    log(Colors.CYAN, "=== Secure Video Summarizer Configuration ===")
    
    if Config.RUN_TESTS:
        print(f"Mode: Test Runner")
        print(f"Debug Mode: {'Enabled' if Config.DEBUG_MODE else 'Disabled'}")
    else:
        if Config.DEVELOPMENT_MODE:
            print(f"Mode: Development")
        elif Config.COLD_START:
            print(f"Mode: Cold Start")
        else:
            print(f"Mode: {'Standard' if Config.RUN_BACKEND and Config.RUN_DASHBOARD else 'Custom'}")
        
        print(f"Backend Server: {'Enabled' if Config.RUN_BACKEND else 'Disabled'} (Port: {Config.BACKEND_PORT})")
        print(f"Dashboard Server: {'Enabled' if Config.RUN_DASHBOARD else 'Disabled'} (Port: {Config.DASHBOARD_PORT})")
        print(f"Install Dependencies: {'Yes' if Config.INSTALL_DEPENDENCIES else 'No'}")
        print(f"Debug Mode: {'Enabled' if Config.DEBUG_MODE else 'Disabled'}")
        print(f"Offline Mode: {'Enabled' if Config.OFFLINE_MODE else 'Disabled'}")
    
    print()

def handle_shutdown_signal(sig, frame):
    """Handle shutdown signals gracefully"""
    print()  # Ensure we're on a new line
    log(Colors.YELLOW, "Shutdown signal received. Cleaning up...")
    sys.exit(0)  # This will trigger the atexit handlers

def main():
    """Main function"""
    # Set logging level based on debug mode
    if Config.DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(Config.LOG_LEVEL)
    
    # Log system information
    logger.info(f"Starting SVS Application on {platform.system()} {platform.release()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Project root: {Config.PROJECT_ROOT}")
    
    # Register cleanup handler to run on exit
    atexit.register(cleanup)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the Secure Video Summarizer application")
    parser.add_argument("--mode", choices=["both", "backend", "dashboard", "cold", "dev", "test"], 
                      default="both", help="Startup mode")
    parser.add_argument("--backend-port", type=int, default=Config.BACKEND_PORT, 
                      help="Backend server port")
    parser.add_argument("--dashboard-port", type=int, default=Config.DASHBOARD_PORT, 
                      help="Dashboard server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--offline", action="store_true", help="Enable offline mode")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--force-update", action="store_true", help="Force update dependencies")
    parser.add_argument("--save-config", action="store_true", help="Save configuration for future use")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (reduced output)")
    
    args = parser.parse_args()
    logger.debug(f"Command line arguments: {args}")
    
    # Apply command line arguments to config
    Config.BACKEND_PORT = args.backend_port
    Config.DASHBOARD_PORT = args.dashboard_port
    Config.DEBUG_MODE = args.debug
    Config.OFFLINE_MODE = args.offline
    Config.INSTALL_DEPENDENCIES = not args.no_deps
    Config.FORCE_UPDATE_DEPS = args.force_update
    Config.SAVE_CONFIG = args.save_config
    Config.QUIET_MODE = args.quiet
    
    # Set logging level based on debug mode
    if Config.DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled - verbose logging activated")
    
    logger.info(f"Configuration: {vars(Config)}")
    
    if args.mode == "backend":
        Config.RUN_BACKEND = True
        Config.RUN_DASHBOARD = False
        logger.info("Mode: Backend only")
    elif args.mode == "dashboard":
        Config.RUN_BACKEND = False
        Config.RUN_DASHBOARD = True
        logger.info("Mode: Dashboard only")
    elif args.mode == "cold":
        Config.COLD_START = True
        logger.info("Mode: Cold start")
    elif args.mode == "dev":
        Config.DEVELOPMENT_MODE = True
        Config.DEBUG_MODE = True
        logger.setLevel(logging.DEBUG)
        logger.info("Mode: Development (debug enabled)")
    elif args.mode == "test":
        Config.RUN_TESTS = True
        logger.info("Mode: Test runner")
    else:
        logger.info("Mode: Standard (both backend and dashboard)")
    
    # Display welcome message
    if not Config.QUIET_MODE:
        print("\n" + "=" * 60)
        log(Colors.BLUE, "       Secure Video Summarizer - Startup Tool")
        print("=" * 60 + "\n")
    
    # Verify directories first
    if not verify_directories():
        logger.error("Directory verification failed. Exiting.")
        sys.exit(1)
    
    # Check if running in a virtual environment
    if is_in_virtualenv():
        logger.warning("Running in a virtual environment. This may cause conflicts.")
        log(Colors.YELLOW, "Warning: You are running this script from within a virtual environment.")
        log(Colors.YELLOW, "This may cause conflicts with the virtual environments created for SVS components.")
    
    # Verify virtual environments
    if not check_venv_exists():
        logger.error("Virtual environment check failed. Exiting.")
        sys.exit(1)
    
    # Pre-startup checks
    verify_ports_clear()
    
    # Check for Python environment
    if not check_python_available():
        error_msg = "Error: Python 3 is not available. Please install Python 3.6 or newer."
        logger.error(error_msg)
        log(Colors.RED, error_msg)
        sys.exit(1)
    
    if not check_venv_module():
        error_msg = "Error: Python venv module is not available. This is required for virtual environments."
        logger.error(error_msg)
        log(Colors.RED, error_msg)
        sys.exit(1)
    
    # Summarize options
    summarize_options()
    
    # Run tests if configured
    if Config.RUN_TESTS:
        logger.info("Running tests")
        success = run_tests()
        if success:
            logger.info("Tests completed successfully")
        else:
            logger.error("Tests failed")
        sys.exit(0 if success else 1)
    
    # Start backend if configured
    if Config.RUN_BACKEND:
        logger.info("Starting backend server")
        if not start_backend_server():
            error_msg = "Backend server failed to start. Exiting."
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            sys.exit(1)
    
    # Start dashboard if configured
    if Config.RUN_DASHBOARD:
        logger.info("Starting dashboard server")
        if not start_dashboard_server():
            error_msg = "Dashboard server failed to start. Exiting."
            logger.error(error_msg)
            log(Colors.RED, error_msg)
            sys.exit(1)
    
    logger.info("Startup complete")
    log(Colors.GREEN, "Startup complete!")
    
    if not Config.QUIET_MODE:
        dashboard_url = f"http://localhost:{Config.DASHBOARD_PORT}" if Config.RUN_DASHBOARD else "Not running"
        backend_url = f"http://localhost:{Config.BACKEND_PORT}" if Config.RUN_BACKEND else "Not running"
        
        log(Colors.CYAN, "=== Service URLs ===")
        print(f"Backend API: {backend_url}")
        print(f"Dashboard: {dashboard_url}")
        print()
        log(Colors.YELLOW, "Press Ctrl+C to stop the application...")
    
    try:
        # Keep the script running until user interrupts
        while True:
            time.sleep(1)
            
            # Check if our processes are still running
            if Config.RUN_BACKEND and backend_process and backend_process.poll() is not None:
                error_msg = "Backend server has stopped unexpectedly!"
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                sys.exit(1)
            
            if Config.RUN_DASHBOARD and dashboard_process and dashboard_process.poll() is not None:
                error_msg = "Dashboard server has stopped unexpectedly!"
                logger.error(error_msg)
                log(Colors.RED, error_msg)
                sys.exit(1)
    except KeyboardInterrupt:
        # Will trigger our atexit handler
        logger.info("Received keyboard interrupt, initiating shutdown")
        pass

if __name__ == "__main__":
    # Need to import threading here to avoid issues with signal handlers
    import threading
    main() 