#!/usr/bin/env python3

import os
import sys
import logging
import requests
import json
import time
import tempfile
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API endpoint URLs
BASE_URL = "http://localhost:5000"
EXTENSION_STATUS_URL = f"{BASE_URL}/api/extension/status"
TRANSCRIBE_URL = f"{BASE_URL}/api/transcribe"
LOGIN_URL = f"{BASE_URL}/auth/login"
USER_URL = f"{BASE_URL}/auth/user"
REFRESH_TOKEN_URL = f"{BASE_URL}/auth/refresh-token"
LOGOUT_URL = f"{BASE_URL}/auth/logout"

def create_test_audio():
    """Create a test audio file for testing"""
    # Create a temporary file
    fd, audio_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    
    # Generate a simple audio file using ffmpeg
    try:
        # Generate a 3-second sine wave audio file
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', 
            '-ar', '16000', '-ac', '1', audio_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

def test_extension_status():
    """Test the extension status endpoint"""
    logger.info("Testing extension status endpoint...")
    
    try:
        response = requests.get(EXTENSION_STATUS_URL)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Extension status: {data['status']}")
            logger.info(f"Version: {data['version']}")
            logger.info(f"Allowed origins: {data['allowed_origins']}")
            return True
        else:
            logger.error(f"Extension status request failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing extension status: {str(e)}")
        return False

def test_transcribe_endpoint(session=None):
    """Test the transcribe endpoint with a real audio file"""
    logger.info("Testing transcribe endpoint...")
    
    # Create a test audio file
    audio_path = create_test_audio()
    if not audio_path:
        logger.error("Failed to create test audio file")
        return False
    
    try:
        # Prepare the file for upload
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_path), audio_file, 'audio/wav')}
            
            # Make the request
            if session:
                response = session.post(TRANSCRIBE_URL, files=files)
            else:
                response = requests.post(TRANSCRIBE_URL, files=files)
            
            # Check the response
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    logger.info("Transcription successful!")
                    logger.info(f"Transcription: {data.get('transcription', '')[:100]}...")
                    logger.info(f"Summary: {data.get('summary', '')[:100]}...")
                    return True
                else:
                    logger.warning(f"Transcription failed: {data.get('error', 'Unknown error')}")
                    logger.warning(f"Error type: {data.get('error_type', 'Unknown')}")
                    logger.warning(f"Details: {data.get('details', 'No details')}")
                    return False
            elif response.status_code == 401:
                logger.error("Authentication required. Please login first.")
                return False
            else:
                logger.error(f"Transcribe request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error testing transcribe endpoint: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed test audio file: {audio_path}")

def test_auth_flow():
    """Test the authentication flow"""
    logger.info("Testing authentication flow...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Check if we're already authenticated
    try:
        response = session.get(USER_URL)
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Already authenticated as: {user_data.get('email', 'Unknown')}")
            
            # Test the transcribe endpoint with the authenticated session
            return test_transcribe_endpoint(session)
        else:
            logger.info("Not authenticated. Starting login flow...")
    except Exception as e:
        logger.error(f"Error checking authentication status: {str(e)}")
        return False
    
    # Step 2: Start the login flow
    try:
        logger.info("Opening login URL in browser. Please complete the authentication process.")
        logger.info(f"Login URL: {LOGIN_URL}")
        
        # We can't automate the OAuth flow easily, so we'll ask the user to do it manually
        input("Press Enter after you've completed the authentication in your browser...")
        
        # Step 3: Check if we're authenticated now
        response = session.get(USER_URL)
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Successfully authenticated as: {user_data.get('email', 'Unknown')}")
            
            # Test the transcribe endpoint with the authenticated session
            return test_transcribe_endpoint(session)
        else:
            logger.error("Authentication failed after login flow")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error during authentication flow: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("Starting manual API tests")
    
    # Test extension status endpoint
    extension_status_result = test_extension_status()
    
    # Test authentication flow and transcribe endpoint
    auth_result = test_auth_flow()
    
    # Print the final result
    if extension_status_result and auth_result:
        logger.info("All API tests passed!")
        return 0
    else:
        logger.error("Some API tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 