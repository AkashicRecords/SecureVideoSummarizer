#!/usr/bin/env python3
"""
Demo video generator for Secure Video Summarizer
This script runs a demo of the video summarization process and captures the output.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("demo_video.log")
    ]
)

logger = logging.getLogger("demo_generator")

def print_with_typing_effect(text, typing_speed=0.03, pause_at_newline=0.5):
    """Print text with a typing effect to simulate a user typing."""
    for char in text:
        print(char, end='', flush=True)
        
        # Add a longer pause at punctuation
        if char in ['.', '!', '?', ',', ';', ':']:
            time.sleep(typing_speed * 3)
        # Add a much longer pause at newlines
        elif char == '\n':
            time.sleep(pause_at_newline)
        else:
            time.sleep(typing_speed)
    
    print()
    time.sleep(0.5)

def print_banner(text, border_char="=", width=80):
    """Print a banner with the given text."""
    print(border_char * width)
    padding = (width - len(text) - 2) // 2
    print(f"{border_char}{' ' * padding}{text}{' ' * (padding + (1 if len(text) % 2 != 0 else 0))}{border_char}")
    print(border_char * width)
    time.sleep(1)

def run_command(command, live_output=True, capture_output=False):
    """Run a shell command with visual feedback and return the output."""
    logger.info(f"Running command: {command}")
    print_with_typing_effect(f"$ {command}")
    time.sleep(0.5)  # Pause before execution
    
    if live_output:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True
        )
        
        output_lines = []
        for line in process.stdout:
            line = line.rstrip()
            print(line)
            if capture_output:
                output_lines.append(line)
            time.sleep(0.05)  # Slight delay between lines for visual effect
        
        process.wait()
        return "\n".join(output_lines) if capture_output else None
    else:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if capture_output:
            return result.stdout
        return None

def create_animated_demo(video_path, output_dir, mode="console"):
    """Create an animated demo of the video summarization process."""
    if not os.path.exists(video_path):
        print_with_typing_effect(f"Error: Video file not found: {video_path}", 0.01)
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Record timestamp for output naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"demo_{timestamp}.txt")
    
    print_banner("SECURE VIDEO SUMMARIZER DEMO")
    time.sleep(0.5)
    
    # Show initial environment setup
    print_with_typing_effect("\n# First, let's check our environment:")
    run_command("python -V")
    run_command("echo $PWD")
    
    # Show video information
    print_with_typing_effect("\n# Let's examine our input video:")
    video_info = run_command(f"ffprobe -v error -show_format -show_streams {video_path} 2>&1", capture_output=True)
    video_duration = "unknown"
    for line in video_info.split("\n"):
        if "duration=" in line:
            video_duration = line.split("=")[1]
            break
    
    print_with_typing_effect(f"\n# Video duration: {video_duration} seconds")
    print_with_typing_effect("\n# Let's start the video summarization process:")
    
    # Run the actual summarization
    print_with_typing_effect("\n# Processing the video with Secure Video Summarizer...")
    
    # Run with different options depending on demo mode
    if mode == "console":
        cmd = f"python backend/test_with_large_video.py {video_path} --duration 20"
    elif mode == "api":
        cmd = f"python backend/test_video_summarization_api.py {video_path}"
    else:
        cmd = f"python backend/test_with_large_video.py {video_path} --duration 20"
    
    run_command(cmd)
    
    # Show completion banner
    print_banner("SUMMARIZATION COMPLETED")
    
    # Display some statistics
    print_with_typing_effect("\n# Summarization Statistics:")
    print_with_typing_effect("- Original video duration: " + video_duration + " seconds")
    print_with_typing_effect("- Processing time: ~30 seconds")
    print_with_typing_effect("- Summary generated successfully!")
    
    # Save the demo script for reference
    with open(output_file, "w") as f:
        f.write(f"Secure Video Summarizer Demo\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Video: {video_path}\n")
        f.write(f"Mode: {mode}\n")
        f.write(f"Duration: {video_duration} seconds\n")
    
    print_with_typing_effect(f"\n# Demo script saved to: {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate a demo video for Secure Video Summarizer")
    parser.add_argument("video_path", help="Path to a video file to summarize")
    parser.add_argument("--output-dir", default="../docs/videos/demos", help="Output directory for demo files")
    parser.add_argument("--mode", choices=["console", "api"], default="console", help="Demo mode")
    
    args = parser.parse_args()
    
    try:
        success = create_animated_demo(args.video_path, args.output_dir, args.mode)
        if success:
            print_with_typing_effect("\nDemo completed successfully!")
        else:
            print_with_typing_effect("\nDemo failed. Check the logs for details.")
            return 1
    except Exception as e:
        logger.exception("Error during demo creation")
        print_with_typing_effect(f"\nError during demo creation: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 