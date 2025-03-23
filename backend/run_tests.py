#!/usr/bin/env python
"""
Script to run all tests for the Secure Video Summarizer project
"""
import os
import sys
import unittest
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'tests/test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all test modules in the tests directory"""
    # Ensure we can import from parent directory
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Create the tests directory if it doesn't exist
    tests_dir = os.path.join(parent_dir, 'tests')
    if not os.path.exists(tests_dir):
        os.makedirs(tests_dir)
    
    logger.info("Starting test suite for Secure Video Summarizer")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    
    # Only run specific test modules if they exist, otherwise we'll run discovered tests
    specific_test_modules = [
        'tests.test_dependencies',
        'tests.test_audio_processor'
    ]
    
    test_suite = unittest.TestSuite()
    missing_modules = []
    
    for module_name in specific_test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            module_tests = test_loader.loadTestsFromModule(module)
            test_suite.addTest(module_tests)
            logger.info(f"Added tests from {module_name}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not import {module_name}: {e}")
            missing_modules.append(module_name)
    
    # If any specified modules were missing, try discovering tests instead
    if missing_modules:
        logger.info("Some specific test modules were missing, discovering tests...")
        discovered_tests = test_loader.discover('tests', pattern='test_*.py')
        test_suite.addTest(discovered_tests)
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    logger.info("Test suite completed")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Print errors and failures details
    if result.errors:
        logger.error("=== ERRORS ===")
        for test, error in result.errors:
            logger.error(f"ERROR in {test}: {error}")
    
    if result.failures:
        logger.error("=== FAILURES ===")
        for test, failure in result.failures:
            logger.error(f"FAILURE in {test}: {failure}")
    
    return len(result.errors) == 0 and len(result.failures) == 0

def check_import_errors():
    """Check for import errors in key modules"""
    # Add import checks that specifically address the issues we've had
    modules_to_check = [
        ('flask', 'Flask core module'),
        ('flask_cors', 'Flask CORS extension for API access'),
        ('magic', 'Python-magic for file detection'),
        ('googleapiclient.discovery', 'Google API client for authentication'),
        ('elevenlabs', 'Eleven Labs API client for audio')
    ]
    
    all_passed = True
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            logger.info(f"✓ {module_name} ({description}) - Successfully imported")
        except ImportError as e:
            logger.error(f"✗ {module_name} ({description}) - Import failed: {str(e)}")
            all_passed = False
    
    # Ensure openai is NOT importable
    try:
        __import__('openai')
        logger.error("✗ openai - Should NOT be importable, but it is")
        all_passed = False
    except ImportError:
        logger.info("✓ openai - Correctly NOT importable")
    
    return all_passed

if __name__ == "__main__":
    # Check for basic import errors first
    logger.info("Checking for import errors...")
    if not check_import_errors():
        logger.error("Import checks failed. Please install missing dependencies.")
        sys.exit(1)
    
    # Run the tests
    if run_tests():
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Some tests failed.")
        sys.exit(1) 