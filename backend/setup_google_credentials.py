#!/usr/bin/env python3

import os
import sys
import json
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_credentials():
    """Set up Google OAuth credentials for testing"""
    logger.info("Setting up Google OAuth credentials")
    
    # Use the specific path to the Google OAuth credentials file
    credentials_path = "/Users/lightspeedtooblivion/Documents/SecureVideoSummarizer/venv/client_secret_365939761536-c6mvm8oavhnfv0gadpab08df5dsa1usv.apps.googleusercontent.com.json"
    logger.info(f"Using credentials file at: {credentials_path}")
    
    if not os.path.exists(credentials_path):
        logger.error(f"File not found: {credentials_path}")
        return False
    
    try:
        # Read the credentials file to validate it
        with open(credentials_path, 'r') as f:
            credentials = json.load(f)
        
        # Check if it's a valid OAuth credentials file
        if 'web' not in credentials or 'client_id' not in credentials['web']:
            logger.error("Invalid OAuth credentials file. Make sure you downloaded the correct JSON file.")
            return False
        
        # Create a credentials directory if it doesn't exist
        credentials_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials')
        os.makedirs(credentials_dir, exist_ok=True)
        
        # Copy the credentials file to the credentials directory
        target_path = os.path.join(credentials_dir, 'google_client_secrets.json')
        shutil.copy(credentials_path, target_path)
        logger.info(f"Credentials file copied to: {target_path}")
        
        # Update the .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        env_vars = {}
        
        # Read existing .env file if it exists
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        # Update the Google client secrets file path
        env_vars['GOOGLE_CLIENT_SECRETS_FILE'] = target_path
        
        # Set other required environment variables if not already set
        if 'FRONTEND_URL' not in env_vars:
            env_vars['FRONTEND_URL'] = 'http://localhost:3000'
        
        if 'BROWSER_EXTENSION_ID' not in env_vars:
            env_vars['BROWSER_EXTENSION_ID'] = 'dummy_extension_id'
        
        if 'ALLOWED_ORIGINS' not in env_vars:
            env_vars['ALLOWED_ORIGINS'] = 'http://localhost:3000,chrome-extension://dummy_extension_id'
        
        # Write the updated .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f".env file updated with Google credentials path: {env_path}")
        
        # Print instructions for the next steps
        print("\n" + "="*80)
        print("Google OAuth credentials have been set up successfully!")
        print("="*80)
        print("\nNext steps:")
        print("1. Make sure your application is running:")
        print("   source venv/bin/activate && python -m app.main")
        print("2. Run the manual API test script:")
        print("   python manual_api_test.py")
        print("\nThe test script will guide you through the authentication process.")
        print("="*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up credentials: {str(e)}")
        return False

if __name__ == '__main__':
    setup_credentials() 