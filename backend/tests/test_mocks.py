"""Test mocks for application."""

import os
import sys
from unittest import mock

# Add the tests directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_constants import *

class MockObjects:
    """Common mock objects for tests."""
    
    @staticmethod
    def mock_google_auth():
        """Create a mock Google auth object."""
        mock_auth = mock.MagicMock()
        mock_auth.authorize_access_token.return_value = {
            'access_token': TEST_GOOGLE_ACCESS_TOKEN,
            'token_type': TEST_GOOGLE_TOKEN_TYPE,
            'expires_in': TEST_GOOGLE_EXPIRES_IN
        }
        return mock_auth
    
    @staticmethod
    def mock_google_userinfo():
        """Create a mock Google userinfo response."""
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {
            'sub': TEST_GOOGLE_USER_ID,
            'email': TEST_USER_EMAIL,
            'name': TEST_USER_NAME,
            'picture': TEST_USER_PICTURE
        }
        return mock_response
    
    @staticmethod
    def mock_audio_processor():
        """Create a mock audio processor."""
        mock_processor = mock.MagicMock()
        mock_processor.convert_to_wav_enhanced.return_value = TEST_AUDIO_CONVERSION_RESULT
        mock_processor.validate_audio.return_value = TEST_AUDIO_VALIDATION_RESULT
        mock_processor.transcribe_audio_enhanced.return_value = TEST_AUDIO_TRANSCRIPTION_RESULT
        mock_processor.summarize_text_enhanced.return_value = TEST_AUDIO_SUMMARIZATION_RESULT
        return mock_processor
    
    @staticmethod
    def mock_file_operations():
        """Create mocks for file operations."""
        mock_exists = mock.MagicMock(return_value=True)
        mock_size = mock.MagicMock(return_value=TEST_FILE_SIZE)
        mock_makedirs = mock.MagicMock(return_value=None)
        return mock_exists, mock_size, mock_makedirs
    
    @staticmethod
    def mock_extension_request():
        """Create a mock extension request."""
        mock_request = mock.MagicMock()
        mock_request.headers = {'Origin': TEST_EXTENSION_ORIGIN}
        mock_request.json.return_value = {
            'summary': TEST_SUMMARY_TEXT,
            'video_data': {
                'title': TEST_VIDEO_TITLE,
                'duration': TEST_VIDEO_DURATION,
                'src': TEST_VIDEO_SRC,
                'platform': TEST_VIDEO_PLATFORM
            }
        }
        return mock_request
    
    @staticmethod
    def mock_session():
        """Create a mock session object."""
        mock_session = mock.MagicMock()
        mock_session.get.return_value = {
            'user_id': TEST_SESSION_USER_ID,
            'access_token': TEST_SESSION_ACCESS_TOKEN,
            'summary_status': TEST_SESSION_SUMMARY_STATUS,
            'summary_text': TEST_SESSION_SUMMARY_TEXT
        }
        return mock_session
    
    @staticmethod
    def mock_audio_file():
        """Create a mock audio file."""
        mock_file = mock.MagicMock()
        mock_file.name = TEST_AUDIO_FILE
        mock_file.read.return_value = b'dummy audio content'
        return mock_file
    
    @staticmethod
    def mock_summary_file():
        """Create a mock summary file."""
        mock_file = mock.MagicMock()
        mock_file.name = f'{TEST_SUMMARY_FILE_PREFIX}20240317_000000{TEST_SUMMARY_FILE_SUFFIX}'
        mock_file.read.return_value = b'{"summary": "Test summary", "video_data": {"title": "Test Video"}}'
        return mock_file
    
    @staticmethod
    def mock_video_element():
        """Create a mock video element."""
        mock_video = mock.MagicMock()
        mock_video.title = TEST_VIDEO_TITLE
        mock_video.duration = TEST_VIDEO_DURATION
        mock_video.src = TEST_VIDEO_SRC
        mock_video.currentTime = TEST_VIDEO_CURRENT_TIME
        mock_video.playbackRate = TEST_VIDEO_PLAYBACK_RATE
        return mock_video
    
    @staticmethod
    def mock_extension_message():
        """Create a mock extension message."""
        mock_message = mock.MagicMock()
        mock_message.data = {
            'type': 'video_data',
            'video': {
                'title': TEST_VIDEO_TITLE,
                'duration': TEST_VIDEO_DURATION,
                'src': TEST_VIDEO_SRC,
                'platform': TEST_VIDEO_PLATFORM
            }
        }
        return mock_message 