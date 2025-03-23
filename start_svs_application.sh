#!/bin/bash
# Complete startup script for the Secure Video Summarizer application
# This script handles both the backend server and dashboard

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print colored output
log() {
  local color=$1
  local msg=$2
  echo -e "${color}${msg}${NC}"
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
      exit 1
    else
      show_result true
    fi
  else
    show_result true
  fi
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
  show_status "Checking for processes on port $port"
  
  if check_port "$port"; then
    show_result false
    show_status "Terminating process on port $port"
    
    # Kill the process using the port
    lsof -ti :"$port" | xargs kill -9 2>/dev/null
    sleep 2
    
    # Verify termination
    if check_port "$port"; then
      show_result false
      log $RED "Failed to terminate process on port $port."
      return 1
    else
      show_result true
      return 0
    fi
  else
    show_result true
    return 0
  fi
}

# Function to verify ports are clear before proceeding
verify_ports_clear() {
  local max_retries=3
  local retry_count=0
  local all_clear=false
  
  show_status "Verifying all ports are clear"
  
  while [ $retry_count -lt $max_retries ] && [ "$all_clear" = false ]; do
    if check_port $BACKEND_PORT; then
      show_result false
      show_status "Force closing port $BACKEND_PORT (attempt $((retry_count+1))/$max_retries)"
      kill_port_process $BACKEND_PORT
      sleep 2
    elif check_port $DASHBOARD_PORT; then
      show_result false
      show_status "Force closing port $DASHBOARD_PORT (attempt $((retry_count+1))/$max_retries)"
      kill_port_process $DASHBOARD_PORT
      sleep 2
    else
      all_clear=true
      show_result true
      break
    fi
    
    retry_count=$((retry_count + 1))
    if [ $retry_count -eq $max_retries ] && (check_port $BACKEND_PORT || check_port $DASHBOARD_PORT); then
      log $RED "CRITICAL ERROR: Could not clear ports after $max_retries attempts."
      log $RED "Please manually check and kill processes on ports $BACKEND_PORT and $DASHBOARD_PORT."
      log $RED "You can use: lsof -i :$BACKEND_PORT -i :$DASHBOARD_PORT"
      log $RED "And kill processes with: kill -9 <PID>"
      exit 1
    fi
  done
  
  # Final verification that all ports are clear
  if [ "$all_clear" = true ]; then
    show_status "Confirming all ports are clear for startup"
    show_result true
  fi
}

# Function to verify all processes have been terminated
verify_clean_environment() {
  local clean_env=true
  
  # Check for backend PID file and process
  show_status "Verifying backend process is not running"
  if [ -f "$PROJECT_ROOT/.backend_pid" ]; then
    local pid=$(cat "$PROJECT_ROOT/.backend_pid")
    if ps -p "$pid" > /dev/null 2>&1; then
      show_result false
      clean_env=false
    else
      show_result true
    fi
  else
    show_result true
  fi
  
  # Check for dashboard PID file and process
  show_status "Verifying dashboard process is not running"
  if [ -f "$PROJECT_ROOT/.dashboard_pid" ]; then
    local pid=$(cat "$PROJECT_ROOT/.dashboard_pid")
    if ps -p "$pid" > /dev/null 2>&1; then
      show_result false
      clean_env=false
    else
      show_result true
    fi
  else
    show_result true
  fi
  
  # Check for any Python processes that might be related to our app
  show_status "Checking for residual Flask processes"
  if pgrep -f "flask run --port=$BACKEND_PORT" > /dev/null 2>&1; then
    show_result false
    clean_env=false
  else
    show_result true
  fi
  
  show_status "Checking for residual dashboard processes"
  if pgrep -f "backend/run_dashboard.sh" > /dev/null 2>&1; then
    show_result false
    clean_env=false
  else
    show_result true
  fi
  
  # Final clean environment status
  if [ "$clean_env" = true ]; then
    show_status "Environment is clean and ready for startup"
    show_result true
  else
    show_status "WARNING: Environment may not be completely clean"
    show_result false
    
    # Attempt to force clean
    show_status "Attempting to force clean environment"
    "$PROJECT_ROOT/stop_svs_application.sh" --force
    sleep 3
    
    # Recheck
    if check_port $BACKEND_PORT || check_port $DASHBOARD_PORT; then
      show_result false
      log $RED "Could not fully clean environment. Try manually shutting down all processes."
      exit 1
    else
      show_result true
    fi
  fi
}

# Function to create a Python virtual environment
create_venv() {
  local venv_dir=$1
  local name=$2
  
  show_status "Checking for $name virtual environment"
  
  if [ ! -d "$venv_dir" ]; then
    show_result false
    show_status "Creating $name virtual environment"
    python3 -m venv "$venv_dir"
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Failed to create $name virtual environment."
      return 1
    fi
    show_result true
  else
    show_result true
  fi
  return 0
}

