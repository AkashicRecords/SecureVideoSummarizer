#!/bin/bash
# Script to package dependencies for offline installation

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Set project directories
PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENDOR_DIR="$BACKEND_DIR/vendor"
VENV_DIR="$PROJECT_ROOT/venv"

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

# Create and set up virtual environment
setup_venv() {
  show_status "Checking for virtual environment"
  if [ ! -d "$VENV_DIR" ]; then
    show_result false
    show_status "Creating virtual environment"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
      show_result false
      log $RED "Failed to create virtual environment."
      exit 1
    fi
    show_result true
  else
    show_result true
  fi
  
  show_status "Activating virtual environment"
  source "$VENV_DIR/bin/activate"
  if [ $? -ne 0 ]; then
    show_result false
    log $RED "Failed to activate virtual environment."
    exit 1
  fi
  show_result true
  
  show_status "Upgrading pip"
  pip install --upgrade pip
  if [ $? -ne 0 ]; then
    show_result false
    log $RED "Failed to upgrade pip."
    exit 1
  fi
  show_result true
}

# Download dependencies for offline installation
download_dependencies() {
  show_status "Creating vendor directory"
  mkdir -p "$VENDOR_DIR"
  show_result true
  
  show_status "Downloading backend dependencies"
  pip download -r "$BACKEND_DIR/requirements.lock" -d "$VENDOR_DIR" --no-deps
  if [ $? -ne 0 ]; then
    show_result false
    log $RED "Failed to download backend dependencies."
    exit 1
  fi
  show_result true
  
  # Download additional dependencies with exact versions
  show_status "Downloading additional dependencies"
  pip download -d "$VENDOR_DIR" --no-deps \
    elevenlabs==2.7.0 \
    flask-cors==3.0.10 \
    flask-session==0.4.0 \
    flask-limiter==2.4.0 \
    python-magic==0.4.24
  if [ $? -ne 0 ]; then
    show_result false
    log $YELLOW "Warning: Some additional dependencies may not have downloaded correctly."
  else
    show_result true
  fi
}

# Create the offline installation script
create_offline_install_script() {
  local script_path="$PROJECT_ROOT/install_offline.sh"
  
  show_status "Creating offline installation script"
  cat > "$script_path" << 'EOF'
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set project directories
PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENDOR_DIR="$BACKEND_DIR/vendor"

echo -e "${BLUE}=== Secure Video Summarizer - Offline Installation ===${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package and try again.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install from vendor directory
echo -e "${YELLOW}Installing dependencies from vendor directory...${NC}"
if [ -d "$VENDOR_DIR" ] && [ "$(ls -A "$VENDOR_DIR")" ]; then
    echo -e "${YELLOW}Installing with exact versions from requirements.lock...${NC}"
    pip install --no-index --find-links="$VENDOR_DIR" --no-deps -r "$BACKEND_DIR/requirements.lock"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies from vendor directory.${NC}"
        deactivate
        exit 1
    fi
    
    # Install additional dependencies with exact versions
    echo -e "${YELLOW}Installing additional dependencies with exact versions...${NC}"
    pip install --no-index --find-links="$VENDOR_DIR" --no-deps \
      elevenlabs==2.7.0 \
      flask-cors==3.0.10 \
      flask-session==0.4.0 \
      flask-limiter==2.4.0 \
      python-magic==0.4.24
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Warning: Some additional dependencies may not have installed correctly.${NC}"
    fi
else
    echo -e "${RED}Vendor directory not found or empty.${NC}"
    echo -e "${RED}Please run 'package_dependencies.sh' to download dependencies first.${NC}"
    deactivate
    exit 1
fi

echo -e "${GREEN}Successfully installed dependencies in offline mode.${NC}"
deactivate
EOF

  chmod +x "$script_path"
  show_result true
}

