#!/usr/bin/env python3

import unittest
import sys
import os

def run_audio_tests():
    """Run only the audio processing tests"""
    # Add the parent directory to the path so we can import the app
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Discover and run only the audio processing tests
    test_loader = unittest.TestLoader()
    
    # Load the test file directly
    test_file = os.path.join(os.path.dirname(__file__), 'tests', 'test_audio_processing.py')
    test_suite = test_loader.discover(os.path.dirname(test_file), pattern=os.path.basename(test_file))
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return the number of failures and errors
    return len(result.failures) + len(result.errors)

if __name__ == '__main__':
    print("Running audio processing tests...")
    exit_code = run_audio_tests()
    sys.exit(exit_code) 