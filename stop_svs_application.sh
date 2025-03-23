#!/bin/bash
# Complete shutdown script for the Secure Video Summarizer application
# This script shuts down both the backend server and dashboard

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default settings
FORCE_MODE=false
QUIET_MODE=false

# Function to print colored output
log() {
  if [ "$QUIET_MODE" = false ]; then
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
  fi
}

# Function to show status with dots and then result
show_status() {
  local message=$1
  local dots_count=40
  local dots_length=$((dots_count - ${#message}))
  local dots=$(printf '%*s' "$dots_length" | tr ' ' '.')
  
  echo -n "$message$dots"
}

# Function to show result of operation
show_result() {
  local success=$1
  if [ "$success" = true ]; then
    echo -e "${GREEN}Done!${NC}"
  else
    echo -e "${RED}Failed!${NC}"
  fi
}

# Function to check if we're in a virtual environment
check_in_venv() {
  if [ -n "$VIRTUAL_ENV" ]; then
    return 0  # In a venv
  else
    return 1  # Not in a venv
  fi
}

# Function to safely deactivate virtual environment
ensure_venv_deactivated() {
  show_status "Checking for active virtual environments"
  
  if check_in_venv; then
    echo -en "\r"
    show_status "Deactivating virtual environment"
    
    # Try to deactivate
    deactivate 2>/dev/null
    sleep 1
    
    # Verify deactivation
    if check_in_venv; then
      show_result false
      echo -e "${RED}Warning: Could not deactivate virtual environment automatically.${NC}"
      echo -e "${YELLOW}Please manually run 'deactivate' before continuing.${NC}"
      return 1
    else
      show_result true
    fi
  else
    show_result true
  fi
  return 0
}

# Function to check if a process is running on a given port
check_port() {
  local port=$1
  lsof -i :"$port" &>/dev/null
  return $?
}

# Function to kill processes running on a given port
kill_port_process() {
  local port=$1
  log $YELLOW "Checking for processes on port $port"
  
  if check_port "$port"; then
    if [ "$QUIET_MODE" = false ]; then
      echo -e "${RED}Found process running on port $port${NC}"
    fi
    
    if [ "$FORCE_MODE" = true ]; then
      log $RED "Force killing process on port $port"
      lsof -ti :"$port" | xargs kill -9 2>/dev/null
    else
      log $YELLOW "Gracefully stopping process on port $port"
      lsof -ti :"$port" | xargs kill 2>/dev/null
    fi
    
    # Wait for process to terminate
    local max_wait=10
    local waited=0
    while check_port "$port" && [ $waited -lt $max_wait ]; do
      sleep 1
      waited=$((waited + 1))
    done
    
    # Check if process is still running
    if check_port "$port"; then
      log $RED "Process on port $port is still running."
      log $RED "Use --force to forcefully terminate it."
      return 1
    else
      log $GREEN "Process on port $port successfully terminated."
      return 0
    fi
  else
    log $GREEN "No process found running on port $port."
    return 0
  fi
}

# Function to kill a process by PID if it exists
kill_process() {
  local pid_file=$1
  local description=$2
  local max_attempts=3
  local attempt=1
  
  show_status "Checking $description PID file"
  
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    show_result true
    
    show_status "Verifying if $description (PID: $pid) is running"
    if ps -p "$pid" > /dev/null; then
      show_result true
      show_status "Terminating $description (PID: $pid)"
      
      # Try increasingly forceful methods to kill the process
      while ps -p "$pid" > /dev/null && [ $attempt -le $max_attempts ]; do
        if [ $attempt -eq 1 ]; then
          if [ "$FORCE_MODE" = true ]; then
            # Skip gentle methods in force mode
            kill -9 "$pid" 2>/dev/null
          else
            # Start with gentle SIGTERM
            kill "$pid" 2>/dev/null
          fi
        elif [ $attempt -eq 2 ]; then
          # Use SIGKILL for the second attempt
          kill -9 "$pid" 2>/dev/null
        else
          # For the third attempt, try more aggressive methods
          if [[ "$(uname)" == "Darwin" ]]; then
            pkill -9 -P "$pid" 2>/dev/null
            kill -9 "$pid" 2>/dev/null
          else
            # Linux additional method
            pkill -9 -P "$pid" 2>/dev/null
            kill -9 "$pid" 2>/dev/null
          fi
        fi
        
        sleep 2
        attempt=$((attempt + 1))
      done
      
      if ps -p "$pid" > /dev/null; then
        show_result false
        log $RED "Failed to terminate $description (PID: $pid) after $max_attempts attempts."
        if [ "$FORCE_MODE" = true ]; then
          log $RED "Even force mode couldn't terminate the process."
        else
          log $YELLOW "Try running with --force option or manually kill with: kill -9 $pid"
        fi
      else
        show_result true
      fi
    else
      show_result false
      log $GREEN "$description with PID $pid is not running."
    fi
    
    show_status "Removing $description PID file"
    rm "$pid_file"
    show_result true
  else
    show_result false
    log $YELLOW "No PID file found for $description."
  fi
}

# Function to verify all processes are stopped
verify_all_stopped() {
  local all_stopped=true
  
  log $BOLD "Performing final verification..."
  
  # Check backend port
  show_status "Verifying backend port $BACKEND_PORT is free"
  if check_port $BACKEND_PORT; then
    show_result false
    all_stopped=false
  else
    show_result true
  fi
  
  # Check dashboard port
  show_status "Verifying dashboard port $DASHBOARD_PORT is free"
  if check_port $DASHBOARD_PORT; then
    show_result false
    all_stopped=false
  else
    show_result true
  fi
  
  # Check for any Flask processes
  show_status "Checking for residual Flask processes"
  if pgrep -f "flask run --port=$BACKEND_PORT" > /dev/null 2>&1; then
    show_result false
    all_stopped=false
  else
    show_result true
  fi
  
  # Check for any Dashboard processes
  show_status "Checking for residual dashboard processes"
  if pgrep -f "backend/run_dashboard.sh" > /dev/null 2>&1; then
    show_result false
    all_stopped=false
  else
    show_result true
  fi
  
  # Final status
  show_status "Environment cleanup status"
  if [ "$all_stopped" = true ]; then
    show_result true
  else
    show_result false
    
    if [ "$FORCE_MODE" = true ]; then
      log $RED "WARNING: Some processes could not be stopped despite using force mode."
      log $RED "You may need to manually check and kill them using these commands:"
      log $YELLOW "    ps aux | grep flask"
      log $YELLOW "    ps aux | grep python"
      log $YELLOW "    kill -9 <PID>"
    else
      log $YELLOW "Try running with --force option: ./stop_svs_application.sh --force"
    fi
  fi
}

# Function to display the help message
display_help() {
  echo ""
  log $BOLD "Usage:"
  echo "  ./stop_svs_application.sh [options]"
  echo ""
  log $BOLD "Options:"
  echo "  --help, -h       Show this help message"
  echo "  --force          Use aggressive methods to terminate processes"
  echo "  --quiet          Suppress most output messages"
  echo ""
  log $BOLD "Examples:"
  echo "  ./stop_svs_application.sh          # Normal shutdown procedure"
  echo "  ./stop_svs_application.sh --force  # Force terminate all processes"
  echo ""
}

# Function to parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        display_help
        exit 0
        ;;
      --force)
        FORCE_MODE=true
        shift
        ;;
      --quiet)
        QUIET_MODE=true
        shift
        ;;
      *)
        log $RED "Unknown option: $1"
        display_help
        exit 1
        ;;
    esac
  done
}

