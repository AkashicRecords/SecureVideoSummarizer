"""Test data generation."""

import os
import sys

# Add the tests directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from test_constants import *

# Test user data
TEST_USER = {
    'id': TEST_USER_ID,
    'email': TEST_USER_EMAIL,
    'name': TEST_USER_NAME,
    'picture': TEST_USER_PICTURE
}

# Test video data
TEST_VIDEO = {
    'title': TEST_VIDEO_TITLE,
    'duration': TEST_VIDEO_DURATION,
    'src': TEST_VIDEO_SRC,
    'platform': TEST_VIDEO_PLATFORM,
    'current_time': TEST_VIDEO_CURRENT_TIME,
    'playback_rate': TEST_VIDEO_PLAYBACK_RATE
}

# Test summary data
TEST_SUMMARY = {
    'summary': TEST_SUMMARY_TEXT,
    'video_data': TEST_VIDEO,
    'timestamp': '2024-03-17T00:00:00'
}

# Test session data
TEST_SESSION = {
    'user_id': TEST_SESSION_USER_ID,
    'access_token': TEST_SESSION_ACCESS_TOKEN,
    'summary_status': TEST_SESSION_SUMMARY_STATUS,
    'summary_text': TEST_SESSION_SUMMARY_TEXT
}

# Test extension request data
TEST_EXTENSION_REQUEST = {
    'headers': {'Origin': TEST_EXTENSION_ORIGIN},
    'data': {
        'summary': TEST_SUMMARY_TEXT,
        'video_data': TEST_VIDEO
    }
}

# Test Google auth data
TEST_GOOGLE_AUTH = {
    'access_token': TEST_GOOGLE_ACCESS_TOKEN,
    'token_type': TEST_GOOGLE_TOKEN_TYPE,
    'expires_in': TEST_GOOGLE_EXPIRES_IN
}

TEST_GOOGLE_USERINFO = {
    'sub': TEST_GOOGLE_USER_ID,
    'email': TEST_USER_EMAIL,
    'name': TEST_USER_NAME,
    'picture': TEST_USER_PICTURE
}

# Test audio data
TEST_AUDIO_DATA = {
    'duration': TEST_AUDIO_DURATION,
    'sample_rate': TEST_AUDIO_SAMPLE_RATE,
    'content': b'dummy audio content'
}

# Test file data
TEST_FILE_DATA = {
    'name': TEST_AUDIO_FILE,
    'size': TEST_FILE_SIZE,
    'content': b'dummy file content'
}

TEST_SUMMARY_FILE_DATA = {
    'name': f'{TEST_SUMMARY_FILE_PREFIX}20240317_000000{TEST_SUMMARY_FILE_SUFFIX}',
    'content': b'{"summary": "Test summary", "video_data": {"title": "Test Video"}}'
}

# Test response data
TEST_RESPONSES = {
    'success': TEST_SUCCESS_RESPONSE,
    'error': TEST_ERROR_RESPONSE,
    'summary': {
        'success': True,
        'summary': TEST_SUMMARY_TEXT,
        'video_data': TEST_VIDEO
    },
    'status': {
        'success': True,
        'status': 'connected',
        'version': '1.0.0'
    }
}

# Test extension message data
TEST_EXTENSION_MESSAGES = {
    'video_data': {
        'type': 'video_data',
        'video': TEST_VIDEO
    },
    'summary_request': {
        'type': 'summary_request',
        'video': TEST_VIDEO
    },
    'summary_response': {
        'type': 'summary_response',
        'summary': TEST_SUMMARY_TEXT
    }
}

# Test error messages
TEST_ERROR_MESSAGES = {
    'invalid_request': 'Invalid request data',
    'unauthorized': 'Unauthorized access',
    'processing_error': 'Error processing video',
    'file_error': 'Error handling file',
    'auth_error': 'Authentication failed'
}

# Test validation data
TEST_VALIDATION_DATA = {
    'valid_video': {
        'title': 'Valid Video',
        'duration': 120,
        'src': 'https://example.com/valid.mp4',
        'platform': 'olympus'
    },
    'invalid_video': {
        'title': '',
        'duration': -1,
        'src': '',
        'platform': ''
    },
    'valid_audio': {
        'duration': 60,
        'sample_rate': 16000,
        'channels': 1
    },
    'invalid_audio': {
        'duration': 0,
        'sample_rate': 0,
        'channels': 0
    }
} 