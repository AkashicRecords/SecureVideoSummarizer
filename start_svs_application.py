#!/usr/bin/env python3
"""
Cross-platform startup script for the Secure Video Summarizer application.
This script handles both the backend server and dashboard initialization.
"""

# Only standard library imports at the top
import os
import sys
import platform
import subprocess
from pathlib import Path
import time
import shutil
import signal
import socket
import venv

# Define colors for different platforms
class Colors:
    """Color codes for terminal output on different platforms"""
    if platform.system() == 'Windows':
        # Windows doesn't support ANSI color codes in cmd.exe
        # Using empty strings as fallback
        GREEN = ''
        RED = ''
        CYAN = ''
        RESET = ''
    else:
        # ANSI color codes for Unix-like systems
        GREEN = '\033[92m'
        RED = '\033[91m'
        CYAN = '\033[96m'
        RESET = '\033[0m'

def log(color, msg):
    """Print colored output to terminal"""
    print(f"{color}{msg}{Colors.RESET}")

def show_status(message):
    """Display status message with dots"""
    dots_count = 40
    dots_length = max(0, dots_count - len(message))
    dots = '.' * dots_length
    print(f"{message}{dots}", end="", flush=True)

def show_result(success):
    """Show result of operation"""
    if success:
        print(f"{Colors.GREEN}Done!{Colors.RESET}")
    else:
        print(f"{Colors.RED}Failed!{Colors.RESET}")

# Check dependencies before importing anything that requires them
print("\n" + "=" * 80)
print(" SECURE VIDEO SUMMARIZER - APPLICATION STARTUP ")
print("=" * 80 + "\n")

def ensure_script_dependencies():
    """Ensure all dependencies required by this script are installed"""
    show_status("Checking script dependencies")
    
    # Create a temporary venv for script dependencies if needed
    script_venv = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.script_venv')
    if not os.path.exists(script_venv):
        try:
            venv.create(script_venv, with_pip=True)
            
            # Get venv Python path
            if platform.system() == 'Windows':
                venv_python = os.path.join(script_venv, 'Scripts', 'python.exe')
                venv_pip = os.path.join(script_venv, 'Scripts', 'pip.exe')
            else:
                venv_python = os.path.join(script_venv, 'bin', 'python')
                venv_pip = os.path.join(script_venv, 'bin', 'pip')
            
            # Install required packages
            subprocess.run([venv_pip, 'install', 'requests', 'psutil'], check=True)
            
            # Restart script with venv Python
            os.execl(venv_python, venv_python, *sys.argv)
        except Exception as e:
            show_result(False)
            log(Colors.RED, f"Failed to set up script dependencies: {e}")
            return False
    
    # Try importing required packages
    try:
        # We don't import at top level anymore, just verify we can import
        __import__('requests')
        __import__('psutil')
        show_result(True)
        return True
    except ImportError as e:
        show_result(False)
        log(Colors.RED, f"Missing dependency: {e}")
        return False

if not ensure_script_dependencies():
    sys.exit(1)

# Remove the second set of imports since we already have them at the top
# The only new ones we need are requests and psutil which are now imported in ensure_script_dependencies

def check_dependencies():
    """Check for required dependencies and install if needed"""
    show_status("Checking for required dependencies")
    return True  # We already checked in ensure_script_dependencies