# Main execution function
shutdown_svs_application() {
  # Step 1: Deactivate any active virtual environment
  log $BOLD "Step 1: Cleaning up environment..."
  ensure_venv_deactivated
  echo ""

  # Step 2: Stop backend server
  log $BOLD "Step 2: Stopping backend server..."
  # Try to kill by PID first
  kill_process "$BACKEND_PID_FILE" "Backend server"
  # Then ensure the port is free
  kill_port_process $BACKEND_PORT
  echo ""

  # Step 3: Stop dashboard server
  log $BOLD "Step 3: Stopping dashboard server..."
  # Try to kill by PID first
  kill_process "$DASHBOARD_PID_FILE" "Dashboard server"
  # Then ensure the port is free
  kill_port_process $DASHBOARD_PORT
  echo ""

  # Step 4: Verify all services are stopped
  log $BOLD "Step 4: Verifying all services are stopped..."
  verify_all_stopped
  echo ""
}

# Set paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID_FILE="$PROJECT_ROOT/.backend_pid"
DASHBOARD_PID_FILE="$PROJECT_ROOT/.dashboard_pid"
BACKEND_PORT=8081
DASHBOARD_PORT=8080

# Banner
echo ""
log $BLUE "=================================================="
log $BLUE "   Secure Video Summarizer - Shutdown Script"
log $BLUE "=================================================="
echo ""

# Parse command line arguments if provided
if [ $# -gt 0 ]; then
  parse_args "$@"
fi

# If force mode is enabled, show a warning
if [ "$FORCE_MODE" = true ]; then
  log $YELLOW "Running in FORCE mode. Aggressive termination will be used."
  echo ""
fi

# Execute the shutdown procedure
shutdown_svs_application

echo ""
log $BLUE "=================================================="
log $GREEN "   Secure Video Summarizer has been shut down!"
log $BLUE "==================================================" 