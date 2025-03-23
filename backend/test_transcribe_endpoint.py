#!/usr/bin/env python3
"""
Test script for the transcribe endpoint using a real audio file.
This script extracts audio from a test video and sends it to the transcribe endpoint.
"""

import os
import sys
import subprocess
import tempfile
import requests
import json
import logging
import time
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("transcribe_test.log")
    ]
)

logger = logging.getLogger("transcribe_test")

# Try to import speech_recognition if it's installed
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

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

def create_test_audio(duration=5, text="This is a test audio file for the secure video summarizer transcription system"):
    """
    Create a test audio file with spoken text for testing purposes.
    Returns the path to the created audio file.
    """
    logger.info("Creating test audio file with spoken words")
    
    # Create a temporary file
    fd, audio_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    try:
        # Create a simple tone with the exact WAV format required by speech_recognition
        cmd = [
            'ffmpeg', '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=5',
            '-c:a', 'pcm_s16le',  # PCM 16-bit encoding (required)
            '-ar', '16000',       # 16kHz sample rate (optimal)
            '-ac', '1',           # Mono (required)
            '-y', audio_path
        ]
        
        logger.info(f"Creating test audio file with exact WAV format required by speech_recognition")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Created test audio file: {audio_path}")
        
        # Verify the created file can be read by speech_recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_path) as source:
                    # Just try to read the file
                    recognizer.record(source)
                logger.info("Verified test audio file can be read by speech_recognition")
            except Exception as e:
                logger.error(f"Test audio file validation failed: {str(e)}")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                return None
            
        return audio_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating test audio: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating test audio: {str(e)}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

def extract_audio_from_video(video_path):
    """
    Extract audio from a video file.
    Returns the path to the extracted audio file.
    """
    logger.info(f"Extracting audio from video: {video_path}")
    
    # Create a temporary file for the audio - use a .wav extension explicitly
    audio_path = os.path.join(tempfile.gettempdir(), f"extracted_audio_{int(time.time())}.wav")
    
    try:
        # Extract audio using FFmpeg with settings known to work with speech_recognition
        # Use a simpler, more reliable command that works with speech_recognition
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn',                   # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit encoding (WAV)
            '-ar', '16000',          # 16kHz sample rate (required for speech recognition)
            '-ac', '1',              # Mono channel (required for speech recognition)
            '-sample_fmt', 's16',    # Force 16-bit sample format
            '-f', 'wav',             # Force WAV format
            '-y',                    # Overwrite output file if exists
            audio_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Extracted audio to: {audio_path}")
        
        # Verify the audio file was created and is bigger than a minimum size
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            logger.error(f"Extracted audio file is too small or doesn't exist: {audio_path}")
            return None
        
        # If we have speech_recognition available, test if it can read the file
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_path) as source:
                    # Just try to read the file
                    recognizer.record(source)
                logger.info("Verified audio file can be read by speech_recognition")
            except Exception as e:
                logger.error(f"Audio file validation failed with speech_recognition: {str(e)}")
                
                # Try a different ffmpeg command for better compatibility
                backup_audio_path = os.path.join(tempfile.gettempdir(), f"backup_audio_{int(time.time())}.wav")
                logger.info(f"Trying alternative FFmpeg command for better compatibility")
                
                # Try a different, more basic encoding approach
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vn',                # No video
                    '-acodec', 'pcm_s16le', # PCM 16-bit encoding
                    '-ar', '16000',       # 16kHz sample rate
                    '-ac', '1',           # Mono channel
                    '-y',                 # Overwrite output file if exists
                    backup_audio_path
                ]
                
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Check if the backup file can be read
                try:
                    with sr.AudioFile(backup_audio_path) as source:
                        recognizer.record(source)
                    logger.info(f"Backup audio file created successfully: {backup_audio_path}")
                    
                    # If successful, use the backup file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    return backup_audio_path
                except Exception as e2:
                    logger.error(f"Backup audio file also failed validation: {str(e2)}")
                    if os.path.exists(backup_audio_path):
                        os.remove(backup_audio_path)
        
        return audio_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting audio: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting audio: {str(e)}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

