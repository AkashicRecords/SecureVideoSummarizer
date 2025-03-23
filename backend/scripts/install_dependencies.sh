#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default settings
FORCE_INSTALL=false
OFFLINE_MODE=false
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
VENDOR_DIR="${PROJECT_ROOT}/vendor"
LOCK_FILE="${PROJECT_ROOT}/requirements.lock"

# Show help message
function show_help {
    echo -e "${BLUE}SVS Dependency Installer${NC}"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --force       Force reinstallation of dependencies"
    echo "  --offline     Use offline installation from vendor directory"
    echo "  --help        Show this help message"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --offline)
            OFFLINE_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check internet connection
function check_internet {
    echo -e "${YELLOW}Checking internet connection...${NC}"
    if ping -c 1 pypi.org &>/dev/null; then
        echo -e "${GREEN}Internet connection available${NC}"
        return 0
    else
        echo -e "${YELLOW}No internet connection available${NC}"
        return 1
    fi
}

# Check if an offline installation is possible
function check_offline_feasibility {
    if [ ! -d "$VENDOR_DIR" ] || [ -z "$(ls -A "$VENDOR_DIR" 2>/dev/null)" ]; then
        echo -e "${RED}Error: Vendor directory is empty or does not exist${NC}"
        return 1
    fi
    
    # Check if the vendor directory has the manifest file
    if [ ! -f "${VENDOR_DIR}/manifest.txt" ]; then
        echo -e "${YELLOW}Warning: Vendor directory does not contain a manifest file${NC}"
    fi
    
    return 0
}

# Main installation logic
echo -e "${BLUE}=== SVS Dependency Installer ===${NC}"

# Check if Python and pip are available
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command -v pip &>/dev/null; then
    echo -e "${RED}Error: pip is not installed${NC}"
    exit 1
fi

# Check if we need to install dependencies
VENV_INSTALLED_FLAG="${PROJECT_ROOT}/venv/installed.flag"
if [ "$FORCE_INSTALL" = true ] || [ ! -f "$VENV_INSTALLED_FLAG" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Check if offline mode is requested
    if [ "$OFFLINE_MODE" = true ]; then
        echo -e "${YELLOW}Running in offline mode${NC}"
        
        # Verify we can do an offline installation
        if ! check_offline_feasibility; then
            echo -e "${RED}Offline installation not possible. Exiting.${NC}"
            exit 1
        fi
        
        # Try to install from vendor directory
        echo -e "${YELLOW}Installing from vendor directory...${NC}"
        
        # Check if we have a lock file to use for precise versions
        if [ -f "$LOCK_FILE" ]; then
            echo -e "${YELLOW}Using requirements.lock for precise versions${NC}"
            if pip install --no-index --find-links="$VENDOR_DIR" -r "$LOCK_FILE"; then
                echo -e "${GREEN}Successfully installed dependencies from vendor directory using lock file${NC}"
            else
                echo -e "${RED}Failed to install using lock file. Trying with requirements.txt...${NC}"
                if pip install --no-index --find-links="$VENDOR_DIR" -r "$REQUIREMENTS_FILE"; then
                    echo -e "${GREEN}Successfully installed dependencies from vendor directory${NC}"
                else
                    echo -e "${RED}Failed to install dependencies. Please check your vendor directory.${NC}"
                    exit 1
                fi
            fi
        else
            echo -e "${YELLOW}No requirements.lock found, using requirements.txt${NC}"
            if pip install --no-index --find-links="$VENDOR_DIR" -r "$REQUIREMENTS_FILE"; then
                echo -e "${GREEN}Successfully installed dependencies from vendor directory${NC}"
            else
                echo -e "${RED}Failed to install dependencies. Please check your vendor directory.${NC}"
                exit 1
            fi
        fi
    else
        # Online installation
        echo -e "${YELLOW}Running in online mode${NC}"
        
        # Check internet connection
        if ! check_internet; then
            echo -e "${YELLOW}No internet connection. Trying offline installation...${NC}"
            
            # Verify we can do an offline installation
            if ! check_offline_feasibility; then
                echo -e "${RED}Offline installation not possible and no internet connection. Exiting.${NC}"
                exit 1
            fi
            
            # Try offline installation since we have no internet
            echo -e "${YELLOW}Installing from vendor directory...${NC}"
            if pip install --no-index --find-links="$VENDOR_DIR" -r "$REQUIREMENTS_FILE"; then
                echo -e "${GREEN}Successfully installed dependencies from vendor directory${NC}"
            else
                echo -e "${RED}Failed to install dependencies. Please check your vendor directory.${NC}"
                exit 1
            fi
        else
            # We have internet, use normal pip install
            echo -e "${YELLOW}Installing from PyPI...${NC}"
            if pip install -r "$REQUIREMENTS_FILE"; then
                echo -e "${GREEN}Successfully installed dependencies from PyPI${NC}"
                
                # Create a lock file for future offline installations
                echo -e "${YELLOW}Creating requirements.lock file...${NC}"
                pip freeze > "$LOCK_FILE"
            else
                echo -e "${RED}Failed to install dependencies from PyPI${NC}"
                exit 1
            fi
        fi
    fi
    
    # Create the installed flag
    touch "$VENV_INSTALLED_FLAG"
else
    echo -e "${GREEN}Dependencies already installed${NC}"
fi

echo -e "${GREEN}Done!${NC}"
exit 0 