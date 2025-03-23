#!/usr/bin/env python3
"""
Test script for the Olympus video processing pipeline.
This script tests the integration between the Chrome extension and backend
for Olympus video processing.
"""

import requests
import json
import time
import argparse
import sys
import traceback
import logging
from termcolor import colored
import os
import subprocess
from datetime import datetime

from app.utils.logger import get_test_logger
from app.utils.test_helpers import info, success, warning, error, debug, Color

# Setup logging
logger = get_test_logger('olympus')

# Configuration - these can be modified by command line arguments
DEFAULT_BASE_URL = "http://localhost:8080"
EXTENSION_ID = "sample-extension-id"
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds

# Sample video data for testing
SAMPLE_VIDEO_DATA = {
    "videoMetadata": {
        "title": "Test Olympus Video",
        "duration": 120,
        "src": "https://olympus.mygreatlearning.com/courses/124502/modules/items/6353964",
        "platform": "olympus",
        "width": 640,
        "height": 360,
        "currentTime": 0,
        "paused": True
    },
    "transcript": "This is a sample transcript for testing. It contains information about the Olympus video platform. The video discusses secure summarization techniques.",
    "sessionId": "test-session-" + str(int(time.time()))
}

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    # Check for yt-dlp (required for video downloading)
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode != 0:
            missing_deps.append("yt-dlp")
    except FileNotFoundError:
        missing_deps.append("yt-dlp")
    
    # Check for ffmpeg (required for audio extraction)
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode != 0:
            missing_deps.append("ffmpeg")
    except FileNotFoundError:
        missing_deps.append("ffmpeg")
    
    # Report missing dependencies
    if missing_deps:
        warning("\nMissing required dependencies:")
        for dep in missing_deps:
            warning(f"  - {dep}")
        
        # Provide installation instructions
        info("\nInstallation instructions:")
        if "yt-dlp" in missing_deps:
            info("  Install yt-dlp: pip install yt-dlp")
        if "ffmpeg" in missing_deps:
            if sys.platform == "darwin":  # macOS
                info("  Install ffmpeg on macOS: brew install ffmpeg")
            elif sys.platform == "linux":
                info("  Install ffmpeg on Linux: sudo apt-get install ffmpeg")
            else:
                info("  Install ffmpeg: https://ffmpeg.org/download.html")
        
        return False
    
    return True

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=None, response_data=None, request_info=None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        self.request_info = request_info
        super().__init__(self.message)
    
    def __str__(self):
        details = []
        if self.status_code:
            details.append(f"Status: {self.status_code}")
        if self.request_info:
            details.append(f"Request: {self.request_info}")
        if self.response_data:
            if isinstance(self.response_data, dict) and 'error' in self.response_data:
                details.append(f"Error: {self.response_data['error']}")
            else:
                details.append(f"Response: {self.response_data}")
                
        if details:
            return f"{self.message} - {', '.join(details)}"
        return self.message

def parse_error_response(response):
    """Parse error response to extract detailed error information"""
    try:
        data = response.json()
        
        # Extract error details if available
        if isinstance(data, dict):
            # Handle different error response formats
            if 'error' in data:
                if isinstance(data['error'], dict):
                    # Structured error response with type, code, etc.
                    error_obj = data['error']
                    error_type = error_obj.get('type', 'APIError')
                    error_msg = error_obj.get('message', str(error_obj))
                    error_code = error_obj.get('code', response.status_code)
                    error_details = error_obj.get('details', {})
                    
                    error_str = f"{error_type}[{error_code}]: {error_msg}"
                    if error_details:
                        error_str += f" - Details: {json.dumps(error_details)}"
                    return error_str
                else:
                    # Simple error string
                    return str(data['error'])
            elif 'message' in data:
                return str(data['message'])
            else:
                return json.dumps(data)
        return str(data)
    except:
        # Fallback to text if can't parse JSON
        return response.text

