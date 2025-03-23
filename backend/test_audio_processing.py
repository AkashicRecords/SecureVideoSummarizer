#!/usr/bin/env python3

import os
import sys
import logging
import tempfile
import subprocess
import time
from app.summarizer.processor import process_audio
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError

# Configure logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_audio():
    """Create a test audio file for testing using ffmpeg"""
    logger.debug("Starting to create test audio file")
    # Create a temporary file
    fd, audio_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    try:
        # Generate a 3-second sine wave audio file
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', 
            '-ar', '16000', '-ac', '1', audio_path
        ]
        
        logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Created test audio file: {audio_path}")
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

def test_audio_processing():
    """Test the audio processing functionality"""
    logger.info("Starting audio processing test")
    
    # Create a test audio file
    logger.debug("Calling create_test_audio()")
    audio_path = create_test_audio()
    if not audio_path:
        logger.error("Failed to create test audio file")
        return False
    
    try:
        # Process the audio file
        logger.info("Processing audio file...")
        start_time = time.time()
        logger.debug("Calling process_audio()")
        result = process_audio(audio_path)
        elapsed = time.time() - start_time
        logger.info(f"Audio processing completed in {elapsed:.2f} seconds")
        
        # Check the result
        if result['success']:
            logger.info("Audio processing successful!")
            logger.info(f"Transcription: {result['transcription'][:100]}...")
            logger.info(f"Summary: {result['summary'][:100]}...")
            return True
        else:
            logger.warning(f"Audio processing failed: {result['error']}")
            logger.warning(f"Error type: {result['error_type']}")
            logger.warning(f"Details: {result['details']}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed test audio file: {audio_path}")

def main():
    """Main function"""
    logger.info("Starting audio processing tests")
    
    # Test audio processing
    success = test_audio_processing()
    
    # Print the final result
    if success:
        logger.info("Audio processing test passed!")
        return 0
    else:
        logger.error("Audio processing test failed!")
        return 1

if __name__ == '__main__':
    # Set all loggers to DEBUG level
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.DEBUG)
    
    sys.exit(main()) 