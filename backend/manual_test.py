#!/usr/bin/env python3

import os
import sys
import logging
import tempfile
import time
from app.summarizer.processor import process_audio
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_audio():
    """Create a test audio file for testing"""
    # Create a temporary file
    fd, audio_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Write some dummy content to the file
    with open(audio_path, 'wb') as f:
        f.write(b'dummy audio content' * 1000)  # Make it large enough to pass size check
    
    return audio_path

def test_audio_processing():
    """Test the audio processing functionality"""
    logger.info("Starting manual audio processing test")
    
    # Create a test audio file
    audio_path = create_test_audio()
    logger.info(f"Created test audio file: {audio_path}")
    
    try:
        # Process the audio file
        logger.info("Processing audio file...")
        start_time = time.time()
        result = process_audio(audio_path)
        elapsed = time.time() - start_time
        logger.info(f"Audio processing completed in {elapsed:.2f} seconds")
        
        # Check the result
        if result['success']:
            logger.info("Audio processing successful!")
            logger.info(f"Transcription: {result['transcription'][:100]}...")
            logger.info(f"Summary: {result['summary'][:100]}...")
        else:
            logger.warning(f"Audio processing failed: {result['error']}")
            logger.warning(f"Error type: {result['error_type']}")
            logger.warning(f"Details: {result['details']}")
        
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed test audio file: {audio_path}")

def main():
    """Main function"""
    logger.info("Starting manual tests")
    
    # Test audio processing
    result = test_audio_processing()
    
    # Print the final result
    if result and result['success']:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 