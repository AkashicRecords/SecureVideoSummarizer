"""Test configuration."""

import os
import tempfile
import sys

# Add the tests directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_constants import *

class TestConfig:
    """Test configuration settings."""
    
    # Test environment variables
    TEST_ENV_VARS = TEST_ENV_VARS
    
    # Test app configuration
    TEST_APP_CONFIG = TEST_APP_CONFIG
    
    # Test file paths
    TEST_DIR = tempfile.mkdtemp()
    TEST_AUDIO_DIR = os.path.join(TEST_DIR, 'audio')
    TEST_SUMMARIES_DIR = os.path.join(TEST_DIR, 'summaries')
    
    # Test file paths
    TEST_AUDIO_FILE = os.path.join(TEST_AUDIO_DIR, TEST_AUDIO_FILE)
    TEST_SUMMARY_FILE = os.path.join(
        TEST_SUMMARIES_DIR,
        f'{TEST_SUMMARY_FILE_PREFIX}20240317_000000{TEST_SUMMARY_FILE_SUFFIX}'
    )
    
    # Test audio settings
    TEST_AUDIO_SETTINGS = {
        'duration': TEST_AUDIO_DURATION,
        'sample_rate': TEST_AUDIO_SAMPLE_RATE,
        'channels': 1,
        'format': 'wav'
    }
    
    # Test video settings
    TEST_VIDEO_SETTINGS = {
        'title': TEST_VIDEO_TITLE,
        'duration': TEST_VIDEO_DURATION,
        'src': TEST_VIDEO_SRC,
        'platform': TEST_VIDEO_PLATFORM,
        'current_time': TEST_VIDEO_CURRENT_TIME,
        'playback_rate': TEST_VIDEO_PLAYBACK_RATE
    }
    
    # Test summary settings
    TEST_SUMMARY_SETTINGS = {
        'max_length': 500,
        'min_length': 50,
        'format': 'text'
    }
    
    # Test session settings
    TEST_SESSION_SETTINGS = {
        'user_id': TEST_SESSION_USER_ID,
        'access_token': TEST_SESSION_ACCESS_TOKEN,
        'summary_status': TEST_SESSION_SUMMARY_STATUS,
        'summary_text': TEST_SESSION_SUMMARY_TEXT
    }
    
    # Test extension settings
    TEST_EXTENSION_SETTINGS = {
        'id': TEST_EXTENSION_ID,
        'origin': TEST_EXTENSION_ORIGIN,
        'version': '1.0.0'
    }
    
    # Test Google auth settings
    TEST_GOOGLE_SETTINGS = {
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'redirect_uri': 'http://localhost:5000/callback',
        'scope': ['openid', 'email', 'profile']
    }
    
    # Test file settings
    TEST_FILE_SETTINGS = {
        'max_size': 100 * 1024 * 1024,  # 100MB
        'allowed_types': ['audio/wav', 'video/mp4'],
        'chunk_size': 8192
    }
    
    # Test response settings
    TEST_RESPONSE_SETTINGS = {
        'success': TEST_SUCCESS_RESPONSE,
        'error': TEST_ERROR_RESPONSE,
        'timeout': 30
    }
    
    # Test validation settings
    TEST_VALIDATION_SETTINGS = {
        'video': {
            'min_duration': 1,
            'max_duration': 3600,
            'allowed_platforms': ['olympus', 'youtube', 'vimeo']
        },
        'audio': {
            'min_duration': 1,
            'max_duration': 3600,
            'min_sample_rate': 8000,
            'max_channels': 2
        }
    }
    
    @classmethod
    def setup_test_dirs(cls):
        """Set up test directories."""
        os.makedirs(cls.TEST_AUDIO_DIR, exist_ok=True)
        os.makedirs(cls.TEST_SUMMARIES_DIR, exist_ok=True)
    
    @classmethod
    def cleanup_test_dirs(cls):
        """Clean up test directories."""
        if os.path.exists(cls.TEST_DIR):
            import shutil
            shutil.rmtree(cls.TEST_DIR)
    
    @classmethod
    def get_test_file_path(cls, filename):
        """Get the full path for a test file."""
        return os.path.join(cls.TEST_DIR, filename)
    
    @classmethod
    def get_test_audio_path(cls, filename):
        """Get the full path for a test audio file."""
        return os.path.join(cls.TEST_AUDIO_DIR, filename)
    
    @classmethod
    def get_test_summary_path(cls, filename):
        """Get the full path for a test summary file."""
        return os.path.join(cls.TEST_SUMMARIES_DIR, filename) 