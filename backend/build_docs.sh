#!/bin/bash
# Build documentation for Secure Video Summarizer

# Set up colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if sphinx-build is installed
if ! command -v sphinx-build &> /dev/null; then
    echo -e "${RED}Error: sphinx-build command not found.${NC}"
    echo -e "Please install Sphinx by running: ${YELLOW}pip install sphinx sphinx-rtd-theme${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p docs/build
mkdir -p docs/source/_static

echo -e "${YELLOW}Building documentation...${NC}"

# Build the HTML documentation
sphinx-build -b html docs/source docs/build/html

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Documentation built successfully!${NC}"
    echo -e "HTML documentation is available at: ${YELLOW}docs/build/html/index.html${NC}"
    
    # Open the documentation in the default browser if possible
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open docs/build/html/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open docs/build/html/index.html
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        start docs/build/html/index.html
    fi
else
    echo -e "${RED}Error: Documentation build failed.${NC}"
    exit 1
fi 