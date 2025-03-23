#!/usr/bin/env python3

import os
import sys
import logging
import tempfile
import subprocess
import time
import psutil
import threading
import datetime
from app.summarizer.processor import process_audio
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError

# Configure logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for resource monitoring
monitoring = False
monitor_thread = None
resource_data = []

def monitor_resources():
    """Monitor system resources and log them"""
    global monitoring, resource_data
    process = psutil.Process(os.getpid())
    parent = psutil.Process(process.ppid())
    
    while monitoring:
        try:
            # Get CPU and memory usage
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            # Get parent process info (which might be running ffmpeg)
            parent_cpu = parent.cpu_percent(interval=0.1)
            parent_memory = parent.memory_info().rss / (1024 * 1024)
            
            # Get system-wide info
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory().percent
            
            # Log the data
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            data = {
                "timestamp": timestamp,
                "process_cpu": cpu_percent,
                "process_memory_mb": memory_mb,
                "parent_cpu": parent_cpu,
                "parent_memory_mb": parent_memory,
                "system_cpu": system_cpu,
                "system_memory_percent": system_memory
            }
            resource_data.append(data)
            
            # Log every 5 seconds to avoid flooding
            if len(resource_data) % 50 == 0:
                logger.debug(f"Resource monitor: CPU: {cpu_percent}%, Memory: {memory_mb:.2f}MB, System CPU: {system_cpu}%")
            
            time.sleep(0.1)  # Check every 100ms
        except Exception as e:
            logger.error(f"Error in resource monitoring: {str(e)}")
            time.sleep(1)  # Wait a bit longer if there's an error

def start_monitoring():
    """Start resource monitoring in a separate thread"""
    global monitoring, monitor_thread, resource_data
    resource_data = []
    monitoring = True
    monitor_thread = threading.Thread(target=monitor_resources)
    monitor_thread.daemon = True
    monitor_thread.start()
    logger.debug("Resource monitoring started")

def stop_monitoring():
    """Stop resource monitoring and log summary"""
    global monitoring, resource_data
    monitoring = False
    if monitor_thread:
        monitor_thread.join(timeout=1.0)
    
    if resource_data:
        # Calculate averages
        avg_process_cpu = sum(d["process_cpu"] for d in resource_data) / len(resource_data)
        avg_process_memory = sum(d["process_memory_mb"] for d in resource_data) / len(resource_data)
        avg_system_cpu = sum(d["system_cpu"] for d in resource_data) / len(resource_data)
        
        # Find peaks
        peak_process_cpu = max(d["process_cpu"] for d in resource_data)
        peak_process_memory = max(d["process_memory_mb"] for d in resource_data)
        peak_system_cpu = max(d["system_cpu"] for d in resource_data)
        
        logger.info(f"Resource monitoring summary:")
        logger.info(f"  Duration: {len(resource_data) / 10:.1f} seconds")
        logger.info(f"  Process CPU: avg={avg_process_cpu:.1f}%, peak={peak_process_cpu:.1f}%")
        logger.info(f"  Process Memory: avg={avg_process_memory:.2f}MB, peak={peak_process_memory:.2f}MB")
        logger.info(f"  System CPU: avg={avg_system_cpu:.1f}%, peak={peak_system_cpu:.1f}%")
    
    logger.debug("Resource monitoring stopped")

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
        
        # Start resource monitoring
        start_monitoring()
        
        # Track time for ffmpeg
        ffmpeg_start = time.time()
        
        # Run ffmpeg
        process = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        ffmpeg_elapsed = time.time() - ffmpeg_start
        logger.info(f"ffmpeg completed in {ffmpeg_elapsed:.2f} seconds")
        
        # Stop resource monitoring
        stop_monitoring()
        
        # Log ffmpeg output
        stderr = process.stderr.decode()
        if stderr:
            logger.debug(f"ffmpeg stderr output: {stderr}")
        
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
    finally:
        # Ensure monitoring is stopped
        if monitoring:
            stop_monitoring()

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
        
        # Start resource monitoring for the main processing
        start_monitoring()
        
        start_time = time.time()
        logger.debug("Calling process_audio()")
        result = process_audio(audio_path)
        elapsed = time.time() - start_time
        
        # Stop resource monitoring
        stop_monitoring()
        
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
        # Ensure monitoring is stopped
        if monitoring:
            stop_monitoring()
            
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed test audio file: {audio_path}")

def main():
    """Main function"""
    logger.info("Starting audio processing tests with resource monitoring")
    
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
    
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        logger.error("psutil module not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        logger.info("psutil installed. Please run the script again.")
        sys.exit(1)
    
    sys.exit(main()) 