# Update start_svs_application.sh to include offline installation option
update_startup_script() {
  local temp_file="$(mktemp)"
  local target_file="$PROJECT_ROOT/start_svs_application.sh"
  
  show_status "Updating startup script with offline install option"
  
  # Create a backup of the original file
  cp "$target_file" "${target_file}.bak"
  
  # Find and replace the menu options
  awk '{
    if ($0 ~ /^  echo "  4\) Cold start \(clean install with dependencies\)"$/) {
      print $0;
      print "  echo \"  5) Offline installation (using packaged dependencies)\"";
      print "  echo \"  6) Development mode (with debug options)\"";
      print "  echo \"  7) Custom configuration\"";
      print "  echo \"  8) Exit\"";
      getline; getline; getline; getline;  # Skip the next 4 lines
    } else if ($0 ~ /^  read -p "Enter your choice \[1-7\]: " menu_choice$/) {
      print "  read -p \"Enter your choice [1-8]: \" menu_choice";
    } else if ($0 ~ /^  case \$menu_choice in$/) {
      print $0;
      next;
    } else if ($0 ~ /^    5\)$/) {
      print "    5)";
      print "      log $GREEN \"Performing offline installation using packaged dependencies...\"";
      print "      INSTALL_DEPENDENCIES=true";
      print "      OFFLINE_INSTALL=true";
      print "      LAST_RUN_MODE=\"offline_install\"";
      print "      ;;";
      print "    6)";
    } else if ($0 ~ /^    6\)$/) {
      print "    7)";
    } else if ($0 ~ /^    7\)$/) {
      print "    8)";
    } else if ($0 ~ /^    \*\)$/) {
      print $0;
    } else {
      print $0;
    }
  }' "$target_file" > "$temp_file"
  
  # Now update the installation part
  awk '{
    if ($0 ~ /^    # Install dependencies \(if enabled\)$/) {
      print $0;
      print "    if [ \"$INSTALL_DEPENDENCIES\" = true ]; then";
      print "      if [ \"$OFFLINE_INSTALL\" = true ]; then";
      print "        show_status \"Installing backend dependencies from vendor directory\"";
      print "        pip install --no-index --find-links=\"$BACKEND_DIR/vendor\" --no-deps -r requirements.lock";
      print "        if [ $? -ne 0 ]; then";
      print "          show_result false";
      print "          log $RED \"Error: Failed to install backend dependencies from vendor directory.\"";
      print "          log $RED \"Make sure to run package_dependencies.sh first to download dependencies.\"";
      print "          deactivate";
      print "          STARTUP_SUCCESS=false";
      print "          exit 1";
      print "        else";
      print "          show_result true";
      print "        fi";
      print "";
      print "        # Install additional dependencies with exact versions";
      print "        show_status \"Installing additional offline dependencies\"";
      print "        pip install --no-index --find-links=\"$BACKEND_DIR/vendor\" --no-deps \\";
      print "          elevenlabs==2.7.0 \\";
      print "          flask-cors==3.0.10 \\";
      print "          flask-session==0.4.0 \\";
      print "          flask-limiter==2.4.0 \\";
      print "          python-magic==0.4.24";
      print "        if [ $? -ne 0 ]; then";
      print "          show_result false";
      print "          log $YELLOW \"Warning: Some additional dependencies may not have installed correctly.\"";
      print "        else";
      print "          show_result true";
      print "        fi";
      print "      elif [ \"$FORCE_UPDATE_DEPS\" = true ]; then";
      getline;  # Skip the original if line
    } else {
      print $0;
    }
  }' "$temp_file" > "${temp_file}.2"
  
  # Add offline install variable to the top
  awk '{
    if ($0 ~ /^# Set default configuration$/) {
      print $0;
      getline;
      print $0;
      print "OFFLINE_INSTALL=false";
    } else {
      print $0;
    }
  }' "${temp_file}.2" > "$target_file"
  
  # Make sure permissions are preserved
  chmod +x "$target_file"
  
  # Clean up temporary files
  rm -f "$temp_file" "${temp_file}.2"
  
  show_result true
}

# Main function
main() {
  log $BLUE "=== Secure Video Summarizer - Package Dependencies ==="
  echo ""
  
  log $BOLD "This script will download and package dependencies for offline installation."
  log $BOLD "The packages will be stored in: $VENDOR_DIR"
  echo ""
  
  # Setup virtual environment
  log $BOLD "Step 1: Setting up virtual environment"
  setup_venv
  echo ""
  
  # Download dependencies
  log $BOLD "Step 2: Downloading dependencies"
  download_dependencies
  echo ""
  
  # Create offline installation script
  log $BOLD "Step 3: Creating offline installation script"
  create_offline_install_script
  echo ""
  
  # Update startup script
  log $BOLD "Step 4: Updating startup script with offline installation option"
  update_startup_script
  echo ""
  
  # Cleanup
  show_status "Deactivating virtual environment"
  deactivate
  show_result true
  
  log $GREEN "Dependencies have been successfully packaged for offline installation."
  log $GREEN "You can now use the following options:"
  log $GREEN "1. Run './install_offline.sh' for standalone offline installation"
  log $GREEN "2. Select 'Offline installation' option in the startup script"
  echo ""
  
  # Make this script executable
  chmod +x "$0"
}

# Run the main function
main 