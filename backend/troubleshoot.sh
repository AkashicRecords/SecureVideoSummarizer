#!/bin/bash
# Troubleshooting script for Secure Video Summarizer backend
# Provides diagnostic information to help identify common issues

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SVS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"  # Parent directory of the script (SVS root)
VENV_DIR="/Users/lightspeedtooblivion/Documents/SecureVideoSummarizer/venv"

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}====== Secure Video Summarizer Troubleshooting ======${NC}"
echo -e "${BLUE}Running diagnostics from:${NC} $SCRIPT_DIR"
echo -e "${BLUE}SVS root directory:${NC} $SVS_DIR"
echo ""

# 1. Check if virtual environment exists
echo -e "${BOLD}[1] Checking Virtual Environment${NC}"
if [ -d "$VENV_DIR" ]; then
  echo -e "  ${GREEN}✓ Virtual environment found at:${NC} $VENV_DIR"
  
  # Activate the virtual environment
  source "$VENV_DIR/bin/activate"
  if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓ Virtual environment activated successfully${NC}"
    echo -e "    Python: $(which python)"
    echo -e "    Version: $(python --version 2>&1)"
  else
    echo -e "  ${RED}✗ Failed to activate virtual environment${NC}"
  fi
else
  echo -e "  ${RED}✗ Virtual environment not found at:${NC} $VENV_DIR"
fi
echo ""

# 2. Check network ports
echo -e "${BOLD}[2] Checking Network Ports${NC}"

# Check if the default ports are in use
echo -e "  ${BLUE}Checking if port 8080 is in use (API default port):${NC}"
if lsof -i:8080 > /dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠ Port 8080 is currently in use by:${NC}"
    lsof -i:8080
else
    echo -e "  ${GREEN}✓ Port 8080 is available${NC}"
fi

echo -e "  ${BLUE}Checking if port 8081 is in use (Alt API port):${NC}"
if lsof -i:8081 > /dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠ Port 8081 is currently in use by:${NC}"
    lsof -i:8081
else
    echo -e "  ${GREEN}✓ Port 8081 is available${NC}"
fi
echo ""

# 3. Check if required Python packages are installed
echo -e "${BOLD}[3] Checking Required Python Packages${NC}"
REQUIRED_PACKAGES=("flask" "flask-cors" "python-magic" "werkzeug" "requests" "flask_limiter" "openai" "numpy" "pydub")

for package in "${REQUIRED_PACKAGES[@]}"; do
  if python -c "import $package" 2>/dev/null; then
    version=$(python -c "import $package; print($package.__version__)" 2>/dev/null)
    if [ -z "$version" ]; then
      version="installed (version unknown)"
    fi
    echo -e "  ${GREEN}✓ $package:${NC} $version"
  else
    echo -e "  ${RED}✗ $package is not installed${NC}"
  fi
done
echo ""

# 4. Check Configuration Files
echo -e "${BOLD}[4] Checking Configuration Files${NC}"

# Check for .env file
if [ -f "$SVS_DIR/.env" ]; then
  echo -e "  ${GREEN}✓ .env file found${NC}"
  echo -e "  Environment variables in .env file:"
  grep -v '^#' "$SVS_DIR/.env" | grep -v '^$' | while read -r line; do
    key=$(echo "$line" | cut -d '=' -f 1)
    echo -e "    - $key"
  done
  
  # Check for critical keys
  CRITICAL_KEYS=("OPENAI_API_KEY" "SECRET_KEY" "DEBUG" "ALLOWED_EXTENSION_IDS" "FLASK_ENV")
  for key in "${CRITICAL_KEYS[@]}"; do
    if grep -q "^$key=" "$SVS_DIR/.env"; then
      echo -e "  ${GREEN}✓ Critical key found:${NC} $key"
    else
      echo -e "  ${RED}✗ Critical key missing:${NC} $key"
    fi
  done
else
  echo -e "  ${YELLOW}⚠ .env file not found at $SVS_DIR/.env${NC}"
fi

# Check for config.py
if [ -f "$SCRIPT_DIR/app/config.py" ]; then
  echo -e "  ${GREEN}✓ config.py file found${NC}"
  echo -e "  Configuration settings:"
  CONFIGS=("DEBUG" "TESTING" "SECRET_KEY" "UPLOAD_FOLDER" "VIDEOS_DIR" "SUMMARIES_DIR" "ALLOWED_EXTENSIONS")
  for config in "${CONFIGS[@]}"; do
    if grep -q "$config" "$SCRIPT_DIR/app/config.py"; then
      value=$(grep "$config" "$SCRIPT_DIR/app/config.py" | head -1)
      echo -e "    - $value"
    fi
  done