def check_in_venv():
    """Check if running in a Python virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def ensure_venv_deactivated():
    """Ensure virtual environment is deactivated"""
    show_status("Checking for active virtual environments")
    
    if check_in_venv():
        print("\r", end="")
        show_status("Warning: Running in a virtual environment")
        show_result(False)
        print(f"{Colors.CYAN}This script should be run outside of virtual environments.{Colors.RESET}")
        print(f"{Colors.CYAN}Please run 'deactivate' and try again.{Colors.RESET}")
        return False
    else:
        show_result(True)
        return True

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_os_commands():
    """Get OS-specific command mappings"""
    if platform.system() == 'Windows':
        return {
            'find_process': ['netstat', '-ano', '|', 'findstr'],
            'kill_process': ['taskkill', '/F', '/PID'],
            'list_processes': ['tasklist'],
            'python_cmd': 'python',
            'npm_cmd': 'npm.cmd'
        }
    else:
        return {
            'find_process': ['lsof', '-ti'],
            'kill_process': ['kill', '-9'],
            'list_processes': ['ps', '-ef'],
            'python_cmd': 'python3',
            'npm_cmd': 'npm'
        }

def kill_process_on_port(port):
    """Kill process on port using OS-specific commands"""
    show_status(f"Checking for processes on port {port}")
    
    if is_port_in_use(port):
        show_result(False)
        show_status(f"Attempting to terminate process on port {port}")
        
        os_commands = get_os_commands()
        try:
            # Find process using port
            if platform.system() == 'Windows':
                cmd = f"netstat -ano | findstr :{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    pid = result.stdout.split()[-1]
                    # Kill the process
                    subprocess.run([os_commands['kill_process'][0], os_commands['kill_process'][1], pid], 
                                 check=True, capture_output=True)
            else:
                cmd = f"lsof -ti:{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    pid = result.stdout.strip()
                    # Kill the process
                    subprocess.run([os_commands['kill_process'][0], os_commands['kill_process'][1], pid], 
                                 check=True, capture_output=True)
            
            time.sleep(2)
            success = not is_port_in_use(port)
            show_result(success)
            return success
        except subprocess.SubprocessError as e:
            show_result(False)
            log(Colors.RED, f"Failed to kill process: {e}")
            return False
    else:
        show_result(True)
        return True

def find_npm():
    """Find npm executable using OS-specific commands"""
    os_commands = get_os_commands()
    
    if platform.system() == 'Windows':
        try:
            # Try where command on Windows
            result = subprocess.run(['where', os_commands['npm_cmd']], 
                                 capture_output=True, text=True)
            if result.stdout:
                return result.stdout.splitlines()[0]
        except subprocess.SubprocessError:
            pass
    else:
        try:
            # Try which command on Unix
            result = subprocess.run(['which', os_commands['npm_cmd']], 
                                 capture_output=True, text=True)
            if result.stdout:
                return result.stdout.strip()
        except subprocess.SubprocessError:
            pass
    
    return os_commands['npm_cmd']  # Fallback to default command

def get_system_python():
    """Get system Python path using OS-specific commands"""
    os_commands = get_os_commands()
    
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(['where', os_commands['python_cmd']], 
                                 capture_output=True, text=True)
            if result.stdout:
                return result.stdout.splitlines()[0]
        else:
            result = subprocess.run(['which', os_commands['python_cmd']], 
                                 capture_output=True, text=True)
            if result.stdout:
                return result.stdout.strip()
    except subprocess.SubprocessError:
        pass
    
    return sys.executable  # Fallback to current Python

def verify_ports_clear(backend_port, dashboard_port):
    """Verify all required ports are clear before proceeding"""
    max_retries = 3
    retry_count = 0
    all_clear = False
    
    show_status("Verifying all ports are clear")
    
    # Try to import psutil for better process management
    try:
        import psutil
        
        def kill_process_on_port(port):
            """Kill process running on a given port using psutil"""
            show_status(f"Checking for processes on port {port}")
            
            if is_port_in_use(port):
                show_result(False)
                show_status(f"Terminating process on port {port}")
                
                # Find and kill the process using the port
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.connections(kind='inet'):
                            if hasattr(conn, 'laddr') and conn.laddr.port == port:
                                try:
                                    proc.kill()
                                    time.sleep(2)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
                
                # Verify termination
                if is_port_in_use(port):
                    show_result(False)
                    log(Colors.RED, f"Failed to terminate process on port {port}.")
                    return False
                else:
                    show_result(True)
                    return True
            else:
                show_result(True)
                return True
    except ImportError:
        # Fall back to simpler method if psutil is not available
        kill_process_on_port = simple_kill_process_on_port
    
    while retry_count < max_retries and not all_clear:
        if is_port_in_use(backend_port):
            show_result(False)
            show_status(f"Force closing port {backend_port} (attempt {retry_count+1}/{max_retries})")
            kill_process_on_port(backend_port)
            time.sleep(2)
        elif is_port_in_use(dashboard_port):
            show_result(False)
            show_status(f"Force closing port {dashboard_port} (attempt {retry_count+1}/{max_retries})")
            kill_process_on_port(dashboard_port)
            time.sleep(2)
        else:
            all_clear = True
            show_result(True)
            break
        
        retry_count += 1
        if retry_count == max_retries and (is_port_in_use(backend_port) or is_port_in_use(dashboard_port)):
            log(Colors.RED, f"CRITICAL ERROR: Could not clear ports after {max_retries} attempts.")
            log(Colors.RED, f"Please manually check and kill processes on ports {backend_port} and {dashboard_port}.")
            return False
    
    # Final verification that all ports are clear
    if all_clear:
        show_status("Confirming all ports are clear for startup")
        show_result(True)
        return True
    return False

def simple_check_pid(pid):
    """Simple cross-platform way to check if a process is running without psutil"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(f"tasklist /FI \"PID eq {pid}\"", 
                          shell=True, check=True, capture_output=True)
            return True
        else:
            os.kill(pid, 0)  # Signal 0 is used to check if process exists
            return True
    except (subprocess.SubprocessError, OSError, ValueError):
        return False

