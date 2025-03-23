#!/bin/bash

# Script to run the Secure Video Summarizer backend server
# Checks dependencies, runs tests, and starts the server

# Configuration
VENV_PATH="/Users/lightspeedtooblivion/Documents/SecureVideoSummarizer/venv"
PORT=8081
DEBUG=true
CONFIG="development"
LOGS_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Log file
LOG_FILE="$LOGS_DIR/server_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

# Function to log messages
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "${BLUE}Starting Secure Video Summarizer server setup${NC}"
log "Working directory: $(pwd)"

# Check if the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    log "${RED}Virtual environment not found at $VENV_PATH${NC}"
    log "Creating new virtual environment..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        log "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    log "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    log "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi
log "${GREEN}Virtual environment activated${NC}"

# Install/upgrade pip
log "Upgrading pip..."
python -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    log "${YELLOW}Warning: Failed to upgrade pip${NC}"
fi

# Install required packages
log "Installing required packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    log "${YELLOW}Warning: Some packages may not have been installed correctly${NC}"
fi

# Make sure essential packages are installed
log "Installing essential packages..."
pip install flask flask-cors flask-session flask-limiter python-magic google-api-python-client google-auth-oauthlib elevenlabs pydub SpeechRecognition
if [ $? -ne 0 ]; then
    log "${YELLOW}Warning: Some essential packages may not have been installed correctly${NC}"
fi

# Set Python path to include the backend directory
export PYTHONPATH=$(pwd):$PYTHONPATH
log "Setting Python path: $PYTHONPATH"
log "Python version: $(python --version)"

# Create extension_routes.py if it doesn't exist
if [ ! -f "app/api/extension_routes.py" ]; then
    log "${YELLOW}extension_routes.py not found, creating it...${NC}"
    mkdir -p app/api
    cat > app/api/extension_routes.py << 'EOF'
from flask import Blueprint, jsonify, request, current_app
import logging
from app.utils.validators import validate_extension_origin

extension_bp = Blueprint('extension', __name__, url_prefix='/api/extension')
logger = logging.getLogger(__name__)

@extension_bp.route('/ping', methods=['GET'])
@validate_extension_origin
def ping():
    """Simple ping endpoint to check if backend is running"""
    logger.debug("Extension ping received")
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running',
        'version': '1.0.0',
        'using_ai': 'ollama'
    })

@extension_bp.route('/status', methods=['GET'])
@validate_extension_origin
def status():
    """Get the status of the extension integration"""
    logger.debug("Extension status check")
    return jsonify({
        'status': 'ready',
        'extension_id': current_app.config.get('EXTENSION_ID', 'Unknown'),
        'supported_features': [
            'transcript_generation',
            'summary_generation', 
            'offline_processing'
        ]
    })

@extension_bp.route('/config', methods=['GET'])
@validate_extension_origin
def get_config():
    """Get the extension configuration"""
    logger.debug("Extension config requested")
    return jsonify({
        'config': {
            'api_url': current_app.config.get('API_URL', 'http://localhost:8081'),
            'ai_provider': 'ollama',
            'summary_length': 'medium',
            'transcript_enabled': True,
            'summary_enabled': True,
            'debug_mode': current_app.config.get('DEBUG', False)
        }
    })
EOF
    log "${GREEN}Created extension_routes.py${NC}"
fi

# Start the server directly from app directory
log "${GREEN}Starting server on port $PORT${NC}"
log "Debug mode: $DEBUG"
log "Configuration: $CONFIG"

cd app
# Use the appropriate debug flag based on value
if [ "$DEBUG" = "true" ]; then
    python -c "import sys; sys.path.append('..'); from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=8081, debug=True)" 2>&1 | tee -a "$LOG_FILE"
else
    python -c "import sys; sys.path.append('..'); from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=8081)" 2>&1 | tee -a "$LOG_FILE"
fi 