else
  echo -e "  ${YELLOW}⚠ config.py file not found at $SCRIPT_DIR/app/config.py${NC}"
fi
echo ""

# 5. Check CORS configuration
echo -e "${BOLD}[5] Checking CORS Configuration${NC}"
# Look for CORS configuration in Python files
echo -e "  CORS settings found in files:"
grep -r "CORS" --include="*.py" "$SCRIPT_DIR" | grep -v "__pycache__" | while read -r line; do
  echo -e "  ${BLUE}$(echo $line | cut -d ':' -f 1):${NC}"
  echo "    $(echo $line | cut -d ':' -f 2-)"
done

# Check if CORS is properly initialized in app/__init__.py
if grep -q "CORS(" "$SCRIPT_DIR/app/__init__.py"; then
  echo -e "  ${GREEN}✓ CORS initialized in app/__init__.py${NC}"
  
  # Extract CORS configuration
  echo -e "  CORS configuration:"
  cors_config=$(grep -A 5 "CORS(" "$SCRIPT_DIR/app/__init__.py")
  echo -e "    $cors_config"
  
  # Check for origins setting
  if echo "$cors_config" | grep -q "origins"; then
    echo -e "  ${GREEN}✓ CORS origins configured${NC}"
  else
    echo -e "  ${YELLOW}⚠ CORS origins not explicitly configured${NC}"
  fi
else
  echo -e "  ${RED}✗ CORS not initialized in app/__init__.py${NC}"
fi
echo ""

# 6. Check for directories and permissions
echo -e "${BOLD}[6] Checking Directories and Permissions${NC}"
DIRS_TO_CHECK=("$SVS_DIR/logs" "$SVS_DIR/backend/app/data" "$SVS_DIR/backend/app/static" "$SVS_DIR/videos" "$SVS_DIR/summaries")

for dir in "${DIRS_TO_CHECK[@]}"; do
  if [ -d "$dir" ]; then
    perm=$(ls -ld "$dir" | awk '{print $1}')
    owner=$(ls -ld "$dir" | awk '{print $3}')
    echo -e "  ${GREEN}✓ Directory exists:${NC} $dir (permissions: $perm, owner: $owner)"
    
    # Check if directory is writable
    if [ -w "$dir" ]; then
      echo -e "    ${GREEN}✓ Directory is writable${NC}"
    else
      echo -e "    ${RED}✗ Directory is not writable${NC}"
    fi
  else
    echo -e "  ${RED}✗ Directory does not exist:${NC} $dir"
  fi
done
echo ""

# 7. Check for log files and errors
echo -e "${BOLD}[7] Checking Log Files${NC}"
LOG_DIR="$SVS_DIR/logs"

if [ -d "$LOG_DIR" ]; then
  echo -e "  ${GREEN}✓ Log directory found at:${NC} $LOG_DIR"
  
  # List most recent log files
  echo -e "  ${BLUE}Most recent log files:${NC}"
  find "$LOG_DIR" -type f -name "*.log" -o -name "*.txt" | xargs ls -lt | head -5 | while read -r logfile; do
    name=$(echo "$logfile" | awk '{print $NF}')
    if [ -n "$name" ]; then
      echo -e "    - $name"
      
      # Show any errors in the log file (last 5)
      errors=$(grep -i "error" "$name" | tail -5)
      if [ -n "$errors" ]; then
        echo -e "      ${YELLOW}Recent errors:${NC}"
        echo "$errors" | while read -r error; do
          echo "        $error"
        done
      fi
    fi
  done
  
  # Check log size
  echo -e "  ${BLUE}Checking log sizes:${NC}"
  largest_logs=$(find "$LOG_DIR" -type f -name "*.log" -o -name "*.txt" | xargs du -h | sort -hr | head -3)
  if [ -n "$largest_logs" ]; then
    echo -e "  Largest log files:"
    echo "$largest_logs" | while read -r line; do
      echo -e "    $line"
    done
  fi
else
  echo -e "  ${YELLOW}⚠ Log directory not found at:${NC} $LOG_DIR"
fi
echo ""

# 8. Database check (if applicable)
echo -e "${BOLD}[8] Checking Database${NC}"
DB_FILE="$SVS_DIR/backend/app/data/svs.db"

