#!/bin/bash

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "Error: ImageMagick is not installed. Please install it first."
    echo "On macOS: brew install imagemagick"
    echo "On Ubuntu/Debian: sudo apt-get install imagemagick"
    exit 1
fi

# Source JPG file
SOURCE="icons/SVS.jpg"

# Check if source file exists
if [ ! -f "$SOURCE" ]; then
    echo "Error: Source file $SOURCE not found."
    exit 1
fi

# Create icons directory if it doesn't exist
mkdir -p icons

# Generate icons in different sizes
echo "Generating icons from $SOURCE..."

# Extension icons
convert "$SOURCE" -resize 16x16 "icons/SVS-16.png"
convert "$SOURCE" -resize 32x32 "icons/SVS-32.png"
convert "$SOURCE" -resize 48x48 "icons/SVS-48.png"
convert "$SOURCE" -resize 128x128 "icons/SVS-128.png"

# Application icons
convert "$SOURCE" -resize 256x256 "icons/SVS-256.png"
convert "$SOURCE" -resize 512x512 "icons/SVS-512.png"

# macOS specific icons
convert "$SOURCE" -resize 1024x1024 "icons/SVS-1024.png"
convert "icons/SVS-1024.png" -alpha set -background none \
        \( -clone 0 -resize 16x16 \) \
        \( -clone 0 -resize 32x32 \) \
        \( -clone 0 -resize 64x64 \) \
        \( -clone 0 -resize 128x128 \) \
        \( -clone 0 -resize 256x256 \) \
        \( -clone 0 -resize 512x512 \) \
        \( -clone 0 -resize 1024x1024 \) \
        -delete 0 "icons/SVS.icns"

# Windows specific icon
convert "icons/SVS-256.png" "icons/SVS.ico"

echo "Icons generated successfully!"
echo "Extension icons:"
echo "- icons/SVS-16.png"
echo "- icons/SVS-32.png"
echo "- icons/SVS-48.png"
echo "- icons/SVS-128.png"
echo "Application icons:"
echo "- icons/SVS-256.png"
echo "- icons/SVS-512.png"
echo "- icons/SVS-1024.png"
echo "Platform-specific icons:"
echo "- icons/SVS.icns (macOS)"
echo "- icons/SVS.ico (Windows)"
