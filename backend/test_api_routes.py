#!/usr/bin/env python3
"""
API test suite for testing all routes in the Secure Video Summarizer.
This script tests the extension ping, status, and other key API endpoints.
"""

import requests
import sys
import time
import json
import os
from termcolor import colored
import argparse

# Configuration - these can be modified by command line arguments
DEFAULT_BASE_URL = "http://localhost:8080"
EXTENSION_ID = "sample-extension-id"

# Routes to test
ROUTES = {
    # Extension routes
    "extension_ping": "/api/extension/ping",
    "extension_status": "/api/extension/status",
    "extension_config": "/api/extension/config",
    
    # Core API routes
    "api_status": "/api/status",
    
    # YouTube routes
    "youtube_status": "/api/youtube/status",
    
    # Olympus routes
    "olympus_status": "/api/olympus/status",
}

# Setup colored output
def success(msg):
    print(colored(f"✅ {msg}", "green"))

def error(msg):
    print(colored(f"❌ {msg}", "red"))

def info(msg):
    print(colored(f"ℹ️ {msg}", "blue"))

def warning(msg):
    print(colored(f"⚠️ {msg}", "yellow"))

def make_request(url, headers=None, method="GET", data=None, expected_status=200, extension_id=EXTENSION_ID):
    """Make a request to the API with proper error handling"""
    start_time = time.time()
    if headers is None:
        headers = {
            "Origin": f"chrome-extension://{extension_id}",
            "X-Extension-ID": extension_id
        }
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    else:
        error(f"Unsupported method: {method}")
        return False, None, None
    
    duration = time.time() - start_time
    
    # Check if status code matches expected
    if response.status_code == expected_status:
        success(f"{method} {url} - {response.status_code} ({duration:.2f}s)")
        try:
            return True, response.json(), duration
        except:
            return True, response.text, duration
    else:
        error(f"{method} {url} - Expected {expected_status}, got {response.status_code} ({duration:.2f}s)")
        try:
            return False, response.json(), duration
        except:
            return False, response.text, duration

def test_extension_routes(base_url, extension_id=EXTENSION_ID):
    """Test all extension-related routes"""
    info("\n--- Testing Extension Routes ---")
    
    # Test ping
    success_count = 0
    total_count = 0
    
    route = ROUTES["extension_ping"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"Extension Ping Response: {data}")
    
    # Test status
    route = ROUTES["extension_status"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"Extension Status Response: {data}")
    
    # Test config
    route = ROUTES["extension_config"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"Extension Config Response: {data}")
    
    return success_count, total_count

def test_youtube_routes(base_url, extension_id=EXTENSION_ID):
    """Test YouTube-related routes"""
    info("\n--- Testing YouTube Routes ---")
    
    success_count = 0
    total_count = 0
    
    # Test status
    route = ROUTES["youtube_status"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"YouTube Status Response: {data}")
    
    return success_count, total_count

def test_olympus_routes(base_url, extension_id=EXTENSION_ID):
    """Test Olympus-related routes"""
    info("\n--- Testing Olympus Routes ---")
    
    success_count = 0
    total_count = 0
    
    # Test status
    route = ROUTES["olympus_status"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"Olympus Status Response: {data}")
    
    return success_count, total_count

def test_api_routes(base_url, extension_id=EXTENSION_ID):
    """Test core API routes"""
    info("\n--- Testing Core API Routes ---")
    
    success_count = 0
    total_count = 0
    
    # Test status
    route = ROUTES["api_status"]
    total_count += 1
    success, data, _ = make_request(f"{base_url}{route}", extension_id=extension_id)
    if success:
        success_count += 1
        info(f"API Status Response: {data}")
    
    return success_count, total_count

def main():
    parser = argparse.ArgumentParser(description="Test API routes for Secure Video Summarizer")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help=f"Base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--extension-id", default=EXTENSION_ID, help="Chrome extension ID for testing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    extension_id = args.extension_id
    base_url = args.url
    
    info(f"Testing API routes at {base_url}")
    info(f"Using extension ID: {extension_id}")
    
    # Update headers with extension ID for all requests
    headers = {
        "Origin": f"chrome-extension://{extension_id}",
        "X-Extension-ID": extension_id
    }
    
    # Test connection
    connection_url = f"{base_url}/api/extension/ping"
    try:
        response = requests.get(connection_url, headers=headers)
        if response.status_code == 200:
            success(f"Connected to server at {base_url}")
        else:
            warning(f"Server responded with status code {response.status_code}")
            error("Failed to connect to server. Exiting.")
            return 1
    except requests.ConnectionError:
        error(f"Could not connect to {base_url}")
        error("Failed to connect to server. Exiting.")
        return 1
    
    # Run all tests
    total_success = 0
    total_tests = 0
    
    ext_success, ext_total = test_extension_routes(base_url, extension_id)
    total_success += ext_success
    total_tests += ext_total
    
    yt_success, yt_total = test_youtube_routes(base_url, extension_id)
    total_success += yt_success
    total_tests += yt_total
    
    olympus_success, olympus_total = test_olympus_routes(base_url, extension_id)
    total_success += olympus_success
    total_tests += olympus_total
    
    api_success, api_total = test_api_routes(base_url, extension_id)
    total_success += api_success
    total_tests += api_total
    
    # Print summary
    print("\n" + "=" * 50)
    if total_success == total_tests:
        success(f"All tests passed! ({total_success}/{total_tests})")
    else:
        warning(f"Some tests failed. Passed {total_success} out of {total_tests} tests.")
    
    print("=" * 50)
    
    # Return exit code based on test results
    return 0 if total_success == total_tests else 1

if __name__ == "__main__":
    sys.exit(main()) 