#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
import logging
import time
import tempfile
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_extract.log')
    ]
)

logger = logging.getLogger("video_extract")

def extract_video_segment(video_path, output_dir, duration=30, start_time=0):
    """Extract a segment from the video"""
    print(f"Extracting {duration} second segment from video starting at {start_time}s...")
    
    # Create output filename
    timestamp = int(time.time())
    output_filename = f"segment_{timestamp}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', str(start_time),  # Start time
        '-t', str(duration),     # Duration
        '-c:v', 'copy',          # Copy video codec
        '-c:a', 'copy',          # Copy audio codec
        output_path,
        '-y'                     # Overwrite if exists
    ]
    
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"Error extracting segment: {result.stderr}")
            return None
        
        print(f"Successfully extracted segment to {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        print("FFmpeg process timed out!")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None
    except Exception as e:
        print(f"Error in extract_video_segment: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def extract_audio(video_path, output_dir):
    """Extract audio from the video file"""
    print(f"Extracting audio from video: {video_path}")
    
    # Create output filename
    timestamp = int(time.time())
    output_filename = f"audio_{timestamp}.wav"
    output_path = os.path.join(output_dir, output_filename)
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',                # No video
        '-acodec', 'pcm_s16le', # PCM 16-bit encoding
        '-ar', '16000',       # 16kHz sample rate
        '-ac', '1',           # Mono channel
        output_path,
        '-y'                  # Overwrite if exists
    ]
    
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"Error extracting audio: {result.stderr}")
            return None
        
        print(f"Successfully extracted audio to {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        print("FFmpeg process timed out!")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None
    except Exception as e:
        print(f"Error in extract_audio: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def get_video_info(video_path):
    """Get information about the video file"""
    print(f"Getting information about video: {video_path}")
    
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration,size',
        '-show_streams',
        '-of', 'json',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Error getting video info: {result.stderr}")
            return None
        
        print(f"Video info: {result.stdout[:200]}...")
        return result.stdout
    except Exception as e:
        print(f"Error in get_video_info: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Video extraction test")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--output_dir", default="extracted_segments", help="Directory to save extracted segments")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds to extract")
    parser.add_argument("--start_time", type=int, default=0, help="Start time in seconds")
    parser.add_argument("--extract_audio", action="store_true", help="Extract audio from the video")
    parser.add_argument("--info_only", action="store_true", help="Only show video information")
    args = parser.parse_args()
    
    # Check if video file exists
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return 1
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created output directory: {args.output_dir}")
    
    print("\n===================================================")
    print(f"PROCESSING VIDEO: {args.video_path}")
    print(f"Output directory: {args.output_dir}")
    print("===================================================\n")
    
    try:
        # Get video information
        video_info = get_video_info(args.video_path)
        if not video_info:
            print("Failed to get video information. Exiting.")
            return 1
        
        if args.info_only:
            print("Info only mode - exiting.")
            return 0
        
        # Extract video segment
        segment_path = extract_video_segment(
            args.video_path, 
            args.output_dir, 
            duration=args.duration, 
            start_time=args.start_time
        )
        
        if not segment_path:
            print("Failed to extract segment. Exiting.")
            return 1
        
        # Extract audio if requested
        if args.extract_audio:
            audio_path = extract_audio(segment_path, args.output_dir)
            if not audio_path:
                print("Failed to extract audio. Exiting.")
                return 1
            print(f"Audio extraction successful: {audio_path}")
        
        print("\n===================================================")
        print("EXTRACTION SUCCESSFUL")
        print(f"Video segment: {segment_path}")
        if args.extract_audio:
            print(f"Audio file: {audio_path}")
        print("===================================================\n")
        
        return 0
        
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 