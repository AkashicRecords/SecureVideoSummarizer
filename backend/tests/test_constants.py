"""Constants used in tests."""

import os

# Test user data
TEST_USER_ID = 'test_user_id'
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_NAME = 'Test User'
TEST_USER_PICTURE = 'https://example.com/picture.jpg'

# Test video data
TEST_VIDEO_TITLE = 'Test Video'
TEST_VIDEO_DURATION = 180
TEST_VIDEO_SRC = 'https://example.com/test-video.mp4'
TEST_VIDEO_PLATFORM = 'olympus'
TEST_VIDEO_CURRENT_TIME = 45
TEST_VIDEO_PLAYBACK_RATE = 1.0

# Test summary data
TEST_SUMMARY_TEXT = 'This is a test summary of the video content.'

# Test session data
TEST_SESSION_USER_ID = 'test_user_id'
TEST_SESSION_ACCESS_TOKEN = 'test_access_token'
TEST_SESSION_SUMMARY_STATUS = 'idle'
TEST_SESSION_SUMMARY_TEXT = None

# Test extension data
TEST_EXTENSION_ID = 'EXTENSION_ID_PLACEHOLDER'
TEST_EXTENSION_ORIGIN = f'chrome-extension://{TEST_EXTENSION_ID}'

# Test Google auth data
TEST_GOOGLE_ACCESS_TOKEN = 'mock_token'
TEST_GOOGLE_TOKEN_TYPE = 'Bearer'
TEST_GOOGLE_EXPIRES_IN = 3600
TEST_GOOGLE_USER_ID = '123456789'

# Test file paths
TEST_AUDIO_FILE = 'test_audio.wav'
TEST_SUMMARY_FILE_PREFIX = 'summary_'
TEST_SUMMARY_FILE_SUFFIX = '.json'

# Test audio parameters
TEST_AUDIO_DURATION = 10
TEST_AUDIO_SAMPLE_RATE = 16000

# Test response data
TEST_SUCCESS_RESPONSE = {'success': True}
TEST_ERROR_RESPONSE = {'success': False, 'error': 'Test error message'}

# Test file sizes
TEST_FILE_SIZE = 1000

# Test environment variables
TEST_ENV_VARS = {
    'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
    'FRONTEND_URL': 'http://localhost:8080',
    'BROWSER_EXTENSION_ID': TEST_EXTENSION_ID,
    'ALLOWED_ORIGINS': f'http://localhost:8080,{TEST_EXTENSION_ORIGIN}',
    'SUMMARIES_DIR': '/tmp/test_summaries'
}

# Test app configuration
TEST_APP_CONFIG = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'PRESERVE_CONTEXT_ON_EXCEPTION': False,
    'ALLOWED_ORIGINS': f'http://localhost:8080,{TEST_EXTENSION_ORIGIN}',
    'SECRET_KEY': 'test_secret_key'
}

# Test audio processing results
TEST_AUDIO_CONVERSION_RESULT = 'test_audio.wav'
TEST_AUDIO_VALIDATION_RESULT = True
TEST_AUDIO_TRANSCRIPTION_RESULT = 'Test transcription'
TEST_AUDIO_SUMMARIZATION_RESULT = 'Test summary' 