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

echo -e "${BLUE}=== SVS Dependency Update Checker ===${NC}"

# Check internet connectivity
echo -e "${YELLOW}Checking internet connectivity...${NC}"
if ! ping -c 1 pypi.org >/dev/null 2>&1; then
    echo -e "${RED}No internet connection available. Skipping update check.${NC}"
    exit 0
fi

# Create temporary files
TEMP_REQS=$(mktemp)
TEMP_NEW_VERSIONS=$(mktemp)

# Load current requirements
echo -e "${YELLOW}Loading current requirements...${NC}"
pip freeze > "$TEMP_REQS"

# Check for updates
echo -e "${YELLOW}Checking for package updates...${NC}"
pip list --outdated --format=columns > "$TEMP_NEW_VERSIONS"

# Count the number of outdated packages (skipping header rows)
NUM_UPDATES=$(tail -n +3 "$TEMP_NEW_VERSIONS" | wc -l)

if [ "$NUM_UPDATES" -gt 0 ]; then
    echo -e "${YELLOW}Found $NUM_UPDATES package(s) with available updates:${NC}"
    tail -n +3 "$TEMP_NEW_VERSIONS" | awk '{printf "  %s: %s -> %s\n", $1, $2, $3}'
    
    # Show options
    echo
    echo -e "${BLUE}Options:${NC}"
    echo "1. Update all packages and rebuild vendor directory"
    echo "2. View details of available updates"
    echo "3. Skip updates for now"
    
    read -p "Your choice (1-3): " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}Updating packages...${NC}"
            pip install --upgrade -r "${PROJECT_ROOT}/requirements.txt"
            
            echo -e "${YELLOW}Rebuilding vendor directory...${NC}"
            "${SCRIPT_DIR}/package_dependencies.sh"
            ;;
        2)
            echo -e "${BLUE}=== Update Details ===${NC}"
            pip list --outdated --format=columns
            echo
            read -p "Update all packages now? (y/n): " confirm
            if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
                echo -e "${YELLOW}Updating packages...${NC}"
                pip install --upgrade -r "${PROJECT_ROOT}/requirements.txt"
                
                echo -e "${YELLOW}Rebuilding vendor directory...${NC}"
                "${SCRIPT_DIR}/package_dependencies.sh"
            fi
            ;;
        3)
            echo -e "${YELLOW}Skipping updates.${NC}"
            ;;
        *)
            echo -e "${RED}Invalid option. Skipping updates.${NC}"
            ;;
    esac
else
    echo -e "${GREEN}All packages are up to date!${NC}"
fi

# Clean up
rm -f "$TEMP_REQS" "$TEMP_NEW_VERSIONS"

exit 0 