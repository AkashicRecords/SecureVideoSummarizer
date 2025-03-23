#!/usr/bin/env python3
"""
Demo Generator for Secure Video Summarizer
This script manages the entire demo generation process.
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("demo_generation.log")
    ]
)

logger = logging.getLogger("demo_generator")

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
VIDEOS_DIR = os.path.join(DOCS_DIR, "videos")
DEMOS_DIR = os.path.join(VIDEOS_DIR, "demos")
TEST_VIDEOS_DIR = os.path.join(PROJECT_ROOT, "test_videos")

# Create necessary directories
os.makedirs(TEST_VIDEOS_DIR, exist_ok=True)
os.makedirs(DEMOS_DIR, exist_ok=True)
os.makedirs(os.path.join(VIDEOS_DIR, "overview"), exist_ok=True)
os.makedirs(os.path.join(VIDEOS_DIR, "tutorials"), exist_ok=True)
os.makedirs(os.path.join(VIDEOS_DIR, "features"), exist_ok=True)

def check_dependencies():
    """Check if all required dependencies are installed."""
    dependencies = {
        "ffmpeg": "FFmpeg is required for video processing",
        "convert": "ImageMagick is required for GIF creation"
    }
    
    missing = []
    for dep, message in dependencies.items():
        try:
            subprocess.run(["which", dep], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            missing.append((dep, message))
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(d[0] for d in missing)}")
        print("Error: Missing required dependencies:")
        for dep, msg in missing:
            print(f"- {dep}: {msg}")
        return False
    
    return True

def run_script(script_name, args=None):
    """Run a Python script with the given arguments."""
    if args is None:
        args = []
    
    script_path = os.path.join(SCRIPT_DIR, script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        cmd = [sys.executable, script_path] + args
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Script completed successfully: {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script {script_name}: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False

def create_sample_videos():
    """Create sample videos for demos."""
    logger.info("Creating sample videos...")
    
    # Create a short sample video for demos
    success = run_script("create_sample_video.py", [
        "--output-dir", TEST_VIDEOS_DIR,
        "--duration", "15"
    ])
    
    if not success:
        return None
    
    # Find the most recent sample video
    videos = [os.path.join(TEST_VIDEOS_DIR, f) for f in os.listdir(TEST_VIDEOS_DIR) 
              if f.startswith("sample_video_") and f.endswith(".mp4")]
    
    if not videos:
        logger.error("No sample videos found")
        return None
    
    # Sort by creation time and get the most recent
    videos.sort(key=os.path.getmtime, reverse=True)
    return videos[0]

def create_animated_demos(video_path):
    """Create animated demos using the sample video."""
    if not video_path or not os.path.exists(video_path):
        logger.error(f"Invalid or non-existent video path: {video_path}")
        return False
    
    logger.info(f"Creating animated demos for {video_path}...")
    
    # Create a console-based animated GIF
    console_success = run_script("create_gif_demo.py", [
        video_path,
        "--output-dir", os.path.join(VIDEOS_DIR, "overview"),
        "--mode", "terminal"
    ])
    
    # Create a UI-based animated GIF
    ui_success = run_script("create_gif_demo.py", [
        video_path,
        "--output-dir", os.path.join(VIDEOS_DIR, "features"),
        "--mode", "ui"
    ])
    
    return console_success and ui_success

def create_console_demo(video_path):
    """Create a console-based demo video."""
    if not video_path or not os.path.exists(video_path):
        logger.error(f"Invalid or non-existent video path: {video_path}")
        return False
    
    logger.info(f"Creating console demo for {video_path}...")
    
    # Run the demo video script
    success = run_script("create_demo_video.py", [
        video_path,
        "--output-dir", os.path.join(VIDEOS_DIR, "tutorials"),
        "--mode", "console"
    ])
    
    return success

def update_readme_with_demo_links():
    """Update the README.md file with links to demo videos."""
    logger.info("Updating README.md with demo links...")
    
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    if not os.path.exists(readme_path):
        logger.error(f"README.md not found at {readme_path}")
        return False
    
    # Find demo videos
    demo_files = []
    for root, _, files in os.walk(VIDEOS_DIR):
        for file in files:
            if file.endswith(".gif") or file.endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(root, file), PROJECT_ROOT)
                demo_files.append(rel_path)
    
    if not demo_files:
        logger.warning("No demo videos found")
        return False
    
    # Read current README
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Check if demos section already exists
    if "## Demos" in content:
        logger.info("Demos section already exists in README.md")
        return True
    
    # Find the right location to add the demos section (after Project Overview)
    if "## Project Overview" in content:
        parts = content.split("## Project Overview", 1)
        
        # Find the next section after Project Overview
        next_section_match = parts[1].find("\n## ")
        if next_section_match >= 0:
            insert_point = next_section_match + 1
            new_content = (
                parts[0] + 
                "## Project Overview" + 
                parts[1][:insert_point] +
                "\n## Demos\n\n"
                "Check out these demos of the Secure Video Summarizer in action:\n\n"
            )
            
            # Add links to GIFs with thumbnails
            gifs = [f for f in demo_files if f.endswith(".gif")]
            if gifs and len(gifs) <= 3:  # Only include up to 3 GIFs directly
                for gif in gifs[:3]:
                    gif_name = os.path.basename(gif).replace("_", " ").replace(".gif", "")
                    new_content += f"<div align='center'>\n"
                    new_content += f"  <p><strong>{gif_name.title()}</strong></p>\n"
                    new_content += f"  <img src='{gif}' alt='{gif_name}' width='600'/>\n"
                    new_content += f"</div>\n\n"
            
            # Add links to all demos in the docs
            new_content += f"For more demos and tutorials, see the [documentation](docs/demo_videos.md).\n\n"
            
            new_content += parts[1][insert_point:]
            
            # Write the updated README
            with open(readme_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Updated README.md with demo links")
            return True
    
    logger.warning("Could not find appropriate location to add demos section in README.md")
    return False

def main():
    parser = argparse.ArgumentParser(description="Generate demos for Secure Video Summarizer")
    parser.add_argument("--video-path", help="Path to an existing video file to use for demos")
    parser.add_argument("--skip-sample", action="store_true", help="Skip sample video creation")
    parser.add_argument("--skip-readme", action="store_true", help="Skip updating README.md")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    video_path = args.video_path
    
    # Create sample videos if needed
    if not args.skip_sample and not video_path:
        print("\n=== Creating Sample Videos ===")
        video_path = create_sample_videos()
        if not video_path:
            print("Failed to create sample videos. Aborting.")
            return 1
        print(f"Sample video created: {video_path}")
    
    # Verify video path
    if not video_path or not os.path.exists(video_path):
        print("Error: No valid video path provided. Use --video-path or allow sample creation.")
        return 1
    
    # Create animated demos
    print("\n=== Creating Animated Demos ===")
    if create_animated_demos(video_path):
        print("Animated demos created successfully!")
    else:
        print("Failed to create some animated demos.")
        # Continue with other steps
    
    # Create console demo
    print("\n=== Creating Console Demo ===")
    if create_console_demo(video_path):
        print("Console demo created successfully!")
    else:
        print("Failed to create console demo.")
        # Continue with other steps
    
    # Update README.md
    if not args.skip_readme:
        print("\n=== Updating README.md ===")
        if update_readme_with_demo_links():
            print("README.md updated with demo links!")
        else:
            print("Failed to update README.md with demo links.")
    
    print("\n=== Demo Generation Complete ===")
    print(f"Demo videos are available in: {VIDEOS_DIR}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 