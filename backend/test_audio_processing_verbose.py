#!/usr/bin/env python3

import os
import sys
import logging
import tempfile
import subprocess
import time
import signal
import threading
from app.summarizer.processor import process_audio
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_verbose.log"),
        logging.StreamHandler(sys.stdout)  # Add stdout handler
    ]
)
logger = logging.getLogger(__name__)

# Global timeout flag
timeout_occurred = False

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    global timeout_occurred
    timeout_occurred = True
    logger.error("TIMEOUT OCCURRED! Operation took too long.")
    print("\n\n*** TIMEOUT OCCURRED! Operation took too long. ***\n\n")

def set_timeout(seconds):
    """Set a timeout for the operation"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def clear_timeout():
    """Clear the timeout"""
    signal.alarm(0)

def create_test_audio():
    """Create a test audio file for testing"""
    logger.info("SKIPPING audio file creation with ffmpeg (using pre-created file)")
    print("SKIPPING audio file creation with ffmpeg (using pre-created file)")
    
    # Create a temporary file
    fd, audio_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Generate a simple WAV file programmatically
    try:
        # Create a very simple WAV file with minimal content
        with open(audio_path, 'wb') as f:
            # Write WAV header
            f.write(b'RIFF')
            f.write((36).to_bytes(4, byteorder='little'))  # File size - 8
            f.write(b'WAVE')
            
            # Write format chunk
            f.write(b'fmt ')
            f.write((16).to_bytes(4, byteorder='little'))  # Chunk size
            f.write((1).to_bytes(2, byteorder='little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, byteorder='little'))   # Num channels
            f.write((16000).to_bytes(4, byteorder='little'))  # Sample rate
            f.write((32000).to_bytes(4, byteorder='little'))  # Byte rate
            f.write((2).to_bytes(2, byteorder='little'))   # Block align
            f.write((16).to_bytes(2, byteorder='little'))  # Bits per sample
            
            # Write data chunk
            f.write(b'data')
            f.write((16).to_bytes(4, byteorder='little'))  # Chunk size
            
            # Write some sample data (silence)
            for i in range(8):
                f.write((0).to_bytes(2, byteorder='little'))
        
        logger.info(f"Created simple test audio file: {audio_path}")
        print(f"Created simple test audio file: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"Error creating test audio: {str(e)}")
        print(f"Error creating test audio: {str(e)}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

def print_separator():
    """Print a separator line"""
    separator = "=" * 80
    print(f"\n{separator}\n")
    logger.info(separator)

def test_audio_processing():
    """Test the audio processing functionality with verbose output"""
    print_separator()
    logger.info("Starting audio processing test with VERBOSE output")
    print("Starting audio processing test with VERBOSE output")
    print_separator()
    
    # Create a test audio file
    logger.debug("Creating test audio file...")
    print("Creating test audio file...")
    audio_path = create_test_audio()
    if not audio_path:
        logger.error("Failed to create test audio file")
        print("Failed to create test audio file")
        return False
    
    try:
        # Process the audio file with timeout
        logger.info("Processing audio file with 30-second timeout...")
        print("Processing audio file with 30-second timeout...")
        print_separator()
        
        # Set timeout (30 seconds)
        set_timeout(30)
        
        start_time = time.time()
        logger.debug("Calling process_audio()...")
        print("Calling process_audio()...")
        
        # Create a thread to print dots to show progress
        stop_progress = False
        def progress_indicator():
            i = 0
            while not stop_progress:
                if i % 10 == 0:
                    print(f"\nStill processing... {int(time.time() - start_time)}s elapsed", flush=True)
                print(".", end="", flush=True)
                i += 1
                time.sleep(1)
        
        progress_thread = threading.Thread(target=progress_indicator)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Call the actual processing function
        try:
            result = process_audio(audio_path)
        finally:
            # Stop the progress indicator
            stop_progress = True
            progress_thread.join(timeout=1.0)
        
        # Clear timeout
        clear_timeout()
        
        elapsed = time.time() - start_time
        logger.info(f"Audio processing completed in {elapsed:.2f} seconds")
        print(f"\nAudio processing completed in {elapsed:.2f} seconds")
        
        # Check for timeout
        if timeout_occurred:
            logger.error("Test failed due to timeout")
            print("Test failed due to timeout")
            return False
        
        print_separator()
        
        # Check the result
        if result['success']:
            logger.info("Audio processing successful!")
            print("Audio processing successful!")
            
            logger.info(f"Transcription: {result['transcription'][:100]}...")
            print(f"Transcription: {result['transcription'][:100]}...")
            
            logger.info(f"Summary: {result['summary'][:100]}...")
            print(f"Summary: {result['summary'][:100]}...")
            return True
        else:
            logger.warning(f"Audio processing failed: {result['error']}")
            print(f"Audio processing failed: {result['error']}")
            
            logger.warning(f"Error type: {result['error_type']}")
            print(f"Error type: {result['error_type']}")
            
            logger.warning(f"Details: {result['details']}")
            print(f"Details: {result['details']}")
            return False
    except Exception as e:
        # Clear timeout
        clear_timeout()
        
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed test audio file: {audio_path}")
            print(f"Removed test audio file: {audio_path}")

def main():
    """Main function"""
    print("\n\n")
    print("=" * 80)
    print("AUDIO PROCESSING TEST WITH VERBOSE OUTPUT")
    print("=" * 80)
    print("\n")
    
    logger.info("Starting audio processing tests with VERBOSE output")
    
    # Test audio processing
    success = test_audio_processing()
    
    print_separator()
    
    # Print the final result
    if success:
        logger.info("Audio processing test PASSED!")
        print("Audio processing test PASSED!")
        return 0
    else:
        logger.error("Audio processing test FAILED!")
        print("Audio processing test FAILED!")
        return 1

if __name__ == '__main__':
    # Set all loggers to DEBUG level
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.DEBUG)
    
    sys.exit(main()) 