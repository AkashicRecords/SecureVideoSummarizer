"""Test cleanup utilities."""

import os
import shutil
import tempfile
from unittest import mock
import sys
import os

# Add the tests directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_config import TestConfig

class TestCleanup:
    """Test cleanup utilities."""
    
    @staticmethod
    def cleanup_temp_files():
        """Clean up temporary files."""
        # Clean up test directories
        TestConfig.cleanup_test_dirs()
        
        # Clean up any remaining temporary files
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith('test_') and filename.endswith('.wav'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    
    @staticmethod
    def cleanup_mocks():
        """Clean up mock objects."""
        # Stop all active patchers
        for patcher in mock.patch.stopall():
            try:
                patcher.stop()
            except Exception:
                pass
    
    @staticmethod
    def cleanup_test_data():
        """Clean up test data."""
        # Clean up test files
        if hasattr(TestConfig, 'TEST_AUDIO_FILE') and os.path.exists(TestConfig.TEST_AUDIO_FILE):
            os.remove(TestConfig.TEST_AUDIO_FILE)
        
        if hasattr(TestConfig, 'TEST_SUMMARY_FILE') and os.path.exists(TestConfig.TEST_SUMMARY_FILE):
            os.remove(TestConfig.TEST_SUMMARY_FILE)
        
        # Clean up test directories
        if hasattr(TestConfig, 'TEST_AUDIO_DIR') and os.path.exists(TestConfig.TEST_AUDIO_DIR):
            shutil.rmtree(TestConfig.TEST_AUDIO_DIR)
        
        if hasattr(TestConfig, 'TEST_SUMMARIES_DIR') and os.path.exists(TestConfig.TEST_SUMMARIES_DIR):
            shutil.rmtree(TestConfig.TEST_SUMMARIES_DIR)
        
        if hasattr(TestConfig, 'TEST_DIR') and os.path.exists(TestConfig.TEST_DIR):
            shutil.rmtree(TestConfig.TEST_DIR)
    
    @staticmethod
    def cleanup_test_session():
        """Clean up test session data."""
        # Clear any test session data
        if hasattr(TestConfig, 'TEST_SESSION_SETTINGS'):
            TestConfig.TEST_SESSION_SETTINGS.clear()
    
    @staticmethod
    def cleanup_test_request():
        """Clean up test request data."""
        # Clear any test request data
        if hasattr(TestConfig, 'TEST_EXTENSION_REQUEST'):
            TestConfig.TEST_EXTENSION_REQUEST.clear()
    
    @staticmethod
    def cleanup_test_response():
        """Clean up test response data."""
        # Clear any test response data
        if hasattr(TestConfig, 'TEST_RESPONSE_SETTINGS'):
            TestConfig.TEST_RESPONSE_SETTINGS.clear()
    
    @staticmethod
    def cleanup_test_validation():
        """Clean up test validation data."""
        # Clear any test validation data
        if hasattr(TestConfig, 'TEST_VALIDATION_SETTINGS'):
            TestConfig.TEST_VALIDATION_SETTINGS.clear()
    
    @staticmethod
    def cleanup_all():
        """Clean up all test resources."""
        TestCleanup.cleanup_temp_files()
        TestCleanup.cleanup_mocks()
        TestCleanup.cleanup_test_data()
        TestCleanup.cleanup_test_session()
        TestCleanup.cleanup_test_request()
        TestCleanup.cleanup_test_response()
        TestCleanup.cleanup_test_validation()
    
    @staticmethod
    def cleanup_directory(directory):
        """Clean up a specific directory."""
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    @staticmethod
    def cleanup_file(file_path):
        """Clean up a specific file."""
        if os.path.exists(file_path):
            os.remove(file_path)
    
    @staticmethod
    def cleanup_mock(mock_obj):
        """Clean up a specific mock object."""
        if isinstance(mock_obj, mock.MagicMock):
            mock_obj.reset_mock()
            if hasattr(mock_obj, 'stop'):
                mock_obj.stop()