# Set default configuration
configure_default_settings() {
  # Set paths
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  BACKEND_DIR="$PROJECT_ROOT/backend"
  BACKEND_VENV="$BACKEND_DIR/venv"
  DASHBOARD_VENV="$BACKEND_DIR/dashboard_venv"
  BACKEND_PORT=8081
  DASHBOARD_PORT=8080
  
  # Default startup options
  INSTALL_DEPENDENCIES=true
  FORCE_UPDATE_DEPS=false
  OFFLINE_INSTALL=false
  RUN_BACKEND=true
  RUN_DASHBOARD=true
  RUN_TESTS=false
  DEBUG_MODE=false
  LAST_RUN_MODE="standard"  # Default mode
  
  # Default repository settings for updates
  SVS_REPO_URL="https://raw.githubusercontent.com/secure-video-summarizer/SVS"
  SVS_BRANCH="main"
  SVS_REQ_PATH="backend/requirements.lock"
}

# Function to display the welcome banner
display_welcome_banner() {
  echo ""
  log $BLUE "=================================================="
  log $BLUE "    Secure Video Summarizer - Startup Script"
  log $BLUE "=================================================="
  echo ""
}

# Function to display the help message
display_help() {
  echo ""
  log $BOLD "Usage:"
  echo "  ./start_svs_application.sh [options]"
  echo ""
  log $BOLD "Options:"
  echo "  --help, -h                   Show this help message"
  echo "  --skip-deps                  Skip dependency installation"
  echo "  --force-update-deps          Force update dependencies"
  echo "  --backend-only               Start only the backend server"
  echo "  --dashboard-only             Start only the dashboard server"
  echo "  --test                       Run all tests and exit"
  echo "  --backend-port PORT          Set backend port (default: 8081)"
  echo "  --dashboard-port PORT        Set dashboard port (default: 8080)"
  echo "  --debug                      Run in debug mode"
  echo ""
  log $BOLD "Examples:"
  echo "  ./start_svs_application.sh                     # Start everything with defaults"
  echo "  ./start_svs_application.sh --backend-only      # Start only the backend server"
  echo "  ./start_svs_application.sh --force-update-deps # Force update all dependencies"
  echo "  ./start_svs_application.sh --test              # Run all tests and exit"
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
      --skip-deps)
        INSTALL_DEPENDENCIES=false
        shift
        ;;
      --force-update-deps)
        FORCE_UPDATE_DEPS=true
        shift
        ;;
      --backend-only)
        RUN_BACKEND=true
        RUN_DASHBOARD=false
        shift
        ;;
      --dashboard-only)
        RUN_BACKEND=false
        RUN_DASHBOARD=true
        shift
        ;;
      --test)
        RUN_TESTS=true
        RUN_BACKEND=false
        RUN_DASHBOARD=false
        shift
        ;;
      --backend-port)
        if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
          BACKEND_PORT="$2"
          shift 2
        else
          log $RED "Error: --backend-port requires a numeric port number"
          display_help
          exit 1
        fi
        ;;
      --dashboard-port)
        if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
          DASHBOARD_PORT="$2"
          shift 2
        else
          log $RED "Error: --dashboard-port requires a numeric port number"
          display_help
          exit 1
        fi
        ;;
      --debug)
        DEBUG_MODE=true
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

# Function to save last successful startup configuration
save_startup_config() {
  local config_file="$PROJECT_ROOT/.svs_last_config"
  
  # Create config file with current settings
  cat > "$config_file" << EOL
LAST_RUN_MODE="$LAST_RUN_MODE"
INSTALL_DEPENDENCIES=$INSTALL_DEPENDENCIES
FORCE_UPDATE_DEPS=$FORCE_UPDATE_DEPS
RUN_BACKEND=$RUN_BACKEND
RUN_DASHBOARD=$RUN_DASHBOARD
DEBUG_MODE=$DEBUG_MODE
BACKEND_PORT=$BACKEND_PORT
DASHBOARD_PORT=$DASHBOARD_PORT
EOL
  
  log $GREEN "Startup configuration saved for future use."
}

# Function to load last successful startup configuration
load_startup_config() {
  local config_file="$PROJECT_ROOT/.svs_last_config"
  
  if [ -f "$config_file" ]; then
    # Source the config file to load variables
    source "$config_file"
    return 0
  else
    return 1
  fi
}

# Function to display countdown timer
display_countdown() {
  local seconds=$1
  local message=$2
  
  echo ""
  log $CYAN "$message"
  
  for (( i=$seconds; i>0; i-- )); do
    echo -ne "\r${YELLOW}Continuing in $i seconds... Press Ctrl+C to cancel${NC}"
    sleep 1
  done
  echo -e "\r${GREEN}Continuing with startup...${NC}                           "
  echo ""
}

