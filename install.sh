#!/bin/bash

# Secure Video Summarizer Installer
echo "=========================================="
echo "   Secure Video Summarizer Installer"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or later."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: ffmpeg is required but not installed."
    echo "Please install ffmpeg using your system's package manager:"
    echo "  - On macOS: brew install ffmpeg"
    echo "  - On Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  - On Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Setup Chrome extension
echo "Setting up Chrome extension..."
cd extension
npm install
npm run build
cd ..

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp backend/.env.example .env
    # Generate a random secret key
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    echo "SECRET_KEY=$SECRET_KEY" >> .env
fi

echo ""
echo "Installation complete!"
echo ""
echo "To start the application:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the server:"
echo "   cd backend && flask run --port=8081 --debug"
echo ""
echo "3. Load the Chrome extension from the extension/dist folder"
echo ""
echo "=========================================="

# Make the script executable with: chmod +x install.sh 