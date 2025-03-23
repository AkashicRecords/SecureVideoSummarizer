"""Test setup utilities."""

import os
import shutil
import tempfile
import sys
from unittest import mock

# Add the tests directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_config import TestConfig
from test_constants import *

class TestSetup:
    """Test environment setup and teardown."""
    
    @staticmethod
    def setup_test_environment():
        """Set up the test environment."""
        # Set up test directories
        TestConfig.setup_test_dirs()
        
        # Mock environment variables
        env_patcher = mock.patch.dict(os.environ, TEST_ENV_VARS)
        env_patcher.start()
        
        # Mock file operations
        file_patcher = mock.patch('os.path.exists', return_value=True)
        file_patcher.start()
        
        # Mock audio processing
        audio_patcher = mock.patch('app.summarizer.processor')
        mock_processor = audio_patcher.start()
        mock_processor.convert_to_wav_enhanced.return_value = TEST_AUDIO_CONVERSION_RESULT
        mock_processor.validate_audio.return_value = TEST_AUDIO_VALIDATION_RESULT
        mock_processor.transcribe_audio_enhanced.return_value = TEST_AUDIO_TRANSCRIPTION_RESULT
        mock_processor.summarize_text_enhanced.return_value = TEST_AUDIO_SUMMARIZATION_RESULT
        
        # Mock Google auth
        google_patcher = mock.patch('app.auth.google_auth')
        mock_auth = google_patcher.start()
        mock_auth.authorize_access_token.return_value = TEST_GOOGLE_AUTH
        
        # Store patchers for cleanup
        TestSetup.patchers = [
            env_patcher,
            file_patcher,
            audio_patcher,
            google_patcher
        ]
    
    @staticmethod
    def teardown_test_environment():
        """Tear down the test environment."""
        # Stop all patchers
        for patcher in TestSetup.patchers:
            patcher.stop()
        
        # Clean up test directories
        TestConfig.cleanup_test_dirs()
    
    @staticmethod
    def create_test_files():
        """Create test files."""
        # Create test audio file
        with open(TestConfig.TEST_AUDIO_FILE, 'w') as f:
            f.write('dummy audio content')
        
        # Create test summary file
        with open(TestConfig.TEST_SUMMARY_FILE, 'w') as f:
            f.write('{"summary": "Test summary", "video_data": {"title": "Test Video"}}')
    
    @staticmethod
    def cleanup_test_files():
        """Clean up test files."""
        # Remove test audio file
        if os.path.exists(TestConfig.TEST_AUDIO_FILE):
            os.remove(TestConfig.TEST_AUDIO_FILE)
        
        # Remove test summary file
        if os.path.exists(TestConfig.TEST_SUMMARY_FILE):
            os.remove(TestConfig.TEST_SUMMARY_FILE)
    
    @staticmethod
    def setup_test_session():
        """Set up test session data."""
        session_data = TEST_SESSION.copy()
        return session_data
    
    @staticmethod
    def setup_test_request():
        """Set up test request data."""
        request_data = TEST_EXTENSION_REQUEST.copy()
        return request_data
    
    @staticmethod
    def setup_test_response():
        """Set up test response data."""
        response_data = TEST_RESPONSES.copy()
        return response_data
    
    @staticmethod
    def setup_test_validation():
        """Set up test validation data."""
        validation_data = TEST_VALIDATION_DATA.copy()
        return validation_data
    
    @staticmethod
    def setup_test_mocks():
        """Set up test mocks."""
        from .test_mocks import MockObjects
        
        mocks = {
            'google_auth': MockObjects.mock_google_auth(),
            'google_userinfo': MockObjects.mock_google_userinfo(),
            'audio_processor': MockObjects.mock_audio_processor(),
            'file_operations': MockObjects.mock_file_operations(),
            'extension_request': MockObjects.mock_extension_request(),
            'session': MockObjects.mock_session(),
            'audio_file': MockObjects.mock_audio_file(),
            'summary_file': MockObjects.mock_summary_file(),
            'video_element': MockObjects.mock_video_element(),
            'extension_message': MockObjects.mock_extension_message()
        }
        
        return mocks 