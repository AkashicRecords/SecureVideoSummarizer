#!/usr/bin/env python3
"""
Disable test mode for the Secure Video Summarizer
This script runs the Flask app with normal settings that use the actual transcription service.
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
        logging.FileHandler("normal_mode.log")
    ]
)

logger = logging.getLogger("normal_mode")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run the Flask app with normal settings")
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server on')
    args = parser.parse_args()
    
    # Set environment variables for development
    os.environ["FLASK_ENV"] = "development"
    os.environ.pop("BYPASS_AUTH_FOR_TESTING", None)  # Remove if exists
    os.environ.pop("IN_TEST_MODE", None)  # Remove if exists
    
    # Set the app path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Import after setting environment variables
    from app.main import create_app
    
    # Directly set the global variables in processor.py
    try:
        from app.summarizer.processor import logger as processor_logger
        import app.summarizer.processor as processor_module
        
        # Disable test mode
        processor_module.IN_TEST_MODE = False
        processor_module.TEST_TRANSCRIBE_ERROR = False
        
        logger.info("Test mode disabled for processor")
        processor_logger.info("Processor running in normal mode")
    except ImportError as e:
        logger.error(f"Failed to import processor module: {str(e)}")
        return 1
    
    # Create and run the app
    app = create_app("development")
    
    # Print normal mode notice
    logger.info("=" * 80)
    logger.info("RUNNING IN NORMAL MODE - Using actual transcription service")
    logger.info("=" * 80)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=args.port)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 