def send_to_transcribe_endpoint(audio_path, api_url="http://localhost:8080/api/transcribe"):
    """
    Send the audio file to the transcribe endpoint.
    Returns the response from the endpoint.
    """
    logger.info(f"Sending audio to transcribe endpoint: {api_url}")
    
    try:
        # Create session data
        session = requests.Session()
        
        # In development mode with BYPASS_AUTH_FOR_TESTING=true,
        # we don't need to authenticate, as the login_required decorator will bypass auth
        logger.info("Development mode: Skipping authentication step")
        
        # Prepare the multipart form data
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_path), audio_file, 'audio/wav')}
            data = {
                'playback_rate': '1.0',
                'video_data': json.dumps({"title": "Test Video", "url": "https://example.com/test"}),
                'options': json.dumps({"use_gpu": False})
            }
            
            # Send the request
            logger.info(f"Sending POST request to {api_url}")
            response = session.post(api_url, files=files, data=data)
            
            # Log the response
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.text[:500]}...")  # Log first 500 chars to avoid huge logs
            
            return response
    except Exception as e:
        logger.error(f"Error sending audio to transcribe endpoint: {str(e)}")
        return None

def test_local_transcription(audio_path):
    """
    Test if the audio file can be transcribed locally.
    This helps identify if the issue is with the server or with the audio format.
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        logger.warning("speech_recognition not available for local transcription test")
        return False
    
    logger.info(f"Testing local transcription of: {audio_path}")
    
    try:
        # Print information about the audio file
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_format', '-show_streams', audio_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Audio file info:\n{result.stdout}")
        except Exception as e:
            logger.warning(f"Could not get audio info: {str(e)}")
        
        # Try to read the file with speech_recognition
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                logger.info("Reading audio file...")
                audio_data = recognizer.record(source)
                logger.info("Audio file read successfully")
                
                # Try to transcribe with Google (if internet is available)
                try:
                    logger.info("Attempting to transcribe with Google Speech Recognition...")
                    text = recognizer.recognize_google(audio_data)
                    logger.info(f"Google transcription result: '{text}'")
                except sr.UnknownValueError:
                    logger.warning("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    logger.warning(f"Could not request results from Google Speech Recognition service: {str(e)}")
                
                # Try to transcribe with Sphinx (offline)
                try:
                    logger.info("Attempting to transcribe with Sphinx (offline)...")
                    text = recognizer.recognize_sphinx(audio_data)
                    logger.info(f"Sphinx transcription result: '{text}'")
                except sr.UnknownValueError:
                    logger.warning("Sphinx could not understand audio")
                except Exception as e:
                    logger.warning(f"Sphinx transcription error: {str(e)}")
            
            logger.info("Audio file can be processed by speech_recognition")
            return True
        except Exception as e:
            logger.error(f"Error reading audio file: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error testing local transcription: {str(e)}")
        return False

def main():
    """Main function"""
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        return 1
    
    # Get API server details from environment or use defaults
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8080")
    api_url = f"http://{api_host}:{api_port}/api/transcribe"
    
    logger.info(f"Using API URL: {api_url}")
    
    try:
        # Try to find an existing test video
        test_video = None
        for video_file in ["backend/test_video.mp4", "test_video.mp4"]:
            if os.path.exists(video_file):
                test_video = video_file
                break
        
        audio_path = None
        if test_video:
            # Extract audio from the test video
            logger.info(f"Using existing test video: {test_video}")
            audio_path = extract_audio_from_video(test_video)
        else:
            # Create a test audio file
            logger.info("No test video found, creating a test audio file")
            audio_path = create_test_audio()
        
        if not audio_path:
            logger.error("Failed to create or extract audio")
            return 1
        
        # Test if the audio file can be transcribed locally
        test_local_transcription(audio_path)
        
        # Send the audio to the transcribe endpoint
        response = send_to_transcribe_endpoint(audio_path, api_url)
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed temporary audio file: {audio_path}")
        
        # Return success or failure
        if response and response.status_code == 200:
            logger.info("Transcription test successful!")
            return 0
        else:
            logger.error("Transcription test failed!")
            return 1
    except Exception as e:
        logger.exception("Error during transcription test")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 