# Function to display the interactive menu
display_interactive_menu() {
  local has_previous_config=false
  local previous_mode_desc=""
  
  # Try to load previous configuration
  if load_startup_config; then
    has_previous_config=true
    
    # Create a description of the previous mode
    case "$LAST_RUN_MODE" in
      "standard")
        previous_mode_desc="Standard startup (backend + dashboard)"
        ;;
      "backend")
        previous_mode_desc="Backend server only"
        ;;
      "dashboard")
        previous_mode_desc="Dashboard server only"
        ;;
      "cold_start")
        previous_mode_desc="Cold start (clean install with dependencies)"
        ;;
      "development")
        previous_mode_desc="Development mode (with debug options)"
        ;;
      "test")
        previous_mode_desc="Run tests"
        ;;
      "custom")
        previous_mode_desc="Custom configuration"
        ;;
      *)
        previous_mode_desc="Standard startup (backend + dashboard)"
        LAST_RUN_MODE="standard"
        ;;
    esac
  fi
  
  echo ""
  log $CYAN "======= SVS STARTUP OPTIONS ======="
  echo ""
  
  # Only show auto-continue option if we have a previous configuration
  if [ "$has_previous_config" = true ]; then
    log $BOLD "Last successful startup mode: $previous_mode_desc"
    echo ""
    log $BOLD "Using last successful configuration in 5 seconds..."
    log $BOLD "Press any key to show the menu or Ctrl+C to cancel"
    
    # Wait for 5 seconds or until a key is pressed
    if read -t 5 -n 1; then
      # Key was pressed, show menu
      echo ""
    else
      # No key was pressed, use last configuration
      echo ""
      log $GREEN "Continuing with previous startup mode: $previous_mode_desc"
      return
    fi
  fi
  
  log $BOLD "Please select a startup mode:"
  echo "  1) Standard startup (backend + dashboard)"
  echo "  2) Backend server only"
  echo "  3) Dashboard server only"
  echo "  4) Cold start (clean install with dependencies)"
  echo "  5) Offline installation (using packaged dependencies)"
  echo "  6) Development mode (with debug options)"
  echo "  7) Run tests"
  echo "  8) Custom configuration"
  echo "  9) Exit"
  echo ""
  read -p "Enter your choice [1-9]: " menu_choice
  
  case $menu_choice in
    1)
      log $GREEN "Starting in standard mode (backend + dashboard)..."
      LAST_RUN_MODE="standard"
      ;;
    2)
      log $GREEN "Starting backend server only..."
      RUN_BACKEND=true
      RUN_DASHBOARD=false
      LAST_RUN_MODE="backend"
      ;;
    3)
      log $GREEN "Starting dashboard server only..."
      RUN_BACKEND=false
      RUN_DASHBOARD=true
      LAST_RUN_MODE="dashboard"
      ;;
    4)
      log $GREEN "Performing cold start (clean install with dependencies)..."
      
      # First check for updates
      log $YELLOW "Checking for application updates (internet connection required)..."
      
      # Run the update check
      check_for_updates
      update_result=$?
      
      # Only prompt to continue if updates were checked properly
      if [ $update_result -eq 0 ]; then
        # Prompt user to continue with cold start
        echo ""
        log $YELLOW "Continue with cold start? (y/n) [y]"
        read -p "" continue_choice
        continue_choice=${continue_choice:-y}
        
        if [[ $continue_choice =~ ^[Nn]$ ]]; then
          log $YELLOW "Cold start canceled. Returning to menu..."
          display_interactive_menu
          return
        fi
      fi
      
      # Proceed with cold start
      INSTALL_DEPENDENCIES=true
      FORCE_UPDATE_DEPS=true
      LAST_RUN_MODE="cold_start"
      ;;
    5)
      log $GREEN "Performing offline installation using packaged dependencies..."
      INSTALL_DEPENDENCIES=true
      OFFLINE_INSTALL=true
      LAST_RUN_MODE="offline_install"
      ;;
    6)
      log $GREEN "Starting in development mode with debug options..."
      DEBUG_MODE=true
      LAST_RUN_MODE="development"
      ;;
    7)
      log $GREEN "Running tests..."
      RUN_TESTS=true
      RUN_BACKEND=false
      RUN_DASHBOARD=false
      LAST_RUN_MODE="test"
      ;;
    8)
      configure_custom_settings
      LAST_RUN_MODE="custom"
      ;;
    9)
      log $YELLOW "Exiting..."
      exit 0
      ;;
    *)
      if [ "$has_previous_config" = true ]; then
        log $YELLOW "Invalid choice. Using previous startup mode: $previous_mode_desc"
      else
        log $YELLOW "Invalid choice. Using standard startup..."
        LAST_RUN_MODE="standard"
      fi
      ;;
  esac
}

