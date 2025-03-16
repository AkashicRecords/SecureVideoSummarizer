#!/usr/bin/env python3
"""
Animated GIF demo generator for Secure Video Summarizer
This script creates animated GIFs showing the summarization process.
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
import logging
import tempfile
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gif_demo.log")
    ]
)

logger = logging.getLogger("gif_generator")

def check_dependencies():
    """Check if all required dependencies are installed."""
    dependencies = ["convert", "ffmpeg"]
    missing = []
    
    for dep in dependencies:
        try:
            subprocess.run(["which", dep], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            missing.append(dep)
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        print(f"Error: The following dependencies are required but not installed: {', '.join(missing)}")
        print("Please install the missing dependencies and try again.")
        print("- ImageMagick: for 'convert' command")
        print("- FFmpeg: for video processing")
        return False
    
    return True

def create_frames_from_terminal_output(script_path, video_path, output_dir, num_frames=20):
    """Create terminal output frames showing the summarization process."""
    logger.info(f"Creating frames from terminal output for {video_path}")
    
    # Create temporary directory for frames
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Set environment variable to control the speed of the demo script
    os.environ["DEMO_SPEED"] = "fast"
    
    # Start the script and capture its output
    process = subprocess.Popen(
        ["python", script_path, video_path, "--mode", "console"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Create frames directory
    frame_count = 0
    temp_file = os.path.join(output_dir, "terminal_output.txt")
    
    with open(temp_file, "w") as f:
        for line in process.stdout:
            f.write(line)
            f.flush()
            
            # Create a frame at regular intervals
            if frame_count % 5 == 0 and frame_count < num_frames * 5:
                frame_path = os.path.join(frames_dir, f"frame_{frame_count//5:04d}.png")
                
                # Use terminal to create an image of the current state
                terminal_cmd = [
                    "convert", "-size", "800x600", 
                    "xc:black", "-font", "Courier", "-pointsize", "14",
                    "-fill", "white", "-annotate", "+10+20", f"@{temp_file}",
                    frame_path
                ]
                
                try:
                    subprocess.run(terminal_cmd, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error creating frame: {e}")
            
            frame_count += 1
    
    process.wait()
    
    # If we have less frames than requested, create the remaining frames by copying the last one
    existing_frames = len([f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".png")])
    if existing_frames < num_frames:
        last_frame = os.path.join(frames_dir, f"frame_{existing_frames-1:04d}.png")
        if os.path.exists(last_frame):
            for i in range(existing_frames, num_frames):
                next_frame = os.path.join(frames_dir, f"frame_{i:04d}.png")
                shutil.copy(last_frame, next_frame)
    
    logger.info(f"Created {existing_frames} frames in {frames_dir}")
    return frames_dir

def create_simulated_ui_frames(video_path, output_dir, num_frames=30):
    """Create simulated UI frames showing the summarization process."""
    logger.info(f"Creating simulated UI frames for {video_path}")
    
    # Create frames directory
    frames_dir = os.path.join(output_dir, "ui_frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Extract a thumbnail from the video
    thumbnail_path = os.path.join(output_dir, "thumbnail.jpg")
    subprocess.run([
        "ffmpeg", "-i", video_path, "-ss", "00:00:05", "-vframes", "1",
        "-vf", "scale=320:-1", thumbnail_path
    ], check=True, capture_output=True)
    
    # Create a series of UI mockup frames showing the summarization process
    steps = [
        "Uploading video...",
        "Extracting audio...",
        "Transcribing audio...",
        "Validating transcription...",
        "Generating summary...",
        "Summary complete!"
    ]
    
    progress_values = [5, 20, 40, 60, 80, 100]
    
    for i, (step, progress) in enumerate(zip(steps, progress_values)):
        frame_count = i * (num_frames // len(steps))
        for j in range(num_frames // len(steps)):
            frame_path = os.path.join(frames_dir, f"frame_{frame_count + j:04d}.png")
            
            # Create a mockup UI frame
            progress_bar = "▓" * (progress // 5) + "░" * (20 - progress // 5)
            
            # Use ImageMagick to create a UI mockup
            ui_cmd = [
                "convert", "-size", "800x600", "xc:white",
                "-font", "Arial", "-pointsize", "24", "-fill", "black",
                "-annotate", "+20+40", "Secure Video Summarizer",
                "-font", "Arial", "-pointsize", "16", 
                "-annotate", "+20+80", f"Status: {step}",
                "-annotate", "+20+110", f"Progress: [{progress_bar}] {progress}%",
                "-font", "Courier", "-pointsize", "14",
            ]
            
            # Add the video thumbnail
            if os.path.exists(thumbnail_path):
                ui_cmd.extend([
                    "thumbnail.jpg", "-geometry", "320x180+20+140",
                    "-composite"
                ])
            
            # Add summary text for the last few frames
            if progress >= 80:
                summary_text = (
                    "SUMMARY:\n\n"
                    "The video discusses the key principles of data security.\n"
                    "Main points:\n"
                    "- Importance of encryption for sensitive data\n"
                    "- Regular security audits are essential\n"
                    "- User training reduces security incidents\n"
                    "- Multi-factor authentication is recommended\n"
                )
                ui_cmd.extend([
                    "-annotate", "+360+160", summary_text
                ])
            
            ui_cmd.append(frame_path)
            
            try:
                # Execute the command from the output directory to find the thumbnail
                current_dir = os.getcwd()
                os.chdir(output_dir)
                subprocess.run(ui_cmd, check=True, capture_output=True)
                os.chdir(current_dir)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error creating UI frame: {e}")
    
    logger.info(f"Created {num_frames} UI frames in {frames_dir}")
    return frames_dir

def create_animated_gif(frames_dir, output_path, delay=20):
    """Create an animated GIF from a directory of frames."""
    logger.info(f"Creating animated GIF from frames in {frames_dir}")
    
    # Get list of frames in order
    frames = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) 
                     if f.startswith("frame_") and f.endswith(".png")])
    
    if not frames:
        logger.error(f"No frames found in {frames_dir}")
        return False
    
    # Create animated GIF
    gif_cmd = ["convert", "-delay", str(delay), "-loop", "0"]
    gif_cmd.extend(frames)
    gif_cmd.append(output_path)
    
    try:
        subprocess.run(gif_cmd, check=True, capture_output=True)
        logger.info(f"Created animated GIF: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating animated GIF: {e}")
        return False

def create_demo_mp4(frames_dir, output_path, fps=10):
    """Create an MP4 video from a directory of frames."""
    logger.info(f"Creating MP4 video from frames in {frames_dir}")
    
    # Create MP4 video
    try:
        subprocess.run([
            "ffmpeg", "-framerate", str(fps), 
            "-pattern_type", "glob", "-i", os.path.join(frames_dir, "frame_*.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y",
            output_path
        ], check=True, capture_output=True)
        
        logger.info(f"Created MP4 video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating MP4 video: {e}")
        return False

def create_demo_assets(video_path, output_dir, mode="ui", create_mp4=True):
    """Create demo assets (GIF and optionally MP4) for the given video."""
    logger.info(f"Creating demo assets for {video_path} in {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create temp directory for frames
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create frames based on the mode
        if mode == "terminal":
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "create_demo_video.py")
            frames_dir = create_frames_from_terminal_output(script_path, video_path, temp_dir)
        else: # ui mode
            frames_dir = create_simulated_ui_frames(video_path, temp_dir)
        
        # Create animated GIF
        gif_path = os.path.join(output_dir, f"{video_name}_{mode}_{timestamp}.gif")
        success_gif = create_animated_gif(frames_dir, gif_path)
        
        # Create MP4 video if requested
        mp4_path = None
        if create_mp4:
            mp4_path = os.path.join(output_dir, f"{video_name}_{mode}_{timestamp}.mp4")
            success_mp4 = create_demo_mp4(frames_dir, mp4_path)
        else:
            success_mp4 = True
    
    return success_gif and success_mp4, gif_path, mp4_path if create_mp4 else None

def main():
    parser = argparse.ArgumentParser(description="Generate animated GIF demos for Secure Video Summarizer")
    parser.add_argument("video_path", help="Path to a video file to use as the basis for the demo")
    parser.add_argument("--output-dir", default="../docs/videos/demos", help="Output directory for demo files")
    parser.add_argument("--mode", choices=["ui", "terminal"], default="ui", help="Demo mode")
    parser.add_argument("--no-mp4", action="store_true", help="Don't create MP4 video (only GIF)")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    try:
        success, gif_path, mp4_path = create_demo_assets(
            args.video_path, args.output_dir, args.mode, not args.no_mp4
        )
        
        if success:
            print(f"\nDemo assets created successfully!")
            print(f"GIF: {gif_path}")
            if mp4_path:
                print(f"MP4: {mp4_path}")
            
            # Print file sizes
            gif_size = os.path.getsize(gif_path) / (1024 * 1024)
            print(f"GIF size: {gif_size:.2f} MB")
            
            if mp4_path and os.path.exists(mp4_path):
                mp4_size = os.path.getsize(mp4_path) / (1024 * 1024)
                print(f"MP4 size: {mp4_size:.2f} MB")
        else:
            print("\nFailed to create demo assets. Check the logs for details.")
            return 1
    except Exception as e:
        logger.exception("Error during demo asset creation")
        print(f"\nError during demo asset creation: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 