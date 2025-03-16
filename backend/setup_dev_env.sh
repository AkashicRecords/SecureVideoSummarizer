#!/bin/bash

# Script to set up the development environment for Secure Video Summarizer

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up development environment for Secure Video Summarizer...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check for system dependencies
echo -e "${YELLOW}Checking system dependencies...${NC}"

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}ffmpeg is not installed. This is required for audio/video processing.${NC}"
    echo -e "${YELLOW}Please install ffmpeg:${NC}"
    echo -e "  - macOS: brew install ffmpeg"
    echo -e "  - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo -e "  - Windows: Download from https://ffmpeg.org/download.html or use chocolatey: choco install ffmpeg"
    echo -e "${YELLOW}Please install ffmpeg and run this script again.${NC}"
    exit 1
fi

# Check for libmagic (needed for python-magic)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! brew list libmagic &> /dev/null; then
        echo -e "${RED}libmagic is not installed. This is required for file type detection.${NC}"
        echo -e "${YELLOW}Installing libmagic with Homebrew...${NC}"
        brew install libmagic
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if ! dpkg -l libmagic1 &> /dev/null; then
        echo -e "${RED}libmagic is not installed. This is required for file type detection.${NC}"
        echo -e "${YELLOW}Installing libmagic...${NC}"
        sudo apt-get update && sudo apt-get install -y libmagic1
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows - python-magic-bin will be installed via pip
    echo -e "${YELLOW}On Windows, python-magic-bin will be installed via pip.${NC}"
else
    echo -e "${YELLOW}Unknown OS type: $OSTYPE${NC}"
    echo -e "${YELLOW}Please manually install libmagic for your system.${NC}"
    echo -e "${YELLOW}For most systems, this is available as libmagic or libmagic1 in your package manager.${NC}"
fi

echo -e "${GREEN}All system dependencies are installed.${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package and try again.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install setuptools and wheel
echo -e "${YELLOW}Installing setuptools and wheel...${NC}"
pip install setuptools wheel

# Install OS-specific dependencies
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    echo -e "${YELLOW}Installing Windows-specific dependencies...${NC}"
    pip install python-magic-bin
fi

# Install dependencies from lock file
echo -e "${YELLOW}Installing dependencies from lock file...${NC}"
if [ -f "requirements.lock" ]; then
    pip install -r requirements.lock
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Failed to install from requirements.lock. Trying development requirements...${NC}"
        if [ -f "requirements.dev.txt" ]; then
            pip install -r requirements.dev.txt
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to install dependencies. Please check requirements.dev.txt and try again.${NC}"
                exit 1
            else
                echo -e "${GREEN}Successfully installed dependencies from requirements.dev.txt${NC}"
            fi
        else
            echo -e "${YELLOW}requirements.dev.txt not found. Trying requirements.txt...${NC}"
            pip install -r requirements.txt
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to install dependencies. Please check requirements.txt and try again.${NC}"
                exit 1
            else
                echo -e "${GREEN}Successfully installed dependencies from requirements.txt${NC}"
            fi
        fi
    else
        echo -e "${GREEN}Successfully installed dependencies from requirements.lock${NC}"
    fi
else
    echo -e "${YELLOW}requirements.lock not found. Using requirements.dev.txt instead.${NC}"
    if [ -f "requirements.dev.txt" ]; then
        pip install -r requirements.dev.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies. Please check requirements.dev.txt and try again.${NC}"
            exit 1
        else
            echo -e "${GREEN}Successfully installed dependencies from requirements.dev.txt${NC}"
        fi
    else
        echo -e "${YELLOW}requirements.dev.txt not found. Using requirements.txt...${NC}"
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies. Please check requirements.txt and try again.${NC}"
            exit 1
        else
            echo -e "${GREEN}Successfully installed dependencies from requirements.txt${NC}"
        fi
    fi
fi

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
python -c "import flask, torch, transformers, pydub, numpy; print('All core dependencies are installed.')"
if [ $? -ne 0 ]; then
    echo -e "${RED}Verification failed. Some dependencies may not be installed correctly.${NC}"
    exit 1
fi

# Make run_tests.py executable
echo -e "${YELLOW}Making run_tests.py executable...${NC}"
chmod +x run_tests.py

# Install pre-commit hooks
if [ "$OS" == "Darwin" ] || [ "$OS" == "Linux" ]; then
    echo "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    echo "Pre-commit hooks installed successfully."
fi

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${GREEN}To activate the environment, run: source venv/bin/activate${NC}"
echo -e "${GREEN}To run tests, run: ./run_tests.py${NC}" 