# Function to configure custom settings
configure_custom_settings() {
  echo ""
  log $CYAN "======= CUSTOM CONFIGURATION ======="
  
  echo ""
  log $BOLD "Backend Server:"
  read -p "Start backend server? (y/n) [y]: " backend_choice
  backend_choice=${backend_choice:-y}
  if [[ $backend_choice =~ ^[Nn]$ ]]; then
    RUN_BACKEND=false
  else
    RUN_BACKEND=true
    read -p "Custom backend port? (leave empty for default $BACKEND_PORT): " custom_backend_port
    if [[ -n "$custom_backend_port" && "$custom_backend_port" =~ ^[0-9]+$ ]]; then
      BACKEND_PORT=$custom_backend_port
    fi
  fi
  
  echo ""
  log $BOLD "Dashboard Server:"
  read -p "Start dashboard server? (y/n) [y]: " dashboard_choice
  dashboard_choice=${dashboard_choice:-y}
  if [[ $dashboard_choice =~ ^[Nn]$ ]]; then
    RUN_DASHBOARD=false
  else
    RUN_DASHBOARD=true
    read -p "Custom dashboard port? (leave empty for default $DASHBOARD_PORT): " custom_dashboard_port
    if [[ -n "$custom_dashboard_port" && "$custom_dashboard_port" =~ ^[0-9]+$ ]]; then
      DASHBOARD_PORT=$custom_dashboard_port
    fi
  fi
  
  echo ""
  log $BOLD "Dependencies:"
  read -p "Install dependencies? (y/n) [y]: " deps_choice
  deps_choice=${deps_choice:-y}
  if [[ $deps_choice =~ ^[Nn]$ ]]; then
    INSTALL_DEPENDENCIES=false
  else
    INSTALL_DEPENDENCIES=true
    read -p "Force update dependencies? (y/n) [n]: " update_choice
    update_choice=${update_choice:-n}
    if [[ $update_choice =~ ^[Yy]$ ]]; then
      FORCE_UPDATE_DEPS=true
    fi
  fi
  
  echo ""
  log $BOLD "Debug Mode:"
  read -p "Enable debug mode? (y/n) [n]: " debug_choice
  debug_choice=${debug_choice:-n}
  if [[ $debug_choice =~ ^[Yy]$ ]]; then
    DEBUG_MODE=true
  fi
  
  # Summary of selections
  echo ""
  log $CYAN "Your custom configuration:"
  echo "  - Backend server: $(if [ "$RUN_BACKEND" = true ]; then echo "Enabled (Port $BACKEND_PORT)"; else echo "Disabled"; fi)"
  echo "  - Dashboard server: $(if [ "$RUN_DASHBOARD" = true ]; then echo "Enabled (Port $DASHBOARD_PORT)"; else echo "Disabled"; fi)"
  echo "  - Install dependencies: $(if [ "$INSTALL_DEPENDENCIES" = true ]; then echo "Yes"; else echo "No"; fi)"
  echo "  - Force update dependencies: $(if [ "$FORCE_UPDATE_DEPS" = true ]; then echo "Yes"; else echo "No"; fi)"
  echo "  - Debug mode: $(if [ "$DEBUG_MODE" = true ]; then echo "Enabled"; else echo "Disabled"; fi)"
  echo ""
  
  read -p "Continue with these settings? (y/n) [y]: " confirm
  confirm=${confirm:-y}
  if [[ $confirm =~ ^[Nn]$ ]]; then
    log $YELLOW "Restarting configuration..."
    display_interactive_menu
  fi
}

# Function to check internet connectivity
check_internet_connection() {
  show_status "Checking internet connection"
  if ping -c 1 github.com &> /dev/null || ping -c 1 google.com &> /dev/null; then
    show_result true
    return 0
  else
    show_result false
    return 1
  fi
}

# Function to download the latest requirements.lock from GitHub
check_for_updates() {
  local TEMP_DIR="$PROJECT_ROOT/.temp_updates"
  local DEFAULT_REPO_URL="https://raw.githubusercontent.com/secure-video-summarizer/SVS"
  local DEFAULT_BRANCH="main"
  local DEFAULT_REQ_PATH="backend/requirements.lock"
  local REPO_URL=${SVS_REPO_URL:-$DEFAULT_REPO_URL}
  local BRANCH=${SVS_BRANCH:-$DEFAULT_BRANCH}
  local REQ_PATH=${SVS_REQ_PATH:-$DEFAULT_REQ_PATH}
  
  log $BLUE "=== Checking for Application Updates ==="
  echo ""
  
  log $BOLD "NOTE: This update process only checks for approved dependency updates"
  log $BOLD "and is designed to be run as part of the Cold Start process to"
  log $BOLD "avoid conflicts with existing installations."
  echo ""
  
  # Check for internet connection first
  if ! check_internet_connection; then
    log $YELLOW "No internet connection found. Continuing without updates in 5 seconds..."
    log $YELLOW "Press Ctrl+C to stop startup if you want to check your network connection."
    
    # 5-second timer countdown
    for i in {5..1}; do
      echo -ne "${YELLOW}$i...${NC}"
      sleep 1
    done
    echo -e "\r${GREEN}Continuing without updates.${NC}                      "
    return 1
  fi
  
  log $GREEN "Internet connection available. Checking for application updates..."
  
  # Create temporary directory
  show_status "Creating temporary directory"
  mkdir -p "$TEMP_DIR"
  show_result true
  
  # Build the URL to the requirements file on GitHub
  local remote_req_url="${REPO_URL}/${BRANCH}/${REQ_PATH}"
  
  # Download latest requirements
  show_status "Downloading latest requirements from GitHub"
  if curl -s -o "$TEMP_DIR/requirements.lock.latest" "$remote_req_url"; then
    show_result true
  else
    show_result false
    log $RED "Failed to download latest requirements from GitHub."
    log $RED "Repository may be unavailable or URL is incorrect."
    log $YELLOW "Repository URL: $remote_req_url"
    log $YELLOW "Continuing without updates in 5 seconds..."
    
    # 5-second timer countdown
    for i in {5..1}; do
      echo -ne "${YELLOW}$i...${NC}"
      sleep 1
    done
    echo -e "\r${GREEN}Continuing without updates.${NC}                      "
    
    rm -rf "$TEMP_DIR"
    return 1
  fi
  
  # Compare requirements
  local local_req="$BACKEND_DIR/requirements.lock"
  local remote_req="$TEMP_DIR/requirements.lock.latest"
  
  # Check if local requirements file exists
  if [ ! -f "$local_req" ]; then
    log $RED "Local requirements.lock file not found at $local_req"
    log $YELLOW "Continuing without updates in 5 seconds..."
    
    # 5-second timer countdown
    for i in {5..1}; do
      echo -ne "${YELLOW}$i...${NC}"
      sleep 1
    done
    echo -e "\r${GREEN}Continuing without updates.${NC}                      "
    
    rm -rf "$TEMP_DIR"
    return 1
  fi
  
  # Check if remote requirements file was downloaded
  if [ ! -f "$remote_req" ]; then
    log $RED "Remote requirements.lock file not found at $remote_req"
    log $YELLOW "Continuing without updates in 5 seconds..."
    
    # 5-second timer countdown
    for i in {5..1}; do
      echo -ne "${YELLOW}$i...${NC}"
      sleep 1
    done
    echo -e "\r${GREEN}Continuing without updates.${NC}                      "
    
    rm -rf "$TEMP_DIR"
    return 1
  fi
  
  show_status "Comparing local and remote requirements"
  
  # Create a temporary file to store differences
  local diff_file="$TEMP_DIR/requirements_diff.txt"
  
  # Compare files and store the result
  if diff -u "$local_req" "$remote_req" > "$diff_file"; then
    show_result true
    log $GREEN "No new updates found. Your application is up to date."
    rm -rf "$TEMP_DIR"
    return 0
  else
    show_result true
    log $YELLOW "The following updates will be installed:"
    echo ""
    
    # Process diff file to show only the important changes
    # Extract lines starting with +/- (excluding +++ and --- lines)
    grep -E "^[+-][^+-]" "$diff_file" | while read -r line; do
      if [[ $line == +* && $line != +++ ]]; then
        # This is a new or updated dependency
        echo -e "${GREEN}${line}${NC}"
      elif [[ $line == -* && $line != --- ]]; then
        # This is a removed or outdated dependency
        echo -e "${RED}${line}${NC}"
      fi
    done
    
    echo ""
    log $YELLOW "These updates have been reviewed and approved by the SVS team."
    
    # Ask if user wants to apply these updates
    echo ""
    log $BOLD "Would you like to apply these updates? (y/n)"
    read -p "Your choice: " update_choice
    
    if [[ $update_choice =~ ^[Yy]$ ]]; then
      echo ""
      # Backup current requirements.lock
      show_status "Backing up current requirements.lock"
      cp "$local_req" "$local_req.bak"
      show_result true
      
      # Apply updates
      show_status "Applying updates"
      cp "$remote_req" "$local_req"
      if [ $? -ne 0 ]; then
        show_result false
        log $RED "Failed to apply updates."
        log $YELLOW "Your original requirements.lock has been preserved as requirements.lock.bak"
        rm -rf "$TEMP_DIR"
        return 1
      else
        show_result true
        log $GREEN "Updates have been applied successfully."
        log $GREEN "Your original requirements.lock has been preserved as requirements.lock.bak"
      fi
    else
      log $YELLOW "Updates not applied. Continuing with existing dependencies."
    fi
  fi
  
  # Clean up temporary files
  rm -rf "$TEMP_DIR"
  return 0
}

