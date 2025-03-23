#!/bin/bash

# Debug script for SVS startup process
set -x  # Enable command tracing

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SVS Startup Debug Tool ===${NC}"
echo "Starting debug process with development mode"

# Set paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKEND_VENV="$BACKEND_DIR/venv"
DASHBOARD_VENV="$BACKEND_DIR/dashboard_venv"
BACKEND_PORT=8081
DASHBOARD_PORT=8080

# Debug 1: Check directory structure
echo -e "${YELLOW}Checking directory structure...${NC}"
ls -la "$PROJECT_ROOT"
ls -la "$BACKEND_DIR"
ls -la "$BACKEND_DIR/scripts" || echo "Scripts directory not found"

# Debug 2: Check script permissions
echo -e "${YELLOW}Checking script permissions...${NC}"
ls -la "$PROJECT_ROOT/start_svs_application.sh"
ls -la "$PROJECT_ROOT/stop_svs_application.sh"
ls -la "$BACKEND_DIR/run_backend.sh" 
ls -la "$BACKEND_DIR/run_dashboard.sh"
if [ -d "$BACKEND_DIR/scripts" ]; then
  ls -la "$BACKEND_DIR/scripts/"*.sh
fi

# Debug 3: Check for Python and virtual environments
echo -e "${YELLOW}Checking Python environment...${NC}"
which python3
python3 --version
python3 -m venv --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Python venv module is available"
else
  echo "Python venv module is NOT available"
fi

# Debug 4: Create/check virtual environments
echo -e "${YELLOW}Checking virtual environments...${NC}"
if [ ! -d "$BACKEND_VENV" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv "$BACKEND_VENV"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create backend virtual environment${NC}"
  else
    echo -e "${GREEN}Backend virtual environment created successfully${NC}"
  fi
else
  echo -e "${GREEN}Backend virtual environment exists${NC}"
fi

if [ ! -d "$DASHBOARD_VENV" ]; then
  echo "Creating dashboard virtual environment..."
  python3 -m venv "$DASHBOARD_VENV"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create dashboard virtual environment${NC}"
  else
    echo -e "${GREEN}Dashboard virtual environment created successfully${NC}"
  fi
else
  echo -e "${GREEN}Dashboard virtual environment exists${NC}"
fi

# Debug 5: Check dependency scripts
echo -e "${YELLOW}Checking dependency scripts...${NC}"
if [ -f "$BACKEND_DIR/scripts/install_dependencies.sh" ]; then
  echo "install_dependencies.sh exists"
else
  echo "install_dependencies.sh NOT found"
fi

# Debug 6: Try to manually activate and install
echo -e "${YELLOW}Testing virtual environment activation...${NC}"
if [ -f "$BACKEND_VENV/bin/activate" ]; then
  echo "Trying to activate backend venv..."
  source "$BACKEND_VENV/bin/activate"
  if [ $? -eq 0 ]; then
    echo "Successfully activated backend venv"
    echo "Python path: $(which python)"
    echo "Checking pip..."
    pip --version
  else
    echo "Failed to activate backend venv"
  fi
  deactivate 2>/dev/null || echo "No active venv to deactivate"
else
  echo "Backend venv activate script not found"
fi

# Debug 7: Check network connectivity for updates
echo -e "${YELLOW}Checking network connectivity...${NC}"
if ping -c 1 google.com &> /dev/null; then
  echo "Internet connection is available"
else
  echo "Internet connection is NOT available"
fi

# Debug 8: Check backend run script
echo -e "${YELLOW}Examining backend run script...${NC}"
if [ -f "$BACKEND_DIR/run_backend.sh" ]; then
  head -n 20 "$BACKEND_DIR/run_backend.sh"
else
  echo "Backend run script not found"
fi

# Debug 9: Force run the backend script directly
echo -e "${YELLOW}Attempting to run backend script directly...${NC}"
if [ -f "$BACKEND_DIR/run_backend.sh" ]; then
  echo "Running backend script with --debug flag..."
  (cd "$BACKEND_DIR" && ./run_backend.sh --debug --port $BACKEND_PORT) > "$PROJECT_ROOT/debug_backend.log" 2>&1 &
  BACKEND_PID=$!
  echo "Backend started with PID: $BACKEND_PID"
  echo "Backend log saved to debug_backend.log"
  sleep 5
  if ps -p $BACKEND_PID > /dev/null; then
    echo "Backend process is still running after 5 seconds"
  else
    echo "Backend process is NOT running after 5 seconds"
    echo "Last 20 lines of backend log:"
    tail -n 20 "$PROJECT_ROOT/debug_backend.log"
  fi
else
  echo "Backend run script not found"
fi

echo -e "${BLUE}=== Debug process complete ===${NC}"
echo "Please examine the output for clues about startup issues"
echo "If backend was started, terminate it with: kill $BACKEND_PID" 