def verify_clean_environment(project_root, backend_port, dashboard_port):
    """Verify all processes have been terminated"""
    clean_env = True
    
    # Import psutil here where needed
    try:
        import psutil
        is_process_running = psutil.pid_exists
    except ImportError:
        is_process_running = simple_check_pid
    
    # Check for backend PID file and process
    show_status("Verifying backend process is not running")
    backend_pid_file = os.path.join(project_root, ".backend_pid")
    if os.path.exists(backend_pid_file):
        try:
            with open(backend_pid_file, 'r') as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                show_result(False)
                # Try to kill the process
                kill_process(pid)
                clean_env = not is_process_running(pid)
            else:
                show_result(True)
                os.remove(backend_pid_file)
        except:
            show_result(True)
            try:
                os.remove(backend_pid_file)
            except:
                pass
    else:
        show_result(True)
    
    # Check for dashboard PID file and process
    show_status("Verifying dashboard process is not running")
    dashboard_pid_file = os.path.join(project_root, ".dashboard_pid")
    if os.path.exists(dashboard_pid_file):
        try:
            with open(dashboard_pid_file, 'r') as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                show_result(False)
                # Try to kill the process
                kill_process(pid)
                clean_env = not is_process_running(pid)
            else:
                show_result(True)
                os.remove(dashboard_pid_file)
        except:
            show_result(True)
            try:
                os.remove(dashboard_pid_file)
            except:
                pass
    else:
        show_result(True)
    
    # Check ports are clear
    if not verify_ports_clear(backend_port, dashboard_port):
        clean_env = False
    
    # Final clean environment status
    if clean_env:
        show_status("Environment is clean and ready for startup")
        show_result(True)
    else:
        show_status("WARNING: Environment may not be completely clean")
        show_result(False)
        
        # Force clean by directly killing processes
        show_status("Attempting to force clean environment")
        if is_port_in_use(backend_port):
            pid = find_process_by_port(backend_port)
            if pid:
                kill_process(pid)
        if is_port_in_use(dashboard_port):
            pid = find_process_by_port(dashboard_port)
            if pid:
                kill_process(pid)
        
        time.sleep(3)
        
        # Recheck
        if is_port_in_use(backend_port) or is_port_in_use(dashboard_port):
            show_result(False)
            log(Colors.RED, "Could not fully clean environment. Try manually shutting down all processes.")
            return False
        else:
            show_result(True)
            return True
    
    return True

def create_venv(venv_dir, name):
    """Create a Python virtual environment"""
    show_status(f"Checking for {name} virtual environment")
    
    if not os.path.exists(venv_dir):
        show_result(False)
        show_status(f"Creating {name} virtual environment")
        try:
            subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True, capture_output=True)
            show_result(True)
        except subprocess.SubprocessError:
            show_result(False)
            log(Colors.RED, f"Failed to create {name} virtual environment.")
            return False
    else:
        show_result(True)
    
    return True

def configure_default_settings():
    """Set default configuration"""
    # Default configuration
    config = {
        'PROJECT_ROOT': os.path.dirname(os.path.abspath(__file__)),
        'BACKEND_PORT': 8081,
        'DASHBOARD_PORT': 8080,
        'BACKEND_VENV': os.path.join('backend', 'venv'),
        'DEBUG_MODE': False,
        'CONFIG_MODE': 'development'  # Default to development mode
    }
    
    return config

