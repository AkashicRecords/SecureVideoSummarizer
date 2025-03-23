#!/bin/bash
# Script to start the Secure Video Summarizer backend server
# This ensures the virtual environment is activated first

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SVS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"  # Parent directory of the script (SVS root)
VENV_DIR="/Users/lightspeedtooblivion/Documents/SecureVideoSummarizer/venv"
PORT=8081

echo "Starting Secure Video Summarizer backend server..."
echo "Script location: $SCRIPT_DIR"
echo "SVS root directory: $SVS_DIR"
echo "Activating virtual environment at $VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if activation was successful
if [ $? -ne 0 ]; then
  echo "Error: Failed to activate virtual environment at $VENV_DIR"
  exit 1
fi

# Change to the SVS directory
cd "$SVS_DIR"

# Check if directory change was successful
if [ $? -ne 0 ]; then
  echo "Error: Failed to change to $SVS_DIR"
  exit 1
fi

# Display Python version and which pip
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"
echo "Using pip: $(which pip)"

# Start the Flask application with debug mode
echo "Starting Flask application on port $PORT..."
echo "Press CTRL+C to stop the server"

# Use the app directory relative to the script location
flask --app app run --host=0.0.0.0 --port=$PORT --debug 