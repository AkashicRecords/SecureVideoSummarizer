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

# Create vendor directory
VENDOR_DIR="${PROJECT_ROOT}/vendor"
mkdir -p "$VENDOR_DIR"

echo -e "${BLUE}=== SVS Dependency Packager ===${NC}"
echo -e "${YELLOW}This script will download and package all dependencies for offline installation.${NC}"
echo

# Check if pip is available
if ! command -v pip >/dev/null 2>&1; then
    echo -e "${RED}Error: pip is not installed or not in PATH${NC}"
    exit 1
fi

# Clean vendor directory
echo -e "${YELLOW}Cleaning vendor directory...${NC}"
rm -rf "$VENDOR_DIR"/*

# Create requirements.lock with exact versions
echo -e "${YELLOW}Creating requirements.lock with exact versions...${NC}"
pip freeze > "${PROJECT_ROOT}/requirements.lock"

# Download all packages
echo -e "${YELLOW}Downloading all packages to vendor directory...${NC}"
pip download -r "${PROJECT_ROOT}/requirements.txt" --dest "$VENDOR_DIR"

# If requirements.lock exists and is different from what we just generated,
# download those specific versions too
if [ -f "${PROJECT_ROOT}/requirements.lock.previous" ]; then
    echo -e "${YELLOW}Found previous requirements.lock, downloading those versions too...${NC}"
    pip download -r "${PROJECT_ROOT}/requirements.lock.previous" --dest "$VENDOR_DIR"
fi

# Save current requirements.lock as previous for next time
cp "${PROJECT_ROOT}/requirements.lock" "${PROJECT_ROOT}/requirements.lock.previous"

# Count packages
PACKAGE_COUNT=$(ls -1 "$VENDOR_DIR" | wc -l)

echo -e "${GREEN}Successfully packaged $PACKAGE_COUNT dependencies to $VENDOR_DIR${NC}"
echo -e "${BLUE}You can now install these dependencies offline using:${NC}"
echo -e "${YELLOW}pip install --no-index --find-links=$VENDOR_DIR -r requirements.txt${NC}"

# Create a manifest file of all packages
echo -e "${YELLOW}Creating package manifest...${NC}"
ls -1 "$VENDOR_DIR" > "${VENDOR_DIR}/manifest.txt"

echo -e "${GREEN}Done!${NC}" 