def deactivate_venv():
    """Attempt to deactivate virtual environment using multiple methods"""
    show_status("Deactivating virtual environment")
    
    if not os.environ.get('VIRTUAL_ENV'):
        show_result(True)
        return True
        
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Method 1: Modify environment variables
            if 'VIRTUAL_ENV' in os.environ:
                del os.environ['VIRTUAL_ENV']
            if '_OLD_VIRTUAL_PATH' in os.environ:
                os.environ['PATH'] = os.environ['_OLD_VIRTUAL_PATH']
                del os.environ['_OLD_VIRTUAL_PATH']
            if '_OLD_VIRTUAL_PYTHONHOME' in os.environ:
                os.environ['PYTHONHOME'] = os.environ['_OLD_VIRTUAL_PYTHONHOME']
                del os.environ['_OLD_VIRTUAL_PYTHONHOME']
                
            # Method 2: Reset Python path
            if hasattr(sys, 'real_prefix'):
                sys.prefix = sys.real_prefix
            elif hasattr(sys, 'base_prefix'):
                sys.prefix = sys.base_prefix
                
            # Method 3: Clean PATH
            paths = os.environ['PATH'].split(os.pathsep)
            clean_paths = [p for p in paths if not any(venv_marker in p.lower() 
                         for venv_marker in ['venv', 'virtualenv', '.env'])]
            os.environ['PATH'] = os.pathsep.join(clean_paths)
            
            # Verify deactivation
            if not os.environ.get('VIRTUAL_ENV'):
                show_result(True)
                return True
                
        except Exception as e:
            if attempt == max_attempts - 1:
                show_result(False)
                log(Colors.RED, f"Failed to deactivate virtual environment: {e}")
                return False
            time.sleep(1)  # Wait before retry
            
    # If all methods fail, try to restart the script outside venv
    show_status("Attempting to restart script outside virtual environment")
    try:
        # Get system Python path without shell commands
        python_cmd = get_system_python()
            
        # Remove venv from PYTHONPATH if present
        if 'PYTHONPATH' in os.environ:
            paths = os.environ['PYTHONPATH'].split(os.pathsep)
            clean_paths = [p for p in paths if not any(venv_marker in p.lower() 
                         for venv_marker in ['venv', 'virtualenv', '.env'])]
            if clean_paths:
                os.environ['PYTHONPATH'] = os.pathsep.join(clean_paths)
            else:
                del os.environ['PYTHONPATH']
            
        # Restart script with system Python
        os.execl(python_cmd, python_cmd, *sys.argv)
    except Exception as e:
        show_result(False)
        log(Colors.RED, f"Failed to restart script: {e}")
        return False
        
    return False

def verify_startup_environment():
    """Verify the environment is clean before starting"""
    show_status("Verifying clean environment")
    
    # Use existing verify_clean_environment function with default config
    config = configure_default_settings()
    if not verify_clean_environment(config['PROJECT_ROOT'], config['BACKEND_PORT'], config['DASHBOARD_PORT']):
        return False
    
    # Handle active virtual environment
    if os.environ.get('VIRTUAL_ENV'):
        if not deactivate_venv():
            return False
    
    # Remove existing backend venv if present
    backend_venv = os.path.join(config['PROJECT_ROOT'], 'backend', 'venv')
    if os.path.exists(backend_venv):
        show_status("Removing existing virtual environment")
        try:
            shutil.rmtree(backend_venv)
            show_result(True)
        except Exception as e:
            show_result(False)
            log(Colors.RED, f"Failed to remove existing virtual environment: {e}")
            return False
    
    show_result(True)
    return True

def verify_shutdown():
    """Verify all processes are stopped and environment is clean"""
    show_status("Verifying shutdown")
    
    # Use existing verify_clean_environment function with default config
    config = configure_default_settings()
    if not verify_clean_environment(config['PROJECT_ROOT'], config['BACKEND_PORT'], config['DASHBOARD_PORT']):
        return False
    
    show_result(True)
    return True

