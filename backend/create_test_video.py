#!/usr/bin/env python
"""
Create a test video file for testing the summarization API.
This script generates a simple video with colored frames and text.
"""

import os
import sys
import numpy as np
import time
from datetime import datetime
import argparse

try:
    import cv2
except ImportError:
    print("OpenCV (cv2) is required. Install with: pip install opencv-python")
    sys.exit(1)

def create_test_video(output_path, duration=10, fps=25, resolution=(640, 480)):
    """Create a test video file with colored frames and text."""
    width, height = resolution
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    
    # Colors to cycle through (BGR format)
    colors = [
        (0, 0, 255),    # Red
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (255, 255, 0)   # Cyan
    ]
    
    print(f"Creating {duration} second test video at {output_path}...")
    
    # Total frames to generate
    total_frames = duration * fps
    start_time = time.time()
    
    for i in range(total_frames):
        # Create a colored frame
        color_idx = (i // (fps * 2)) % len(colors)  # Change color every 2 seconds
        frame = np.zeros((height, width, 3), np.uint8)
        frame[:] = colors[color_idx]
        
        # Add frame counter and timestamp text
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        frame_text = f"Frame: {i}/{total_frames}"
        progress = f"Progress: {i / total_frames * 100:.1f}%"
        
        cv2.putText(frame, frame_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2)
        cv2.putText(frame, timestamp, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2)
        cv2.putText(frame, progress, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2)
        
        # Write the frame
        out.write(frame)
        
        # Print progress
        if i % fps == 0:
            sys.stdout.write(f"\rGenerating: {i / total_frames * 100:.1f}%")
            sys.stdout.flush()
    
    # Release the VideoWriter
    out.release()
    
    elapsed = time.time() - start_time
    print(f"\nVideo created successfully in {elapsed:.2f} seconds")
    print(f"Video saved to: {os.path.abspath(output_path)}")
    
    # Return video metadata
    return {
        "path": os.path.abspath(output_path),
        "duration": duration,
        "resolution": resolution,
        "fps": fps,
        "size_bytes": os.path.getsize(output_path)
    }

def main():
    parser = argparse.ArgumentParser(description="Create a test video for API testing")
    parser.add_argument("--output", default="backend/uploads/videos/test_video.mp4", 
                        help="Output video file path")
    parser.add_argument("--duration", type=int, default=10, 
                        help="Video duration in seconds")
    parser.add_argument("--fps", type=int, default=25, 
                        help="Frames per second")
    parser.add_argument("--width", type=int, default=640, 
                        help="Video width in pixels")
    parser.add_argument("--height", type=int, default=480, 
                        help="Video height in pixels")
    
    args = parser.parse_args()
    
    # Create the test video
    video_info = create_test_video(
        args.output,
        duration=args.duration,
        fps=args.fps,
        resolution=(args.width, args.height)
    )
    
    # Print video information
    print("\nVideo Information:")
    print(f"Duration: {video_info['duration']} seconds")
    print(f"Resolution: {video_info['resolution'][0]}x{video_info['resolution'][1]}")
    print(f"FPS: {video_info['fps']}")
    print(f"Size: {video_info['size_bytes'] / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main() 