# Function to print a section header
print_section_header() {
  local header_text="$1"
  local width=60
  local padding=$(( (width - ${#header_text} - 2) / 2 ))
  local padding_left=$padding
  local padding_right=$padding
  
  # Adjust padding if text length is odd
  if [ $(( (width - ${#header_text} - 2) % 2 )) -eq 1 ]; then
    padding_right=$(( padding_right + 1 ))
  fi
  
  local padding_str_left=$(printf '%*s' "$padding_left" '')
  local padding_str_right=$(printf '%*s' "$padding_right" '')
  
  echo ""
  echo -e "${CYAN}$(printf '%*s' "$width" '' | tr ' ' '=')"
  echo -e "${padding_str_left} ${BOLD}${header_text}${NC} ${padding_str_right}"
  echo -e "${CYAN}$(printf '%*s' "$width" '' | tr ' ' '=')${NC}"
  echo ""
}

# Function to summarize startup options
summarize_options() {
  print_section_header "STARTUP CONFIGURATION SUMMARY"
  
  echo -e "${YELLOW}Selected Mode:${NC} $LAST_RUN_MODE"
  
  # Only show server info if not in test mode
  if [ "$RUN_TESTS" != true ]; then
    echo -e "${YELLOW}Backend Server:${NC} $(if [ "$RUN_BACKEND" = true ]; then echo "Enabled (Port $BACKEND_PORT)"; else echo "Disabled"; fi)"
    echo -e "${YELLOW}Dashboard Server:${NC} $(if [ "$RUN_DASHBOARD" = true ]; then echo "Enabled (Port $DASHBOARD_PORT)"; else echo "Disabled"; fi)"
  else
    echo -e "${YELLOW}Test Mode:${NC} Enabled (servers will not start automatically)"
  fi
  
  echo -e "${YELLOW}Dependencies:${NC} $(if [ "$INSTALL_DEPENDENCIES" = true ]; then
                if [ "$OFFLINE_INSTALL" = true ]; then echo "Offline Installation";
                elif [ "$FORCE_UPDATE_DEPS" = true ]; then echo "Clean Install";
                else echo "Standard Install"; fi;
              else echo "Skip Installation"; fi)"
  echo -e "${YELLOW}Debug Mode:${NC} $(if [ "$DEBUG_MODE" = true ]; then echo "Enabled"; else echo "Disabled"; fi)"
  echo ""
}

# Function to install dependencies with offline support
install_dependencies() {
  local target_dir="$1"
  local venv_dir="$2"
  local name="$3"
  
  # Activate venv
  source "$venv_dir/bin/activate"
  
  if [ "$OFFLINE_INSTALL" = true ]; then
    show_status "Installing $name dependencies in offline mode"
    
    # Check if vendor directory exists
    if [ ! -d "$BACKEND_DIR/vendor" ] || [ -z "$(ls -A "$BACKEND_DIR/vendor" 2>/dev/null)" ]; then
      show_result false
      log $RED "Error: Vendor directory is empty or does not exist."
      log $RED "Please run './backend/scripts/package_dependencies.sh' with an internet connection first."
      return 1
    fi
    
    # Run the install script with offline flag
    if [ "$DEBUG_MODE" = true ]; then
      "$BACKEND_DIR/scripts/install_dependencies.sh" --offline --force
    else
      "$BACKEND_DIR/scripts/install_dependencies.sh" --offline
    fi
    
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Failed to install $name dependencies in offline mode."
      return 1
    fi
    show_result true
  else
    # Regular online installation
    show_status "Installing $name dependencies"
    
    if [ "$FORCE_UPDATE_DEPS" = true ]; then
      if [ "$DEBUG_MODE" = true ]; then
        "$BACKEND_DIR/scripts/install_dependencies.sh" --force
      else
        "$BACKEND_DIR/scripts/install_dependencies.sh" --force
      fi
    else
      if [ "$DEBUG_MODE" = true ]; then
        "$BACKEND_DIR/scripts/install_dependencies.sh"
      else
        "$BACKEND_DIR/scripts/install_dependencies.sh"
      fi
    fi
    
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Failed to install $name dependencies."
      return 1
    fi
    show_result true
  fi
  
  # Deactivate venv
  deactivate
  return 0
}

# Modify the existing start_backend_server function
start_backend_server() {
  show_status "Starting backend server on port $BACKEND_PORT"
  
  # Create command with proper flags
  local backend_cmd="./run_backend.sh"
  if [ "$DEBUG_MODE" = true ]; then
    backend_cmd="$backend_cmd --debug"
  else
    backend_cmd="$backend_cmd --no-debug"
  fi
  
  if [ "$FORCE_UPDATE_DEPS" = true ]; then
    backend_cmd="$backend_cmd --install-deps"
  fi
  
  if [ "$OFFLINE_INSTALL" = true ]; then
    backend_cmd="$backend_cmd --offline"
  fi
  
  backend_cmd="$backend_cmd --port $BACKEND_PORT"
  
  # Change to backend directory and run command
  (cd "$BACKEND_DIR" && $backend_cmd) > "$PROJECT_ROOT/backend.log" 2>&1 &
  BACKEND_PID=$!
  
  # Save PID to file
  echo "$BACKEND_PID" > "$PROJECT_ROOT/.backend_pid"
  
  # Wait a moment for backend to start
  sleep 2
  
  # Verify backend is running
  if ps -p "$BACKEND_PID" > /dev/null; then
    show_result true
    log $GREEN "Backend server started successfully on port $BACKEND_PORT (PID: $BACKEND_PID)"
    return 0
  else
    show_result false
    log $RED "Backend server failed to start on port $BACKEND_PORT"
    log $RED "Check backend.log for error details"
    return 1
  fi
}

# Modify the existing start_dashboard_server function
start_dashboard_server() {
  show_status "Starting dashboard server on port $DASHBOARD_PORT"
  
  # Create command with proper flags
  local dashboard_cmd="./run_dashboard.sh"
  if [ "$DEBUG_MODE" = true ]; then
    dashboard_cmd="$dashboard_cmd --debug"
  else
    dashboard_cmd="$dashboard_cmd --no-debug"
  fi
  
  if [ "$FORCE_UPDATE_DEPS" = true ]; then
    dashboard_cmd="$dashboard_cmd --install-deps"
  fi
  
  if [ "$OFFLINE_INSTALL" = true ]; then
    dashboard_cmd="$dashboard_cmd --offline"
  fi
  
  dashboard_cmd="$dashboard_cmd --port $DASHBOARD_PORT"
  
  # Change to backend directory and run command
  (cd "$BACKEND_DIR" && $dashboard_cmd) > "$PROJECT_ROOT/dashboard.log" 2>&1 &
  DASHBOARD_PID=$!
  
  # Save PID to file
  echo "$DASHBOARD_PID" > "$PROJECT_ROOT/.dashboard_pid"
  
  # Wait a moment for dashboard to start
  sleep 2
  
  # Verify dashboard is running
  if ps -p "$DASHBOARD_PID" > /dev/null; then
    show_result true
    log $GREEN "Dashboard server started successfully on port $DASHBOARD_PORT (PID: $DASHBOARD_PID)"
    return 0
  else
    show_result false
    log $RED "Dashboard server failed to start on port $DASHBOARD_PORT"
    log $RED "Check dashboard.log for error details"
    return 1
  fi
}

# Function to run application tests
run_application_tests() {
  print_section_header "RUNNING TESTS"
  
  # Make sure the test script is executable
  show_status "Preparing test runner script"
  chmod +x "$PROJECT_ROOT/run_tests.sh"
  show_result true
  
  # Ask for test options
  echo ""
  log $BOLD "Test options:"
  echo "  1) Run all tests"
  echo "  2) Run Python tests only"
  echo "  3) Run Jest tests only"
  echo "  4) Run tests with verbose output"
  echo ""
  read -p "Enter your choice [1-4]: " test_choice
  
  # Prepare test command
  local test_cmd="$PROJECT_ROOT/run_tests.sh"
  case $test_choice in
    2)
      test_cmd="$test_cmd --python-only"
      ;;
    3)
      test_cmd="$test_cmd --jest-only"
      ;;
    4)
      test_cmd="$test_cmd --verbose"
      ;;
    *)
      # Default is to run all tests
      ;;
  esac
  
  # Run the tests
  echo ""
  log $YELLOW "Running tests with command: $test_cmd"
  echo ""
  
  # Execute test command
  $test_cmd
  local test_result=$?
  
  # Handle test results
  if [ $test_result -eq 0 ]; then
    log $GREEN "All tests completed successfully!"
  else
    log $RED "Some tests failed. Please check the output above for details."
  fi
  
  # Ask if user wants to start the application after tests
  echo ""
  log $YELLOW "Would you like to start the application now? (y/n)"
  read -p "Your choice: " start_choice
  
  if [[ $start_choice =~ ^[Yy]$ ]]; then
    # Re-enable application start
    RUN_BACKEND=true
    RUN_DASHBOARD=true
    # Continue with normal startup
    return 0
  else
    # Exit after tests
    exit $test_result
  fi
}

# Main startup function
start_svs_application() {
  # Preliminary Steps: Ensure clean environment
  print_section_header "PREPARING ENVIRONMENT"
  
  # Make sure no virtual environments are active
  ensure_venv_deactivated
  
  # Make sure the shutdown script is executable
  show_status "Preparing shutdown script"
  chmod +x "$PROJECT_ROOT/stop_svs_application.sh"
  show_result true
  
  # Run the shutdown script to clean up existing instances
  log $BOLD "Running shutdown procedure to clean up any existing instances..."
  "$PROJECT_ROOT/stop_svs_application.sh" --quiet
  
  # Extra verification to ensure environment is clean
  verify_ports_clear
  verify_clean_environment
  
  # Summarize startup options before continuing
  summarize_options
  
  # Check if we should run tests
  if [ "$RUN_TESTS" = true ]; then
    run_application_tests
  fi
  
  # If neither service should run, exit
  if [ "$RUN_BACKEND" = false ] && [ "$RUN_DASHBOARD" = false ]; then
    log $RED "Error: Neither backend nor dashboard selected to run. Exiting..."
    exit 1
  fi

  # Initialize startup success flag
  STARTUP_SUCCESS=true

  # Step 2: Set up and start the backend server (if enabled)
  if [ "$RUN_BACKEND" = true ]; then
    print_section_header "STARTING BACKEND SERVER"
    
    # Change to backend directory
    show_status "Navigating to backend directory"
    cd "$BACKEND_DIR" || {
      show_result false
      log $RED "Error: Backend directory not found at $BACKEND_DIR"
      STARTUP_SUCCESS=false
      exit 1
    }
    show_result true

    # Create backend virtual environment
    create_venv "$BACKEND_VENV" "Backend"

    # Activate backend virtual environment
    show_status "Activating backend virtual environment"
    source "$BACKEND_VENV/bin/activate"
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Failed to activate backend virtual environment."
      STARTUP_SUCCESS=false
      exit 1
    fi
    show_result true

    # Install dependencies (if enabled)
    if [ "$INSTALL_DEPENDENCIES" = true ]; then
      install_dependencies "$BACKEND_DIR" "$BACKEND_VENV" "Backend"
      if [ $? -ne 0 ]; then
        show_result false
        log $RED "Error: Failed to install backend dependencies."
        deactivate
        STARTUP_SUCCESS=false
        exit 1
      fi
    fi

    # Set Flask environment variables
    export FLASK_APP=app
    export FLASK_ENV=$([ "$DEBUG_MODE" = true ] && echo "development" || echo "production")
    
    # Start backend server with the appropriate options
    start_backend_server
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Error: Failed to start backend server."
      deactivate
      STARTUP_SUCCESS=false
      exit 1
    fi

    # Deactivate backend venv
    show_status "Deactivating backend virtual environment"
    deactivate
    show_result true
  fi

  # Step 3: Set up and start the dashboard server (if enabled)
  if [ "$RUN_DASHBOARD" = true ]; then
    print_section_header "STARTING DASHBOARD SERVER"
    
    # Change to backend directory if not already there
    if [ "$RUN_BACKEND" = false ]; then
      show_status "Navigating to backend directory"
      cd "$BACKEND_DIR" || {
        show_result false
        log $RED "Error: Backend directory not found at $BACKEND_DIR"
        STARTUP_SUCCESS=false
        exit 1
      }
      show_result true
    fi
    
    # Make the script executable
    show_status "Preparing dashboard startup script"
    chmod +x run_dashboard.sh
    show_result true

    # Prepare dashboard arguments
    DASHBOARD_ARGS=""
    if [ "$INSTALL_DEPENDENCIES" = true ]; then
      DASHBOARD_ARGS="--install-deps"
    fi
    if [ "$FORCE_UPDATE_DEPS" = true ]; then
      DASHBOARD_ARGS="$DASHBOARD_ARGS --update"
    fi
    if [ "$DEBUG_MODE" = true ]; then
      DASHBOARD_ARGS="$DASHBOARD_ARGS --debug"
    else
      DASHBOARD_ARGS="$DASHBOARD_ARGS --no-debug"
    fi
    if [ "$OFFLINE_INSTALL" = true ]; then
      DASHBOARD_ARGS="$DASHBOARD_ARGS --offline"
    fi
    
    # Add config based on debug mode
    if [ "$DEBUG_MODE" = true ]; then
      DASHBOARD_ARGS="$DASHBOARD_ARGS --config development"
    else
      DASHBOARD_ARGS="$DASHBOARD_ARGS --config production"
    fi
    
    # Add port configuration if different from default
    if [ "$DASHBOARD_PORT" != "8080" ]; then
      DASHBOARD_ARGS="$DASHBOARD_ARGS --port $DASHBOARD_PORT"
    fi

    # Run the dashboard script with arguments
    start_dashboard_server
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Error: Failed to start dashboard server."
      deactivate
      STARTUP_SUCCESS=false
      exit 1
    fi
  fi

  # Step 4: Return to the project root
  show_status "Returning to project root directory"
  cd "$PROJECT_ROOT" || {
    show_result false
    log $RED "Error: Could not return to project root directory."
    STARTUP_SUCCESS=false
    exit 1
  }
  show_result true

  # Step 5: Verify running services
  print_section_header "VERIFYING SERVICES"
  
  VERIFICATION_SUCCESS=true
  
  if [ "$RUN_BACKEND" = true ]; then
    show_status "Checking backend server on port $BACKEND_PORT"
    if check_port $BACKEND_PORT; then
      show_result true
      log $GREEN "Backend server is running on port $BACKEND_PORT"
      
      # Test API response
      show_status "Testing backend API response"
      if curl -s "http://localhost:$BACKEND_PORT/api/status" | grep -q "SVS API"; then
        show_result true
        log $GREEN "Backend API is responding correctly"
      else
        show_result false
        log $YELLOW "Backend API is not responding as expected. Service may not be fully initialized."
        # Don't fail verification as the server might need more time
      fi
    else
      show_result false
      log $RED "Backend server is not running on port $BACKEND_PORT"
      VERIFICATION_SUCCESS=false
    fi
  fi

  if [ "$RUN_DASHBOARD" = true ]; then
    show_status "Checking dashboard server on port $DASHBOARD_PORT"
    if check_port $DASHBOARD_PORT; then
      show_result true
      log $GREEN "Dashboard server is running on port $DASHBOARD_PORT"
      
      # Test dashboard response
      show_status "Testing dashboard response"
      if curl -s "http://localhost:$DASHBOARD_PORT/dashboard" | grep -q "Dashboard"; then
        show_result true
        log $GREEN "Dashboard is responding correctly"
      else
        show_result false
        log $YELLOW "Dashboard is not responding as expected. Service may not be fully initialized."
        # Don't fail verification as the server might need more time
      fi
    else
      show_result false
      log $RED "Dashboard server is not running on port $DASHBOARD_PORT"
      # Don't fail verification for dashboard as it might be slow to start
    fi
  fi

  # Save configuration if startup was successful
  if [ "$STARTUP_SUCCESS" = true ] && [ "$VERIFICATION_SUCCESS" = true ]; then
    save_startup_config
  fi

  # Step 6: Print access information
  print_section_header "ACCESS INFORMATION"
  
  if [ "$RUN_BACKEND" = true ]; then
    log $GREEN "Backend server: http://localhost:$BACKEND_PORT"
    log $GREEN "API documentation: http://localhost:$BACKEND_PORT/api/docs"
  fi
  if [ "$RUN_DASHBOARD" = true ]; then
    log $GREEN "Dashboard: http://localhost:$DASHBOARD_PORT/dashboard"
    log $GREEN "Jobs page: http://localhost:$DASHBOARD_PORT/dashboard/jobs"
    log $GREEN "Admin page: http://localhost:$DASHBOARD_PORT/dashboard/admin"
    log $GREEN "Logs: http://localhost:$DASHBOARD_PORT/dashboard/logs"
  fi
  
  print_section_header "STARTUP COMPLETE"
  
  log $GREEN "Secure Video Summarizer is now running!"
  echo ""
  log $YELLOW "To test the job progress tracking, run:"
  log $YELLOW "    ./test_progress_tracking.sh"
  echo ""
  log $YELLOW "To stop the servers, run:"
  log $YELLOW "    ./stop_svs_application.sh"
  echo ""
  
  if [ "$DEBUG_MODE" = true ]; then
    log $CYAN "DEBUG MODE ENABLED - Check logs for detailed debug information:"
    log $CYAN "    Backend logs: $BACKEND_DIR/logs/backend_server.log"
    log $CYAN "    Dashboard logs: $BACKEND_DIR/logs/dashboard_server.log"
    echo ""
  fi
}

# Main execution flow
configure_default_settings
display_welcome_banner

# Check if command-line arguments were provided
if [ $# -gt 0 ]; then
  # Parse command-line arguments
  parse_args "$@"
else
  # Show interactive menu if no arguments provided
  display_interactive_menu
fi

# Start the application
start_svs_application 