#!/usr/bin/env python3
"""
Test the transcription endpoint with a YouTube video
This script downloads a YouTube video, extracts the audio, and sends it to the transcription API
"""

import os
import sys
import json
import tempfile
import requests
import logging
import subprocess
import argparse
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default API URL
API_URL = "http://localhost:8080/api/transcribe"

def check_dependencies():
    """Check if required dependencies are installed"""
    # Check yt-dlp
    try:
        subprocess.run(["yt-dlp", "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        logger.info("yt-dlp is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("yt-dlp is not installed. Please install it with: pip install yt-dlp")
        return False
        
    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        logger.info("ffmpeg is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("ffmpeg is not installed. Please install it first.")
        return False
        
    return True

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if "youtu.be" in url:
        # Short URL format: https://youtu.be/VIDEO_ID
        path = urlparse(url).path
        return path.strip("/")
    elif "youtube.com" in url:
        # Regular URL format: https://www.youtube.com/watch?v=VIDEO_ID
        query = urlparse(url).query
        params = parse_qs(query)
        return params.get("v", [""])[0]
    else:
        # Direct ID or unknown format
        return url.strip()

def download_audio(youtube_url, output_path=None):
    """Download audio from YouTube URL"""
    if not output_path:
        # Create a temporary file with timestamp for uniqueness
        import time
        output_path = os.path.join(tempfile.gettempdir(), f"youtube_audio_{int(time.time())}.wav")
    
    logger.info(f"Downloading audio from YouTube URL: {youtube_url}")
    
    # Extract YouTube ID to verify it's a valid URL
    video_id = extract_youtube_id(youtube_url)
    if not video_id:
        logger.error("Invalid YouTube URL or ID")
        return None
    
    # Command to download audio with high quality and save as WAV
    cmd = [
        "yt-dlp",
        "-x",                          # Extract audio
        "--audio-format", "wav",       # Convert to WAV
        "--audio-quality", "0",        # Highest quality
        "-o", output_path,             # Output path
        "--postprocessor-args", "-ar 16000 -ac 1",  # Set audio rate and channels
        youtube_url
    ]
    
    logger.info(f"Running download command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(output_path):
            logger.info(f"Audio downloaded to: {output_path}")
            return output_path
        else:
            logger.error(f"Download command completed but output file not found: {output_path}")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading audio: {str(e)}")
        logger.error(f"yt-dlp stderr: {e.stderr.decode('utf-8', errors='replace')}")
        return None

def ensure_audio_format(audio_path):
    """Ensure audio format is compatible with speech recognition"""
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return None
        
    logger.info(f"Ensuring audio format is compatible with speech recognition: {audio_path}")
    
    # Create a temporary file for the processed audio
    fd, output_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Process audio with FFmpeg to ensure compatibility
    cmd = [
        "ffmpeg",
        "-i", audio_path,              # Input file
        "-vn",                         # No video
        "-acodec", "pcm_s16le",        # PCM 16-bit encoding (required by most speech recognition)
        "-ar", "16000",                # 16kHz sample rate
        "-ac", "1",                    # Mono channel
        "-y",                          # Overwrite if exists
        output_path                    # Output file
    ]
    
    logger.info(f"Processing audio with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Audio processed to: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error processing audio: {str(e)}")
        logger.error(f"ffmpeg stderr: {e.stderr.decode('utf-8', errors='replace')}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def transcribe_audio(audio_path, api_url=API_URL):
    """Send audio to the transcribe endpoint and get result"""
    logger.info(f"Sending audio to transcribe endpoint: {api_url}")
    
    # Skip authentication for development
    logger.info("Development mode: Skipping authentication step")
    
    with open(audio_path, "rb") as f:
        logger.info(f"Sending POST request to {api_url}")
        response = requests.post(
            api_url,
            files={"audio": (os.path.basename(audio_path), f, "audio/wav")},
            data={"playback_rate": "1.0"}
        )
    
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response content: {response.text[:500]}...")  # Show only first 500 chars
    
    return response

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test the transcription endpoint with a YouTube video")
    parser.add_argument("youtube_url", help="YouTube URL or video ID to transcribe")
    parser.add_argument("--api-url", default=API_URL, help="API URL for the transcription endpoint")
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    logger.info(f"Using API URL: {args.api_url}")
    
    # Download audio from YouTube
    audio_path = download_audio(args.youtube_url)
    if not audio_path:
        logger.error("Failed to download audio from YouTube")
        return 1
    
    # Process audio to ensure compatibility
    processed_audio = ensure_audio_format(audio_path)
    if not processed_audio:
        logger.error("Failed to process audio format")
        return 1
    
    # Send to transcription API
    try:
        response = transcribe_audio(processed_audio, args.api_url)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Transcription test successful!")
            
            # Print transcription
            logger.info("Transcription result:")
            logger.info("-" * 80)
            logger.info(result.get("transcription", "No transcription returned"))
            logger.info("-" * 80)
            
            # Also print to stdout without logging
            print("\nTranscription result:")
            print("-" * 80)
            print(result.get("transcription", "No transcription returned"))
            print("-" * 80)
            
            # Print summary
            logger.info("Summary result:")
            logger.info("-" * 80)
            logger.info(result.get("summary", "No summary returned"))
            logger.info("-" * 80)
            
            # Also print to stdout without logging
            print("\nSummary result:")
            print("-" * 80)
            print(result.get("summary", "No summary returned"))
            print("-" * 80)
            
        else:
            logger.error(f"Error response from API: {response.text}")
            return 1
    except Exception as e:
        logger.error(f"Error sending audio to transcribe endpoint: {str(e)}")
        return 1
    finally:
        # Clean up temporary files
        if 'processed_audio' in locals() and os.path.exists(processed_audio):
            os.remove(processed_audio)
            logger.info(f"Removed temporary audio file: {processed_audio}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 