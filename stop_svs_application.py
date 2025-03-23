#!/usr/bin/env python3
"""
Cross-platform script to stop the Secure Video Summarizer application.
This script terminates both backend and dashboard server processes.
"""

import os
import sys
import signal
import subprocess
import platform
import psutil
import argparse
import time
import logging
import datetime

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"stop_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SVS_Stop")

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
    BACKEND_PORT = 5000
    DASHBOARD_PORT = 8080
    FORCE_KILL = False
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
    BACKEND_PID_FILE = os.path.join(BACKEND_DIR, "backend.pid")
    DASHBOARD_PID_FILE = os.path.join(BACKEND_DIR, "dashboard.pid")

def log(color, message):
    """Print colored log messages"""
    print(f"{color}{message}{Colors.NC}")
    logger.info(message)

def find_process_by_port(port):
    """Find a process using a specific port"""
    logger.debug(f"Looking for process using port {port}")
    
    try:
        if platform.system() == "Windows":
            # Use netstat on Windows
            netstat_output = subprocess.check_output(["netstat", "-ano"], text=True)
            for line in netstat_output.split('\n'):
                if f":{port}" in line and ("LISTENING" in line or "ESTABLISHED" in line):
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        logger.debug(f"Found process {pid} using port {port}")
                        return int(pid)
        else:
            # Use lsof on Unix-like systems
            lsof_output = subprocess.check_output(["lsof", "-i", f":{port}"], text=True)
            for line in lsof_output.split('\n')[1:]:  # Skip header
                if line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        logger.debug(f"Found process {pid} using port {port}")
                        return int(pid)
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"Error looking for process by port: {e}")
    
    logger.debug(f"No process found using port {port}")
    return None

def read_pid_file(pid_file):
    """Read process ID from a PID file"""
    logger.debug(f"Trying to read PID from {pid_file}")
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                logger.debug(f"Read PID {pid} from {pid_file}")
                return pid
        except (IOError, ValueError) as e:
            logger.warning(f"Error reading PID file {pid_file}: {e}")
    
    logger.debug(f"PID file {pid_file} not found or invalid")
    return None

def is_process_running(pid):
    """Check if a process with the given PID is running"""
    logger.debug(f"Checking if process {pid} is running")
    
    try:
        process = psutil.Process(pid)
        status = process.status()
        logger.debug(f"Process {pid} status: {status}")
        return status != psutil.STATUS_ZOMBIE and status != psutil.STATUS_DEAD
    except psutil.NoSuchProcess:
        logger.debug(f"Process {pid} not found")
        return False

def kill_process(pid, force=False, process_name=""):
    """Kill a process by PID"""
    if not pid:
        logger.debug(f"No PID provided for {process_name}")
        return False
    
    logger.info(f"Attempting to stop {process_name} process (PID: {pid})")
    log(Colors.YELLOW, f"Stopping {process_name} process (PID: {pid})...")
    
    try:
        process = psutil.Process(pid)
        
        # First try gentle termination
        if not force:
            process.terminate()
            try:
                # Wait up to 5 seconds for the process to terminate
                process.wait(timeout=5)
                log(Colors.GREEN, f"{process_name} process stopped successfully!")
                logger.info(f"{process_name} process (PID: {pid}) stopped successfully")
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"{process_name} process (PID: {pid}) not responding to termination")
                log(Colors.YELLOW, f"{process_name} process not responding, force killing...")
        
        # Force kill if requested or if termination timed out
        process.kill()
        process.wait(timeout=2)
        log(Colors.GREEN, f"{process_name} process force killed successfully!")
        logger.info(f"{process_name} process (PID: {pid}) force killed successfully")
        return True
    
    except psutil.NoSuchProcess:
        log(Colors.GREEN, f"{process_name} process is not running (PID: {pid})")
        logger.info(f"{process_name} process (PID: {pid}) is not running")
        return True
    except psutil.AccessDenied:
        log(Colors.RED, f"Access denied when trying to kill {process_name} process (PID: {pid})")
        logger.error(f"Access denied when trying to kill {process_name} process (PID: {pid})")
        return False
    except Exception as e:
        log(Colors.RED, f"Error killing {process_name} process (PID: {pid}): {e}")
        logger.error(f"Error killing {process_name} process (PID: {pid}): {e}", exc_info=True)
        return False

def find_python_processes(name_pattern):
    """Find Python processes with a specific command line pattern"""
    logger.debug(f"Looking for Python processes with pattern: {name_pattern}")
    result = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and len(cmdline) > 1:
                cmdline_str = ' '.join(cmdline)
                if 'python' in proc.info['name'].lower() and name_pattern in cmdline_str:
                    logger.debug(f"Found matching process: PID {proc.info['pid']}, cmd: {cmdline_str[:100]}")
                    result.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return result