def verify_venv(venv_path):
    """Verify virtual environment is properly created and accessible"""
    show_status("Verifying virtual environment")
    
    # Check if venv directory exists
    if not os.path.exists(venv_path):
        show_result(False)
        log(Colors.RED, f"Virtual environment not found at {venv_path}")
        return False
    
    # Check for pip executable
    pip_cmd = os.path.join(venv_path, 'bin', 'pip') if platform.system() != 'Windows' else os.path.join(venv_path, 'Scripts', 'pip.exe')
    if not os.path.exists(pip_cmd):
        show_result(False)
        log(Colors.RED, "pip not found in virtual environment")
        return False
    
    # Try to run pip to verify it works
    try:
        subprocess.run([pip_cmd, '--version'], check=True, capture_output=True)
        show_result(True)
        return True
    except subprocess.SubprocessError:
        show_result(False)
        log(Colors.RED, "Failed to verify pip in virtual environment")
        return False

def setup_venv(venv_path):
    """Set up virtual environment with required dependencies"""
    show_status("Setting up virtual environment")
    
    # Create venv if it doesn't exist
    if not os.path.exists(venv_path):
        log(Colors.CYAN, f"Creating virtual environment at {venv_path}")
        if not create_venv(venv_path, "backend"):
            return False
    
    # Verify venv
    if not verify_venv(venv_path):
        return False
    
    # Install psutil first
    pip_cmd = os.path.join(venv_path, 'bin', 'pip') if platform.system() != 'Windows' else os.path.join(venv_path, 'Scripts', 'pip.exe')
    log(Colors.CYAN, "Installing psutil...")
    try:
        result = subprocess.run([pip_cmd, 'install', 'psutil'], 
                              check=True, capture_output=True, text=True)
        log(Colors.GREEN, "psutil installed successfully")
    except subprocess.SubprocessError as e:
        log(Colors.RED, f"Failed to install psutil: {e}")
        log(Colors.RED, f"Error output: {e.stderr}")
        return False
    
    # Install other dependencies
    log(Colors.CYAN, "Installing project dependencies...")
    try:
        result = subprocess.run([pip_cmd, 'install', '-r', os.path.join(os.path.dirname(venv_path), 'requirements.txt')], 
                              check=True, capture_output=True, text=True)
        log(Colors.GREEN, "Dependencies installed successfully")
        show_result(True)
        return True
    except subprocess.SubprocessError as e:
        show_result(False)
        log(Colors.RED, f"Failed to install dependencies: {e}")
        log(Colors.RED, f"Error output: {e.stderr}")
        return False

