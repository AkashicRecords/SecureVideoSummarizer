#!/usr/bin/env python3
"""
Enable test mode for the Secure Video Summarizer
This script runs the Flask app with test settings that bypass the actual transcription.
"""

import os
import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_mode.log")
    ]
)

logger = logging.getLogger("test_mode")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run the Flask app with test settings")
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server on')
    args = parser.parse_args()
    
    # Set environment variables for development and testing
    os.environ["FLASK_ENV"] = "development"
    os.environ["BYPASS_AUTH_FOR_TESTING"] = "true"
    os.environ["IN_TEST_MODE"] = "true"  # This will be read by the app
    
    # Set the app path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Import after setting environment variables
    from app.main import create_app
    
    # Directly set the global variables in processor.py
    try:
        from app.summarizer.processor import logger as processor_logger
        import app.summarizer.processor as processor_module
        
        # Enable test mode
        processor_module.IN_TEST_MODE = True
        processor_module.TEST_TRANSCRIBE_OUTPUT = "This is a test transcription generated in test mode. The transcription service has been bypassed."
        processor_module.TEST_TRANSCRIBE_ERROR = False
        
        logger.info("Test mode enabled for processor")
        processor_logger.info("Processor test mode enabled")
    except ImportError as e:
        logger.error(f"Failed to import processor module: {str(e)}")
        return 1
    
    # Create and run the app
    app = create_app("development")
    
    # Print test mode notice
    logger.info("=" * 80)
    logger.info("RUNNING IN TEST MODE - Transcription service is bypassed")
    logger.info("All transcription requests will return a test response")
    logger.info("=" * 80)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=args.port)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 