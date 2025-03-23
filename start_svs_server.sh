#!/bin/bash
# Script to start the Secure Video Summarizer backend server
# This ensures the virtual environment is activated first

# Define paths
SVS_DIR="/Users/lightspeedtooblivion/Documents/SVS"
VENV_DIR="/Users/lightspeedtooblivion/Documents/SecureVideoSummarizer/venv"
PORT=8081

echo "Starting Secure Video Summarizer backend server..."
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
flask --app backend/app run --host=0.0.0.0 --port=$PORT --debug 