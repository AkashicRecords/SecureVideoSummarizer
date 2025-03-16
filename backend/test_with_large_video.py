#!/usr/bin/env python
import os
import sys
import json
import argparse
import subprocess
import logging
import time
import threading
from app.summarizer.processor import VideoSummarizer, IN_TEST_MODE, TEST_VALIDATE_LOW_SAMPLE_RATE
from flask import Flask, current_app

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_processing.log')
    ]
)

# Get the root logger and set it to DEBUG
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Set up our specific logger
logger = logging.getLogger("video_processor")
logger.setLevel(logging.DEBUG)

# Make sure other loggers are verbose too
logging.getLogger("app.summarizer.processor").setLevel(logging.DEBUG)
logging.getLogger("app.summarizer.ollama_client").setLevel(logging.DEBUG)

def create_app_context():
    """Create a minimal Flask app context with verbose logging"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.logger.setLevel(logging.DEBUG)
    return app

def extract_segment(video_path, output_path, duration=60):
    """Extract a segment from the video for faster testing"""
    logger.info(f"Extracting {duration} second segment from {video_path}")
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-t', str(duration),
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_path,
        '-y'  # Overwrite if exists
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Error extracting segment: {result.stderr}")
        return False
    
    logger.info(f"Successfully extracted segment to {output_path}")
    logger.info(f"Segment file size: {os.path.getsize(output_path)} bytes")
    return True

def log_progress_indicator():
    """Print a progress indicator every few seconds"""
    i = 0
    symbols = "|/-\\"
    while not progress_done.is_set():
        sys.stdout.write(f"\rProcessing... {symbols[i % len(symbols)]}")
        sys.stdout.flush()
        i += 1
        time.sleep(0.5)
    
    # Clear the progress indicator line when done
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()

# Add a monkey patch to the VideoSummarizer to add more logging
original_process_video = VideoSummarizer.process_video
def verbose_process_video(self, video_path, options=None):
    """Monkey-patched version of process_video with more logging"""
    logger.info("=" * 50)
    logger.info("STARTING VIDEO PROCESSING")
    logger.info(f"Video path: {video_path}")
    logger.info(f"Options: {options}")
    logger.info("=" * 50)
    
    # Log video file details
    file_size = os.path.getsize(video_path)
    logger.info(f"Video file size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Print start of process
    print("\n--- Starting Video Processing ---")
    print(f"Video: {video_path}")
    print(f"File size: {file_size/1024/1024:.2f} MB")
    
    try:
        # Log each step of the process
        logger.info("Step 1: Extracting audio from video")
        print("Step 1: Extracting audio from video...")
        
        # Extract audio (original method extracted from the process_video method)
        audio_path = self.extract_audio(video_path)
        logger.info(f"Audio extracted to: {audio_path}")
        logger.info(f"Audio file size: {os.path.getsize(audio_path)} bytes")
        print(f"   Audio extracted successfully ({os.path.getsize(audio_path)/1024:.2f} KB)")
        
        # Validate audio
        logger.info("Step 2: Validating audio file")
        print("Step 2: Validating audio file...")
        from app.summarizer.processor import validate_audio
        if not validate_audio(audio_path):
            logger.error("Audio validation failed")
            print("   Audio validation failed!")
            raise Exception("Invalid audio extracted from video")
        logger.info("Audio validation passed")
        print("   Audio validation passed!")
        
        # Transcribe audio
        logger.info("Step 3: Transcribing audio")
        print("Step 3: Transcribing audio (this may take a while)...")
        from app.summarizer.processor import transcribe_audio_enhanced
        transcription = transcribe_audio_enhanced(audio_path)
        logger.info(f"Transcription complete: {len(transcription)} characters")
        logger.info(f"Transcription sample: {transcription[:100]}...")
        print(f"   Transcription complete: {len(transcription)} characters")
        
        # Summarize text
        logger.info("Step 4: Summarizing transcription")
        print("Step 4: Summarizing transcription...")
        
        min_length = options.get('min_length', 50) if options else 50
        max_length = options.get('max_length', 150) if options else 150
        
        logger.info(f"Summary parameters: min_length={min_length}, max_length={max_length}")
        summary = self.summarize_text(transcription, min_length=min_length, max_length=max_length)
        logger.info(f"Summary complete: {len(summary)} characters")
        logger.info(f"Summary sample: {summary[:100]}...")
        print(f"   Summary complete: {len(summary)} characters")
        
        # Clean up
        logger.info("Step 5: Cleaning up temporary files")
        print("Step 5: Cleaning up temporary files...")
        if os.path.exists(audio_path):
            os.unlink(audio_path)
            logger.info(f"Removed temporary audio file: {audio_path}")
            print(f"   Removed temporary audio file")
        
        logger.info("Video processing completed successfully")
        print("Video processing completed successfully!")
        
        return {
            "transcript": transcription,
            "summary": summary
        }
    except Exception as e:
        logger.exception(f"Error in process_video: {str(e)}")
        print(f"\nERROR in processing: {str(e)}")
        # If we're in a test environment, we might want to re-raise this
        # for easier debugging, but in production we'll handle it gracefully
        if IN_TEST_MODE:
            raise
        return {
            "transcript": f"Error: {str(e)}",
            "summary": f"Failed to process video due to error: {str(e)}"
        }

# Replace the original method with our verbose version
VideoSummarizer.process_video = verbose_process_video

# Global flag for progress indicator
progress_done = threading.Event()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test video summarization directly")
    parser.add_argument("video_path", help="Path to the video file to summarize")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Duration of video segment to process (in seconds)")
    parser.add_argument("--length", choices=["short", "medium", "long"], default="medium", 
                       help="Summary length")
    parser.add_argument("--format", choices=["paragraph", "bullets", "numbered", "key_points"], 
                       default="bullets", help="Summary format")
    parser.add_argument("--full", action="store_true",
                       help="Process the full video instead of just a segment")
    args = parser.parse_args()
    
    # Check if video file exists
    if not os.path.exists(args.video_path):
        logger.error(f"Video file not found: {args.video_path}")
        return 1
    
    # Extract a segment for faster processing if not processing the full video
    video_to_process = args.video_path
    if not args.full:
        segment_path = f"segment_{int(time.time())}.mp4"
        if not extract_segment(args.video_path, segment_path, args.duration):
            logger.error("Failed to extract video segment. Trying to process the full video instead.")
        else:
            video_to_process = segment_path
            logger.info(f"Using extracted segment: {segment_path}")
    
    # Set up summarization options
    options = {
        "length": args.length,
        "format": args.format,
        "focus": ["key_points"],
        "min_length": 30 if args.length == "short" else (100 if args.length == "long" else 50),
        "max_length": 100 if args.length == "short" else (250 if args.length == "long" else 150)
    }
    
    logger.info("=" * 70)
    logger.info("STARTING VIDEO SUMMARIZATION PROCESS")
    logger.info(f"Video: {video_to_process}")
    logger.info(f"Options: {json.dumps(options, indent=2)}")
    logger.info("=" * 70)
    
    print("\n==========================================================")
    print("PROCESSING VIDEO DIRECTLY")
    print("==========================================================")
    print(f"Video: {video_to_process}")
    print(f"Options: {json.dumps(options, indent=2)}")
    if not args.full:
        print(f"Processing only the first {args.duration} seconds of the video")
    print("==========================================================\n")
    
    # Create app context
    app = create_app_context()
    with app.app_context():
        try:
            # Initialize VideoSummarizer
            logger.info("Initializing VideoSummarizer")
            print("Initializing VideoSummarizer...")
            summarizer = VideoSummarizer()
            logger.info("VideoSummarizer initialized")
            
            # Start progress indicator in a separate thread
            progress_done.clear()
            progress_thread = threading.Thread(target=log_progress_indicator)
            progress_thread.daemon = True
            progress_thread.start()
            
            # Process the video
            logger.info("Starting video processing")
            print("Starting video processing (this may take a while)...")
            
            start_time = time.time()
            result = summarizer.process_video(video_to_process, options)
            end_time = time.time()
            
            # Stop progress indicator
            progress_done.set()
            progress_thread.join()
            
            processing_time = end_time - start_time
            logger.info(f"Video processing completed in {processing_time:.2f} seconds")
            
            # Display results
            print("\n==========================================================")
            print("VIDEO SUMMARIZATION RESULTS")
            print(f"Processing time: {processing_time:.2f} seconds")
            print("==========================================================")
            
            if result and 'transcript' in result:
                transcript = result.get('transcript', 'No transcript available')
                summary = result.get('summary', 'No summary available')
                
                logger.info(f"Transcript length: {len(transcript)} characters")
                logger.info(f"Summary length: {len(summary)} characters")
                
                print("\nTRANSCRIPT:")
                print("----------------------------------------------------------")
                print(transcript)
                
                print("\nSUMMARY:")
                print("----------------------------------------------------------")
                print(summary)
                
                print("\n==========================================================")
                
                # Clean up segment if created
                if not args.full and os.path.exists(segment_path):
                    os.remove(segment_path)
                    logger.info(f"Removed temporary segment file: {segment_path}")
                
                return 0
            else:
                logger.error(f"Failed to process video. Result: {result}")
                print("\nERROR: Failed to process video")
                print(f"Result: {result}")
                print("\n==========================================================")
                return 1
                
        except Exception as e:
            # Stop progress indicator if it's running
            progress_done.set()
            if 'progress_thread' in locals() and progress_thread.is_alive():
                progress_thread.join()
                
            logger.exception("Error processing video")
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            print("\n==========================================================")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 