def start_backend_server(venv_path, config):
    """Start the backend server"""
    show_status("Starting backend server")
    
    python_cmd = os.path.join(venv_path, 'bin', 'python') if platform.system() != 'Windows' else os.path.join(venv_path, 'Scripts', 'python.exe')
    backend_script = os.path.join(config['PROJECT_ROOT'], 'backend', 'run_backend.py')
    
    if not os.path.exists(backend_script):
        log(Colors.RED, f"Backend script not found at {backend_script}")
        return False
    
    try:
        backend_process = subprocess.Popen(
            [python_cmd, backend_script, '--config', config['CONFIG_MODE']],
            cwd=os.path.join(config['PROJECT_ROOT'], 'backend'),
            stdout=subprocess.PIPE if config['DEBUG_MODE'] else None,
            stderr=subprocess.PIPE if config['DEBUG_MODE'] else None,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Save backend PID
        with open(os.path.join(config['PROJECT_ROOT'], '.backend_pid'), 'w') as f:
            f.write(str(backend_process.pid))
        
        # Only monitor output in debug mode
        if config['DEBUG_MODE']:
            def read_output(pipe, is_error=False):
                for line in pipe:
                    if is_error:
                        log(Colors.RED, line.strip())
                    else:
                        log(Colors.CYAN, line.strip())
            
            # Start output monitoring threads
            import threading
            stdout_thread = threading.Thread(target=read_output, args=(backend_process.stdout, False))
            stderr_thread = threading.Thread(target=read_output, args=(backend_process.stderr, True))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
        
        # Check if process started successfully
        time.sleep(2)  # Give it a moment to start
        if backend_process.poll() is not None:
            # Process died immediately
            if config['DEBUG_MODE']:
                stderr = backend_process.stderr.read() if backend_process.stderr else "No error output available"
                log(Colors.RED, f"Backend server failed to start: {stderr}")
            else:
                log(Colors.RED, "Backend server failed to start")
            return False
        
        show_result(True)
        return True
    except Exception as e:
        show_result(False)
        log(Colors.RED, f"Failed to start backend server: {e}")
        return False

def start_frontend_server(config):
    """Start the frontend development server"""
    show_status("Starting frontend server")
    
    frontend_dir = os.path.join(config['PROJECT_ROOT'], 'frontend')
    if not os.path.exists(frontend_dir):
        log(Colors.RED, f"Frontend directory not found at {frontend_dir}")
        return False
    
    npm_cmd = find_npm()
    
    try:
        # Install dependencies
        subprocess.run([npm_cmd, 'install'], 
                      cwd=frontend_dir,
                      check=True, 
                      capture_output=True, 
                      text=True)
    except subprocess.SubprocessError as e:
        log(Colors.RED, f"Failed to install frontend dependencies: {e}")
        log(Colors.RED, f"Error output: {e.stderr}")
        return False
    
    try:
        # Start the development server
        frontend_process = subprocess.Popen(
            [npm_cmd, 'start'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE if config['DEBUG_MODE'] else None,
            stderr=subprocess.PIPE if config['DEBUG_MODE'] else None,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Save frontend PID
        with open(os.path.join(config['PROJECT_ROOT'], '.frontend_pid'), 'w') as f:
            f.write(str(frontend_process.pid))
        
        # Check if process started successfully
        time.sleep(2)  # Give it a moment to start
        if frontend_process.poll() is not None:
            # Process died immediately
            stderr = frontend_process.stderr.read() if frontend_process.stderr else "No error output available"
            log(Colors.RED, f"Frontend server failed to start: {stderr}")
            return False
        
        show_result(True)
        return True
    except Exception as e:
        show_result(False)
        log(Colors.RED, f"Failed to start frontend server: {e}")
        return False

def check_backend_health(port):
    """Check if backend server is healthy and responding"""
    try:
        import requests  # Import here where needed
        response = requests.get(f"http://localhost:{port}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        log(Colors.RED, f"Backend health check failed: {e}")
        return False

def check_frontend_health(port):
    """Check if frontend server is healthy and responding"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        log(Colors.RED, f"Frontend health check failed: {e}")
        return False

def check_extension_health(port):
    """Check if extension server is healthy and responding"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        log(Colors.RED, f"Extension health check failed: {e}")
        return False

def verify_servers_running(config):
    """Verify all servers are running and healthy"""
    show_status("Verifying servers are running")
    
    # Wait a bit for servers to start
    time.sleep(5)
    
    # Check backend
    if not check_backend_health(config['BACKEND_PORT']):
        return False
    
    # Check frontend
    if not check_frontend_health(config['DASHBOARD_PORT']):
        return False
    
    # Check extension if it's enabled
    if config.get('ENABLE_EXTENSION', False) and not check_extension_health(config['EXTENSION_PORT']):
        return False
    
    show_result(True)
    return True

def main():
    """Main entry point for the application"""
    # Check dependencies first
    if not ensure_script_dependencies():
        log(Colors.RED, "Required dependencies are not available")
        return 1

    # Get configuration
    config = configure_default_settings()
    
    # Verify clean environment before starting
    if not verify_startup_environment():
        log(Colors.RED, "Cannot start: Environment is not clean")
        return 1
    
    # Set up backend virtual environment
    backend_venv_path = os.path.join(config['PROJECT_ROOT'], 'backend', 'venv')
    if not setup_venv(backend_venv_path):
        sys.exit(1)
    
    # Start backend server
    if not start_backend_server(backend_venv_path, config):
        sys.exit(1)
    
    # Start frontend server
    if not start_frontend_server(config):
        sys.exit(1)
    
    # Verify servers are running and healthy
    if not verify_servers_running(config):
        log(Colors.RED, "Health checks failed. Please check the logs for details.")
        sys.exit(1)
    
    log(Colors.GREEN, "Application started successfully!")
    log(Colors.GREEN, f"Backend running on http://localhost:{config['BACKEND_PORT']}")
    log(Colors.GREEN, f"Frontend running on http://localhost:{config['DASHBOARD_PORT']}")
    return 0

def shutdown():
    """Shutdown the application"""
    show_status("Shutting down application")
    
    # Stop processes
    stop_processes()
    
    # Verify shutdown
    if not verify_shutdown():
        log(Colors.RED, "Shutdown verification failed")
        return 1
    
    show_result(True)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 