#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
PORT=8080
DEBUG=true
CONFIG="development"
FORCE_INSTALL=false
UPDATE_PACKAGES=false
OFFLINE_MODE=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --install-deps)
      FORCE_INSTALL=true
      shift
      ;;
    --update)
      UPDATE_PACKAGES=true
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --no-debug)
      DEBUG=false
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --offline)
      OFFLINE_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--install-deps] [--update] [--port PORT] [--debug|--no-debug] [--config CONFIG] [--offline]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}=== Starting SVS Dashboard ===${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Port: $PORT"
echo -e "  Debug mode: $DEBUG"
echo -e "  Config: $CONFIG"
echo -e "  Offline mode: $OFFLINE_MODE"

# Check for updates if requested
if [ "$UPDATE_PACKAGES" = true ]; then
    echo -e "${YELLOW}Checking for package updates...${NC}"
    ./scripts/check_updates.sh
fi

# Dashboard venv
DASHBOARD_VENV="dashboard_venv"

# Create/activate virtual environment
if [ ! -d "$DASHBOARD_VENV" ]; then
    echo -e "${YELLOW}Creating dashboard virtual environment...${NC}"
    python3 -m venv $DASHBOARD_VENV
fi

# Activate virtual environment
source $DASHBOARD_VENV/bin/activate

# Install requirements if needed or forced
if [ ! -f "$DASHBOARD_VENV/installed.flag" ] || [ "$FORCE_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing dashboard requirements...${NC}"
    
    if [ "$OFFLINE_MODE" = true ]; then
        # Use offline installation script
        ./scripts/install_dependencies.sh --offline
    else
        # Use regular installation script
        ./scripts/install_dependencies.sh
    fi
    
    # Also ensure dashboard-specific dependencies are installed
    pip install flask-socketio eventlet
    
    # Create installed flag
    touch "$DASHBOARD_VENV/installed.flag"
fi

# Set dashboard environment variables
export FLASK_APP=dashboard
export DASHBOARD_PORT=$PORT
export BACKEND_API_URL="http://localhost:8081"
export FLASK_ENV=$CONFIG
export DASHBOARD_DEBUG=$DEBUG

# Run the dashboard
echo -e "${GREEN}Starting dashboard on port $PORT...${NC}"

cd app

if [ "$DEBUG" = true ]; then
    echo -e "${YELLOW}Running in debug mode${NC}"
    python -m dashboard.app --port $PORT --debug
else
    echo -e "${YELLOW}Running in production mode${NC}"
    python -m dashboard.app --port $PORT
fi

# Note: This script will not terminate as Flask will keep running
# Use Ctrl+C to stop the dashboard 