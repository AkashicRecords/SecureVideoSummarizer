#!/bin/bash
# Script to check for updates to dependencies from GitHub repository

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Set default repository URL and branch
DEFAULT_REPO_URL="https://raw.githubusercontent.com/yourusername/secure-video-summarizer"
DEFAULT_BRANCH="main"
REPO_URL=${SVS_REPO_URL:-$DEFAULT_REPO_URL}
BRANCH=${SVS_BRANCH:-$DEFAULT_BRANCH}

# Set project directories
PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
TEMP_DIR="$PROJECT_ROOT/.temp_updates"

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

# Function to download the latest requirements.lock from GitHub
download_latest_requirements() {
  show_status "Creating temporary directory"
  mkdir -p "$TEMP_DIR"
  show_result true
  
  # Build the URL to the requirements.lock file on GitHub
  local remote_req_url="${REPO_URL}/${BRANCH}/backend/requirements.lock"
  
  show_status "Downloading latest requirements from GitHub"
  if curl -s -o "$TEMP_DIR/requirements.lock.latest" "$remote_req_url"; then
    show_result true
    return 0
  else
    show_result false
    log $RED "Failed to download latest requirements from GitHub."
    log $RED "Please check your internet connection and repository settings."
    log $YELLOW "Repository URL: $remote_req_url"
    return 1
  fi
}

# Function to compare local and remote requirements
compare_requirements() {
  local local_req="$BACKEND_DIR/requirements.lock"
  local remote_req="$TEMP_DIR/requirements.lock.latest"
  
  # Check if local requirements file exists
  if [ ! -f "$local_req" ]; then
    log $RED "Local requirements.lock file not found at $local_req"
    return 1
  fi
  
  # Check if remote requirements file was downloaded
  if [ ! -f "$remote_req" ]; then
    log $RED "Remote requirements.lock file not found at $remote_req"
    return 1
  fi
  
  show_status "Comparing local and remote requirements"
  
  # Create a temporary file to store differences
  local diff_file="$TEMP_DIR/requirements_diff.txt"
  
  # Compare files and store the result
  if diff -u "$local_req" "$remote_req" > "$diff_file"; then
    show_result true
    log $GREEN "Your dependencies are up to date. No updates available."
    return 0
  else
    show_result true
    log $YELLOW "Updates are available for the following dependencies:"
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
    return 2  # Return code 2 means updates are available
  fi
}

# Function to apply updates
apply_updates() {
  show_status "Backing up current requirements.lock"
  cp "$BACKEND_DIR/requirements.lock" "$BACKEND_DIR/requirements.lock.bak"
  show_result true
  
  show_status "Applying updates"
  cp "$TEMP_DIR/requirements.lock.latest" "$BACKEND_DIR/requirements.lock"
  if [ $? -ne 0 ]; then
    show_result false
    log $RED "Failed to apply updates."
    log $YELLOW "Your original requirements.lock has been preserved as requirements.lock.bak"
    return 1
  else
    show_result true
    log $GREEN "Updates have been applied successfully."
    log $GREEN "Your original requirements.lock has been preserved as requirements.lock.bak"
    return 0
  fi
}

# Function to clean up temporary files
cleanup() {
  show_status "Cleaning up temporary files"
  rm -rf "$TEMP_DIR"
  show_result true
}

# Main function
main() {
  log $BLUE "=== Secure Video Summarizer - Update Checker ==="
  echo ""
  
  # Note about updates and cold start
  log $BOLD "NOTE: This update process only checks for approved dependency updates"
  log $BOLD "and is designed to be run as part of the Cold Start process to"
  log $BOLD "avoid conflicts with existing installations."
  echo ""
  
  # Download latest requirements
  download_latest_requirements
  if [ $? -ne 0 ]; then
    cleanup
    exit 1
  fi
  
  # Compare requirements
  compare_requirements
  local compare_result=$?
  
  if [ $compare_result -eq 0 ]; then
    # No updates available
    cleanup
    exit 0
  elif [ $compare_result -eq 2 ]; then
    # Updates available, ask if user wants to apply them
    echo ""
    log $BOLD "Would you like to apply these updates? (y/n)"
    read -p "Your choice: " update_choice
    
    if [[ $update_choice =~ ^[Yy]$ ]]; then
      echo ""
      log $BOLD "Applying updates..."
      apply_updates
      
      # Suggest running package dependencies if updates were applied
      if [ $? -eq 0 ]; then
        echo ""
        log $BOLD "To use these updates in offline mode, you should repackage dependencies:"
        log $YELLOW "Run './package_dependencies.sh' to download the updated dependencies."
      fi
    else
      log $YELLOW "Updates not applied. You can apply them later by running this script again."
    fi
  else
    # Error occurred during comparison
    log $RED "An error occurred while comparing requirements."
    cleanup
    exit 1
  fi
  
  # Clean up temporary files
  cleanup
}

# Run the main function
main 