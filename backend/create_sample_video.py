#!/usr/bin/env python3
"""
Sample video generator for Secure Video Summarizer
This script creates a simple sample video with text for demo purposes.
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sample_video.log")
    ]
)

logger = logging.getLogger("sample_generator")

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("FFmpeg is not installed or not in PATH")
        print("Error: FFmpeg is required but not installed or not in PATH.")
        print("Please install FFmpeg and try again.")
        return False

def create_text_video(output_path, duration=30, width=1280, height=720, bg_color="black", text_color="white"):
    """Create a simple video with scrolling text about data security."""
    logger.info(f"Creating sample video: {output_path}")
    
    # Define the text content
    text_content = [
        "DATA SECURITY BEST PRACTICES",
        "",
        "1. Encryption of Sensitive Information",
        "   - Always encrypt data at rest and in transit",
        "   - Use strong encryption standards (AES-256)",
        "   - Manage encryption keys securely",
        "",
        "2. Regular Security Audits",
        "   - Conduct penetration testing quarterly",
        "   - Review access logs monthly",
        "   - Update security policies annually",
        "",
        "3. User Training and Awareness",
        "   - Train employees on security protocols",
        "   - Create awareness about phishing attacks",
        "   - Implement clear data handling procedures",
        "",
        "4. Multi-Factor Authentication",
        "   - Require MFA for all sensitive systems",
        "   - Use a combination of factors (knowledge, possession, inherence)",
        "   - Regularly rotate authentication credentials",
        "",
        "5. Data Minimization",
        "   - Collect only necessary information",
        "   - Establish data retention policies",
        "   - Properly dispose of unnecessary data"
    ]
    
    # Create a text file for FFmpeg
    text_file = "temp_text.txt"
    with open(text_file, "w") as f:
        f.write("\n".join(text_content))
    
    # Calculate font size based on video dimensions
    font_size = height // 20
    
    # Create the video using FFmpeg
    try:
        command = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color={bg_color}:s={width}x{height}:d={duration}",
            "-vf", (
                f"drawtext=fontfile=Arial:fontsize={font_size}:fontcolor={text_color}:x=(w-text_w)/2:"
                f"y=h-20*t:textfile={text_file}:line_spacing=8"
            ),
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-t", str(duration),
            output_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        logger.info(f"Sample video created successfully: {output_path}")
        
        # Clean up the temporary text file
        if os.path.exists(text_file):
            os.remove(text_file)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating sample video: {e}")
        print(f"Error creating sample video: {e}")
        return False

def create_test_video_suite(output_dir):
    """Create a suite of test videos with different durations."""
    logger.info(f"Creating test video suite in {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Create videos of different durations
    durations = [10, 30, 60]
    success = True
    
    for duration in durations:
        output_path = os.path.join(output_dir, f"sample_video_{duration}sec_{timestamp}.mp4")
        result = create_text_video(output_path, duration=duration)
        if not result:
            success = False
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Generate sample videos for testing")
    parser.add_argument("--output-dir", default="test_videos", help="Output directory for sample videos")
    parser.add_argument("--duration", type=int, default=30, help="Duration of the video in seconds")
    parser.add_argument("--suite", action="store_true", help="Create a suite of sample videos with different durations")
    
    args = parser.parse_args()
    
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        return 1
    
    try:
        if args.suite:
            if create_test_video_suite(args.output_dir):
                print(f"\nTest video suite created successfully in {args.output_dir}")
                return 0
            else:
                print("\nFailed to create test video suite. Check the logs for details.")
                return 1
        else:
            output_dir = args.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"sample_video_{args.duration}sec_{timestamp}.mp4")
            
            if create_text_video(output_path, duration=args.duration):
                print(f"\nSample video created successfully: {output_path}")
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"Video size: {file_size:.2f} MB")
                print(f"Duration: {args.duration} seconds")
                return 0
            else:
                print("\nFailed to create sample video. Check the logs for details.")
                return 1
    except Exception as e:
        logger.exception("Error during sample video creation")
        print(f"\nError during sample video creation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 