if [ -f "$DB_FILE" ]; then
  echo -e "  ${GREEN}✓ Database file found at:${NC} $DB_FILE"
  echo -e "  File size: $(du -h "$DB_FILE" | cut -f1)"
  echo -e "  Last modified: $(stat -f "%Sm" "$DB_FILE")"
  
  # Check if sqlite3 is available
  if command -v sqlite3 &> /dev/null; then
    echo -e "  ${BLUE}Database tables:${NC}"
    sqlite3 "$DB_FILE" ".tables" | tr ' ' '\n' | while read -r table; do
      if [ -n "$table" ]; then
        count=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM $table;")
        echo -e "    - $table: $count records"
      fi
    done
  else
    echo -e "  ${YELLOW}⚠ sqlite3 not available to inspect database${NC}"
  fi
else
  echo -e "  ${YELLOW}⚠ Database file not found at:${NC} $DB_FILE"
fi
echo ""

# 9. Check disk space
echo -e "${BOLD}[9] Checking Disk Space${NC}"
echo -e "  ${BLUE}Available disk space:${NC}"
df -h | grep -E "Filesystem|/dev/disk1" | awk '{print "  "$0}'
echo ""

# 10. Extension build check
echo -e "${BOLD}[10] Checking Extension Build${NC}"
EXTENSION_DIR="$SVS_DIR/extension"
if [ -d "$EXTENSION_DIR" ]; then
  echo -e "  ${GREEN}✓ Extension directory found at:${NC} $EXTENSION_DIR"
  
  # Check manifest.json in both source and build
  if [ -f "$EXTENSION_DIR/manifest.json" ]; then
    echo -e "  ${GREEN}✓ Source manifest.json found${NC}"
    ext_version=$(grep '"version"' "$EXTENSION_DIR/manifest.json" | head -1 | cut -d'"' -f4)
    echo -e "    Extension version: $ext_version"
    
    # Check permissions
    permissions=$(grep -A10 '"permissions"' "$EXTENSION_DIR/manifest.json")
    echo -e "    Permissions:"
    echo "$permissions" | grep -v "permissions" | grep -v "^--$" | while read -r line; do
      echo -e "      $line"
    done
  fi
  
  if [ -f "$EXTENSION_DIR/build/manifest.json" ]; then
    echo -e "  ${GREEN}✓ Extension build found${NC}"
    build_date=$(stat -f "%Sm" "$EXTENSION_DIR/build/manifest.json")
    echo -e "    Build date: $build_date"
  else
    echo -e "  ${YELLOW}⚠ Extension build not found${NC}"
  fi
  
  # Check extension API URL configuration
  echo -e "  ${BLUE}Checking extension API URL configuration:${NC}"
  api_url=$(grep "API_BASE_URL" "$EXTENSION_DIR/popup.js" | head -1)
  echo -e "    $api_url"
else
  echo -e "  ${RED}✗ Extension directory not found at:${NC} $EXTENSION_DIR"
fi
echo ""

# 11. Check API endpoints
echo -e "${BOLD}[11] Testing API Endpoints${NC}"
echo -e "  ${YELLOW}Note: This requires the server to be running${NC}"

# Try to ping the API if it's running
for port in 8080 8081; do
  echo -e "  ${BLUE}Testing API on port $port:${NC}"
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/api/health 2>/dev/null | grep -q "200"; then
    echo -e "    ${GREEN}✓ API is responding on port $port${NC}"
    
    # Get more information about the API
    status_response=$(curl -s http://localhost:$port/api/extension/status)
    echo -e "    Status response: $status_response"
  else
    echo -e "    ${YELLOW}⚠ API is not responding on port $port${NC}"
  fi
done

echo -e "  ${BLUE}You can test endpoints with:${NC}"
echo -e "    curl -v http://localhost:8081/api/extension/status"
echo -e "    curl -v http://localhost:8081/api/health"
echo -e "    curl -v http://localhost:8081/api/video/list"
echo ""

# 12. Check system state
echo -e "${BOLD}[12] Checking System State${NC}"
echo -e "  ${BLUE}System memory:${NC}"
vm_stat | grep "Pages free" | awk '{print "    Free memory: " $3 * 4096 / 1048576 " MB"}'

echo -e "  ${BLUE}Current processes:${NC}"
ps -ef | grep -E "python|flask|node" | grep -v grep | while read -r process; do
  pid=$(echo "$process" | awk '{print $2}')
  cmd=$(echo "$process" | awk '{for(i=8;i<=NF;i++) printf "%s ", $i}')
  echo -e "    - PID $pid: $cmd"
done
echo ""

echo -e "${BOLD}====== Troubleshooting Complete ======${NC}"
echo -e "For more detailed debugging, you can start the server in debug mode using:"
echo -e "  ${BLUE}./start_svs_server.sh${NC}"
echo "" 