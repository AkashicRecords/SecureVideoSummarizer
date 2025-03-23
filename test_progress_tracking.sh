#!/bin/bash
# Test script for progress tracking functionality
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default settings
BACKEND_PORT=8081
DASHBOARD_PORT=8080
TEST_VIDEO_PATH="test_videos/sample.mp4"
MAX_RETRIES=10

# Function to show colored output
log() {
  echo -e "${1}${2}${NC}"
}

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check if server is running
check_server() {
  local url=$1
  local name=$2
  
  echo -n "Checking if $name is running at $url... "
  if curl -s "$url" > /dev/null; then
    echo "YES"
    return 0
  else
    echo "NO"
    return 1
  fi
}

# Ensure we're in the project root
cd "$(dirname "$0")"

# Step 1: Check dependencies
log $YELLOW "Checking dependencies..."

if ! command_exists python3; then
  log $RED "Python 3 is required but not installed."
  exit 1
fi

if ! command_exists pip3; then
  log $RED "Pip3 is required but not installed."
  exit 1
fi

if ! command_exists ffmpeg; then
  log $RED "ffmpeg is required but not installed."
  exit 1
fi

# Step 2: Install required Python packages
log $YELLOW "Installing required packages..."
pip3 install opencv-python requests numpy

# Step 3: Create test video
log $YELLOW "Creating test video..."
DURATION=${1:-10}
VIDEO_PATH="backend/uploads/videos/test_video.mp4"

python3 backend/create_test_video.py --output $VIDEO_PATH --duration $DURATION

if [ ! -f "$VIDEO_PATH" ]; then
  log $RED "Failed to create test video at $VIDEO_PATH"
  exit 1
fi

log $GREEN "Test video created successfully at $VIDEO_PATH"

echo ""
log $BLUE "=== SVS Progress Tracking Test ==="
echo ""

# Check if backend is running
if ! check_server "http://localhost:$BACKEND_PORT/api/status" "Backend API"; then
  log $RED "Backend server is not running. Please start it with ./start_svs_application.sh"
  exit 1
fi

# Check if dashboard is running
if ! check_server "http://localhost:$DASHBOARD_PORT/dashboard" "Dashboard"; then
  log $RED "Dashboard server is not running. Please start it with ./start_svs_application.sh"
  exit 1
fi

# Check if test video exists
if [ ! -f "$TEST_VIDEO_PATH" ]; then
  log $YELLOW "Test video not found at $TEST_VIDEO_PATH"
  
  # Create test videos directory if it doesn't exist
  mkdir -p test_videos
  
  log $YELLOW "Downloading a sample video for testing..."
  curl -L "https://filesamples.com/samples/video/mp4/sample_640x360.mp4" -o "$TEST_VIDEO_PATH"
  
  if [ ! -f "$TEST_VIDEO_PATH" ]; then
    log $RED "Failed to download test video. Please place a video file at $TEST_VIDEO_PATH manually."
    exit 1
  fi
  
  log $GREEN "Test video downloaded successfully."
fi

log $YELLOW "Starting summarization job with progress tracking..."

# Generate a unique job ID for tracking
JOB_ID=$(uuidgen || date +%s)
log $YELLOW "Job ID: $JOB_ID"

# Start the summarization job
echo -n "Uploading video and starting job... "
RESPONSE=$(curl -s -X POST \
  -F "video=@$TEST_VIDEO_PATH" \
  -F "job_id=$JOB_ID" \
  -F "track_progress=true" \
  "http://localhost:$BACKEND_PORT/api/summarize")

if echo "$RESPONSE" | grep -q "error"; then
  echo "ERROR"
  log $RED "Failed to start job: $(echo $RESPONSE | grep -o '"error":"[^"]*"')"
  exit 1
else
  echo "SUCCESS"
  log $GREEN "Job started successfully. You can now view progress on the dashboard."
  log $GREEN "Dashboard URL: http://localhost:$DASHBOARD_PORT/dashboard/jobs"
fi

echo ""
log $YELLOW "Progress tracking steps:"
echo "1. Video Upload       - Uploading file to secure storage"
echo "2. Transcription      - Converting speech to text"
echo "3. Text Processing    - Analyzing and refining content"
echo "4. Summary Generation - Creating final summary"
echo "5. Completion         - Job finished successfully"
echo ""

log $YELLOW "Polling job status..."
echo ""

# Poll for job status
for ((i=1; i<=MAX_RETRIES; i++)); do
  echo "Checking job status (attempt $i of $MAX_RETRIES)..."
  
  STATUS_RESPONSE=$(curl -s "http://localhost:$BACKEND_PORT/api/jobs/$JOB_ID/status")
  
  if echo "$STATUS_RESPONSE" | grep -q "not found"; then
    log $YELLOW "Job not found yet. Waiting 2 seconds..."
  else
    PROGRESS=$(echo "$STATUS_RESPONSE" | grep -o '"progress":[0-9]*' | cut -d: -f2)
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    STAGE=$(echo "$STATUS_RESPONSE" | grep -o '"stage":"[^"]*"' | cut -d'"' -f4)
    
    echo "Current Status: $STATUS"
    echo "Current Stage: $STAGE"
    echo "Progress: $PROGRESS%"
    
    # Break if job is completed
    if [ "$STATUS" = "completed" ]; then
      break
    fi
  fi
  
  # Wait before next poll
  sleep 2
done

echo ""
log $GREEN "Job progress is now visible on the dashboard: http://localhost:$DASHBOARD_PORT/dashboard/jobs"
log $GREEN "You can reload the dashboard to see progress updates"
echo ""
log $YELLOW "Note: This script does not wait for the full job completion. Real jobs will progress"
log $YELLOW "through all stages automatically and can be monitored on the dashboard."

exit 0 