def find_node_processes(name_pattern):
    """Find Node.js processes with a specific command line pattern"""
    logger.debug(f"Looking for Node.js processes with pattern: {name_pattern}")
    result = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and len(cmdline) > 1:
                cmdline_str = ' '.join(cmdline)
                if ('node' in proc.info['name'].lower() or 'npm' in proc.info['name'].lower()) and name_pattern in cmdline_str:
                    logger.debug(f"Found matching Node.js process: PID {proc.info['pid']}, cmd: {cmdline_str[:100]}")
                    result.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return result

def stop_backend():
    """Stop the backend server"""
    success = False
    
    # Method 1: Try using the PID file
    pid = read_pid_file(Config.BACKEND_PID_FILE)
    if pid and is_process_running(pid):
        success = kill_process(pid, Config.FORCE_KILL, "Backend")
    
    # Method 2: Try finding the process by port
    if not success:
        pid = find_process_by_port(Config.BACKEND_PORT)
        if pid:
            success = kill_process(pid, Config.FORCE_KILL, "Backend")
    
    # Method 3: Try finding Python processes with backend pattern
    if not success:
        backend_pattern = os.path.join(Config.BACKEND_DIR, "app") 
        pids = find_python_processes(backend_pattern)
        for pid in pids:
            if kill_process(pid, Config.FORCE_KILL, f"Backend (found by pattern, PID: {pid})"):
                success = True
    
    # Clean up PID file
    if os.path.exists(Config.BACKEND_PID_FILE):
        try:
            os.remove(Config.BACKEND_PID_FILE)
            logger.info(f"Removed backend PID file: {Config.BACKEND_PID_FILE}")
        except OSError as e:
            logger.warning(f"Failed to remove backend PID file: {e}")
    
    if not success:
        log(Colors.YELLOW, "No running backend process found")
        logger.warning("No running backend process found")
    
    return success

def stop_dashboard():
    """Stop the dashboard server"""
    success = False
    
    # Method 1: Try using the PID file
    pid = read_pid_file(Config.DASHBOARD_PID_FILE)
    if pid and is_process_running(pid):
        success = kill_process(pid, Config.FORCE_KILL, "Dashboard")
    
    # Method 2: Try finding the process by port
    if not success:
        pid = find_process_by_port(Config.DASHBOARD_PORT)
        if pid:
            success = kill_process(pid, Config.FORCE_KILL, "Dashboard")
    
    # Method 3: Try finding Node.js or Python processes with dashboard pattern
    if not success:
        dashboard_pattern = os.path.join(Config.BACKEND_DIR, "app", "dashboard")
        
        # First check for Node.js processes
        pids = find_node_processes(dashboard_pattern)
        for pid in pids:
            if kill_process(pid, Config.FORCE_KILL, f"Dashboard (Node.js, PID: {pid})"):
                success = True
        
        # If no Node.js processes found, check for Python processes
        if not pids:
            pids = find_python_processes(dashboard_pattern)
            for pid in pids:
                if kill_process(pid, Config.FORCE_KILL, f"Dashboard (Python, PID: {pid})"):
                    success = True
    
    # Clean up PID file
    if os.path.exists(Config.DASHBOARD_PID_FILE):
        try:
            os.remove(Config.DASHBOARD_PID_FILE)
            logger.info(f"Removed dashboard PID file: {Config.DASHBOARD_PID_FILE}")
        except OSError as e:
            logger.warning(f"Failed to remove dashboard PID file: {e}")
    
    if not success:
        log(Colors.YELLOW, "No running dashboard process found")
        logger.warning("No running dashboard process found")
    
    return success

def main():
    """Main function"""
    logger.info(f"Starting stop script on {platform.system()} {platform.release()}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Stop the Secure Video Summarizer application")
    parser.add_argument("--backend-port", type=int, default=Config.BACKEND_PORT, 
                        help="Port for the backend server")
    parser.add_argument("--dashboard-port", type=int, default=Config.DASHBOARD_PORT, 
                        help="Port for the dashboard server")
    parser.add_argument("--force", action="store_true", 
                        help="Force kill processes without attempting graceful termination")
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug output")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backend-only", action="store_true", 
                       help="Stop only the backend server")
    group.add_argument("--dashboard-only", action="store_true", 
                       help="Stop only the dashboard server")
    
    args = parser.parse_args()
    
    # Update configuration from command line arguments
    Config.BACKEND_PORT = args.backend_port
    Config.DASHBOARD_PORT = args.dashboard_port
    Config.FORCE_KILL = args.force
    
    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled - verbose logging activated")
    
    # Print startup information
    log(Colors.BLUE, "Stopping Secure Video Summarizer application...")
    logger.info("Starting shutdown sequence")
    
    # Stop backend and/or dashboard based on arguments
    if args.backend_only:
        log(Colors.BLUE, "Stopping backend server only...")
        stop_backend()
    elif args.dashboard_only:
        log(Colors.BLUE, "Stopping dashboard server only...")
        stop_dashboard()
    else:
        log(Colors.BLUE, "Stopping all SVS components...")
        stop_backend()
        stop_dashboard()
    
    log(Colors.GREEN, "Shutdown complete!")
    logger.info("Shutdown sequence completed")

if __name__ == "__main__":
    main() 