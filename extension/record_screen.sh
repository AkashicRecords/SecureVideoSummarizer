#!/bin/bash

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: FFmpeg is not installed. Please install it first."
    echo "On macOS: brew install ffmpeg"
    echo "On Ubuntu/Debian: sudo apt-get install ffmpeg"
    exit 1
fi

# Set output file name and duration
OUTPUT="screen_recording_$(date +%Y%m%d_%H%M%S).mp4"
DURATION=60  # Duration in seconds

# Start recording the screen
echo "Recording screen for $DURATION seconds..."
ffmpeg -f avfoundation -framerate 30 -i "0" -t $DURATION -c:v libx264 -pix_fmt yuv420p "$OUTPUT"

echo "Screen recording saved as $OUTPUT"
