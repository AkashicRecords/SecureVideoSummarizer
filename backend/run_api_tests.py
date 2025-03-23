#!/usr/bin/env python3

import unittest
import sys
import os
import logging
import signal
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define a timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test execution timed out")

def run_api_tests():
    """Run all API-related tests"""
    # Discover and run tests
    logger.info("Running API tests...")
    
    # Set environment variables for testing
    os.environ['TESTING'] = 'True'
    os.environ['GOOGLE_CLIENT_SECRETS_FILE'] = 'dummy_path'
    os.environ['FRONTEND_URL'] = 'http://localhost:3000'
    os.environ['BROWSER_EXTENSION_ID'] = 'dummy_extension_id'
    os.environ['ALLOWED_ORIGINS'] = 'http://localhost:3000,chrome-extension://dummy_extension_id'
    
    # Set a timeout for the entire test suite (5 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 300 seconds = 5 minutes
    
    try:
        # Discover tests in the tests directory
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*_endpoints.py')
        
        # Run the tests
        start_time = time.time()
        logger.info("Starting API tests execution...")
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        elapsed = time.time() - start_time
        logger.info(f"API tests completed in {elapsed:.2f} seconds")
        
        # Cancel the alarm
        signal.alarm(0)
        
        # Return the result
        return result.wasSuccessful()
    except TimeoutError:
        logger.error("API tests timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running API tests: {str(e)}")
        return False
    finally:
        # Make sure to cancel the alarm in case of any exception
        signal.alarm(0)

if __name__ == '__main__':
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the tests
    success = run_api_tests()
    sys.exit(0 if success else 1) 