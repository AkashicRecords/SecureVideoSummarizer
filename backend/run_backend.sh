# Default settings
PORT=8081
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

# Check for updates if requested
if [ "$UPDATE_PACKAGES" = true ]; then
    echo -e "${YELLOW}Checking for package updates...${NC}"
    ./scripts/check_updates.sh
fi

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed or forced
if [ ! -f "venv/installed.flag" ] || [ "$FORCE_INSTALL" = true ]; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    
    if [ "$OFFLINE_MODE" = true ]; then
        # Use offline installation script
        ./scripts/install_dependencies.sh --offline
    else
        # Use regular installation script
        ./scripts/install_dependencies.sh
    fi
fi 