def make_request(url, method="GET", headers=None, data=None, expected_status=200, timeout=30):
    """Make a request to the API with robust error handling"""
    if headers is None:
        headers = {
            "Origin": f"chrome-extension://{EXTENSION_ID}",
            "X-Extension-ID": EXTENSION_ID,
            "Content-Type": "application/json"
        }
    
    start_time = time.time()
    request_info = f"{method} {url}"
    
    try:
        debug(f"Making request: {request_info}")
        debug(f"Headers: {json.dumps(headers, indent=2)}")
        if data:
            debug(f"Request data: {json.dumps(data, indent=2)}")
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            error_msg = f"Unsupported method: {method}"
            error(error_msg)
            raise APIError(error_msg, request_info=request_info)
        
        duration = time.time() - start_time
        
        # Log detailed response information
        debug(f"Response status: {response.status_code} ({response.reason})")
        debug(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            debug(f"Response data: {json.dumps(response_data, indent=2)}")
        except Exception as e:
            debug(f"Could not parse response as JSON: {str(e)}")
            debug(f"Response text: {response.text[:1000]}{'...' if len(response.text) > 1000 else ''}")
            response_data = response.text
        
        if response.status_code == expected_status:
            success(f"{method} {url} - {response.status_code} [{response.reason}] ({duration:.2f}s)")
            return True, response_data, response
        else:
            error_details = parse_error_response(response)
            error_msg = f"{method} {url} - Expected {expected_status}, got {response.status_code} [{response.reason}] ({duration:.2f}s)"
            error(error_msg)
            error(f"Error details: {error_details}")
            
            # Check for common HTTP error codes and provide more context
            if response.status_code == 400:
                warning("Bad Request: The server couldn't understand the request")
            elif response.status_code == 401:
                warning("Unauthorized: Authentication required or failed")
            elif response.status_code == 403:
                warning("Forbidden: You don't have permission to access this resource")
            elif response.status_code == 404:
                warning("Not Found: The requested resource does not exist")
            elif response.status_code == 429:
                warning("Too Many Requests: Rate limit exceeded")
            elif response.status_code >= 500:
                warning("Server Error: The server failed to fulfill a valid request")
                
            return False, response_data, response
                
    except requests.Timeout:
        error_msg = f"{method} {url} - Request timed out after {timeout} seconds"
        error(error_msg)
        logger.error(error_msg)
        return False, f"Timeout after {timeout}s", None
        
    except requests.ConnectionError as e:
        error_msg = f"{method} {url} - Connection error: {str(e)}"
        error(error_msg)
        logger.error(f"Connection error: {traceback.format_exc()}")
        return False, f"Connection error: {str(e)}", None
        
    except requests.RequestException as e:
        error_msg = f"{method} {url} - Request failed: {str(e)}"
        error(error_msg)
        logger.error(f"Request exception: {traceback.format_exc()}")
        return False, f"Request error: {str(e)}", None
        
    except json.JSONDecodeError as e:
        error_msg = f"{method} {url} - JSON decode error: {str(e)}"
        error(error_msg)
        logger.error(f"JSON decode error: {traceback.format_exc()}")
        return False, f"JSON decode error: {str(e)}", None
        
    except Exception as e:
        error_msg = f"Unexpected error with {method} {url}: {str(e)}"
        error(error_msg)
        logger.error(f"Unexpected exception: {traceback.format_exc()}")
        return False, f"Unexpected error: {str(e)}", None

def test_olympus_status(base_url):
    """Test the Olympus platform status endpoint"""
    info("\nTesting Olympus status endpoint...")
    try:
        success, data, response = make_request(f"{base_url}/api/olympus/status")
        
        if success:
            info(f"Olympus status response: {json.dumps(data, indent=2)}")
            
            # Validate the response structure
            expected_keys = ['status', 'extension_id', 'supported_features']
            missing_keys = [key for key in expected_keys if key not in data]
            
            if missing_keys:
                warning(f"Response is missing expected keys: {', '.join(missing_keys)}")
                
            # Check if the status indicates the system is ready
            if data.get('status') != 'ready':
                warning(f"Olympus system status is not 'ready': {data.get('status')}")
        
        return success
    except Exception as e:
        error(f"Exception during Olympus status test: {str(e)}")
        logger.error(f"Status test exception: {traceback.format_exc()}")
        return False

def test_olympus_capture(base_url):
    """Test the Olympus transcript capture endpoint"""
    info("\nTesting Olympus transcript capture endpoint...")
    
    try:
        # Log the request data being sent
        debug(f"Sending video data for capture: {json.dumps(SAMPLE_VIDEO_DATA, indent=2)}")
        
        # Make the request
        success, data, response = make_request(
            f"{base_url}/api/olympus/capture",
            method="POST",
            data=SAMPLE_VIDEO_DATA
        )
        
        if success:
            info(f"Olympus capture response: {json.dumps(data, indent=2)}")
            
            # Validate the response structure
            expected_keys = ['success', 'sessionId', 'summary']
            missing_keys = [key for key in expected_keys if key not in data]
            
            if missing_keys:
                warning(f"Response is missing expected keys: {', '.join(missing_keys)}")
            
            # Validate summary content if present
            if 'summary' in data:
                summary_length = len(data['summary'])
                info(f"Successfully generated summary with {summary_length} characters")
                
                if summary_length < 10:
                    warning(f"Summary is suspiciously short ({summary_length} chars)")
            
            # Validate session ID
            if 'sessionId' in data:
                session_id = data['sessionId']
                info(f"Session ID: {session_id}")
                
                if not session_id:
                    warning("Empty session ID returned")
        else:
            # If response is available, extract more details about the error
            if response:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and 'error' in error_data:
                            error(f"Server returned error: {error_data['error']}")
                    except:
                        pass
        
        return success
    except Exception as e:
        error(f"Exception during Olympus capture test: {str(e)}")
        logger.error(f"Capture test exception: {traceback.format_exc()}")
        return False

def test_olympus_process_url(base_url):
    """Test the Olympus URL processing endpoint"""
    info("\nTesting Olympus URL processing endpoint...")
    
    # Check dependencies before running test
    if not check_dependencies() and '--ignore-deps' not in sys.argv:
        warning("Skipping URL processing test due to missing dependencies")
        warning("Run with --ignore-deps to force the test anyway")
        return False
    
    try:
        # Check if we need to use mocked data
        mock_download = '--mock-download' in sys.argv
        
        if mock_download:
            info("Using mocked data for URL processing test")
            # Create a test data payload with special test flag
            test_data = {
                "url": "https://olympus.mygreatlearning.com/courses/124502/modules/items/6353964",
                "videoMetadata": SAMPLE_VIDEO_DATA["videoMetadata"],
                "_test_mode": True,  # Signal to the backend that this is a test
                "skip_download": True,  # Skip actual download
                "mock_transcript": "This is a mock transcript for testing purposes.",
                "mock_summary": "This is a mock summary of the transcript."
            }
        else:
            # Create standard test data
            test_data = {
                "url": "https://olympus.mygreatlearning.com/courses/124502/modules/items/6353964",
                "videoMetadata": SAMPLE_VIDEO_DATA["videoMetadata"]
            }
        
        # Log the request data being sent
        debug(f"Sending URL data for processing: {json.dumps(test_data, indent=2)}")
        
        # Make the request
        success, data, response = make_request(
            f"{base_url}/api/olympus/process-url",
            method="POST",
            data=test_data
        )
        
        if success:
            info(f"Olympus URL processing response: {json.dumps(data, indent=2)}")
            
            # Validate the response structure
            expected_keys = ['success', 'sessionId']
            missing_keys = [key for key in expected_keys if key not in data]
            
            if missing_keys:
                warning(f"Response is missing expected keys: {', '.join(missing_keys)}")
                
            # Validate transcript and summary if present
            if 'transcript' in data:
                transcript_length = len(data['transcript'])
                info(f"Successfully generated transcript with {transcript_length} characters")
                
                if transcript_length < 10:
                    warning(f"Transcript is suspiciously short ({transcript_length} chars)")
                    
            if 'summary' in data:
                summary_length = len(data['summary'])
                info(f"Successfully generated summary with {summary_length} characters")
                
                if summary_length < 10:
                    warning(f"Summary is suspiciously short ({summary_length} chars)")
        else:
            # Check for special error case where client-side download is required
            if response and response.status_code == 400:
                try:
                    error_data = response.json()
                    if error_data.get('request_client_download') is True:
                        warning("Server requested client-side download of blob URL")
                except:
                    pass
        
        return success
    except Exception as e:
        error(f"Exception during Olympus process URL test: {str(e)}")
        logger.error(f"Process URL test exception: {traceback.format_exc()}")
        return False

def test_api_health(base_url):
    """Test the API health endpoint"""
    info("\nTesting API health endpoint...")
    try:
        success, data, response = make_request(f"{base_url}/api/status")
        
        if success:
            info(f"API health response: {json.dumps(data, indent=2)}")
            
            # Validate the response structure
            expected_keys = ['status']
            missing_keys = [key for key in expected_keys if key not in data]
            
            if missing_keys:
                warning(f"Response is missing expected keys: {', '.join(missing_keys)}")
            
            # Check if API status is healthy
            if data.get('status') != 'ok':
                warning(f"API status is not 'ok': {data.get('status')}")
                
        return success
    except Exception as e:
        error(f"Exception during API health test: {str(e)}")
        logger.error(f"API health test exception: {traceback.format_exc()}")
        return False

def main():
    try:
        parser = argparse.ArgumentParser(description="Test Olympus video processing pipeline")
        parser.add_argument("--url", default=DEFAULT_BASE_URL, help=f"Base URL (default: {DEFAULT_BASE_URL})")
        parser.add_argument("--extension-id", default=EXTENSION_ID, help="Chrome extension ID for testing")
        parser.add_argument("--test", choices=["all", "status", "capture", "process", "health"], default="all",
                        help="Specific test to run (default: all)")
        parser.add_argument("--verbose", action="store_true", help="Print verbose output")
        parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)")
        parser.add_argument("--mock-download", action="store_true", help="Use mock data instead of downloading video")
        parser.add_argument("--ignore-deps", action="store_true", help="Ignore dependency checks")
        
        args = parser.parse_args()
        
        # Enable debug logging if verbose flag is set
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
            debug("Verbose mode enabled")
        
        # Use local variables instead of globals
        extension_id = args.extension_id
        base_url = args.url
        
        info(f"Testing Olympus video processing at {base_url}")
        info(f"Using extension ID: {extension_id}")
        
        # Declare make_request as global before using it
        global make_request
        
        # Store original make_request function reference
        original_make_request = make_request
        
        # Create a new wrapper function that uses the original_make_request
        def make_request_with_id(url, method="GET", headers=None, data=None, expected_status=200, timeout=30):
            if headers is None:
                headers = {
                    "Origin": f"chrome-extension://{extension_id}",
                    "X-Extension-ID": extension_id,
                    "Content-Type": "application/json"
                }
            return original_make_request(url, method, headers, data, expected_status, timeout=timeout)
        
        # Override the global function with our wrapper
        make_request = make_request_with_id
        
        success_count = 0
        total_tests = 0
        
        try:
            # Run the selected tests
            if args.test in ["all", "health"]:
                total_tests += 1
                if test_api_health(base_url):
                    success_count += 1
            
            if args.test in ["all", "status"]:
                total_tests += 1
                if test_olympus_status(base_url):
                    success_count += 1
            
            if args.test in ["all", "capture"]:
                total_tests += 1
                if test_olympus_capture(base_url):
                    success_count += 1
            
            if args.test in ["all", "process"]:
                total_tests += 1
                if test_olympus_process_url(base_url):
                    success_count += 1
        finally:
            # Restore the original function
            make_request = original_make_request
        
        # Print summary
        print("\n" + "=" * 50)
        if success_count == total_tests:
            success(f"All tests passed! ({success_count}/{total_tests})")
        else:
            warning(f"Some tests failed. Passed {success_count} out of {total_tests} tests.")
        
        if args.verbose:
            info(f"See '{os.path.abspath('olympus_test.log')}' for detailed logs")
            
        print("=" * 50)
        
        # Return exit code based on test results
        return 0 if success_count == total_tests else 1
    
    except KeyboardInterrupt:
        warning("\nTest interrupted by user")
        return 130
    
    except Exception as e:
        error(f"Fatal error in test script: {str(e)}")
        logger.error(f"Fatal error: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 