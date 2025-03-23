import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest import mock
from app.main import create_app
from app.config import Config
from tests.test_helpers import (
    mock_google_auth_response, 
    mock_google_userinfo_response,
    create_test_audio_file,
    mock_audio_processing_functions,
    mock_extension_headers as helper_mock_extension_headers,
    create_test_video_file,
    mock_video_processing_functions,
    create_test_video_data,
    create_test_summary_data,
    create_test_session_data,
    create_test_error_response,
    create_test_success_response
)
from app.summarizer.processor import process_audio
from tests.test_helpers_validation import (
    validate_audio_file
)

@pytest.fixture(scope="session")
def app():
    """Create a test Flask application instance."""
    # Create a temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    
    # Mock environment variables
    env_patcher = mock.patch.dict(os.environ, {
        'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
        'FRONTEND_URL': 'http://localhost:3000',
        'BROWSER_EXTENSION_ID': 'test_extension_id',
        'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id',
        'SUMMARIES_DIR': temp_dir
    })
    env_patcher.start()
    
    # Create test app
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'PRESERVE_CONTEXT_ON_EXCEPTION': False,
        'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id',
        'SUMMARIES_DIR': temp_dir,
        'SECRET_KEY': 'test_secret_key',
        'SESSION_TYPE': 'filesystem',
        'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
        'FRONTEND_URL': 'http://localhost:3000',
        'BROWSER_EXTENSION_ID': 'test_extension_id'
    })
    
    yield app
    
    # Cleanup
    env_patcher.stop()
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the app with authentication."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_info'] = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/profile.jpg',
            'email_verified': True
        }
        sess['last_activity'] = datetime.utcnow().isoformat()
        sess['extension_jobs'] = {}
        sess['oauth_state'] = 'test_state'
        sess['credentials'] = {
            'token': 'test_token',
            'refresh_token': 'test_refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'scopes': ['profile', 'email'],
            'expiry': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    return client

@pytest.fixture(scope="function")
def app_context(app):
    """Create an application context."""
    with app.app_context() as ctx:
        yield ctx

@pytest.fixture(scope="function")
def mock_google_auth():
    """Mock Google authentication."""
    with mock.patch('app.auth.google_auth') as mock_auth:
        mock_auth.authorize_access_token.return_value = mock_google_auth_response()
        yield mock_auth

@pytest.fixture(scope="function")
def mock_google_userinfo():
    """Mock Google user info."""
    with mock.patch('app.auth.google_auth.get') as mock_get:
        mock_get.return_value.json.return_value = mock_google_userinfo_response()
        yield mock_get

@pytest.fixture(scope="function")
def mock_audio_processing():
    """Mock audio processing functions."""
    yield mock_audio_processing_functions()

@pytest.fixture(scope="function")
def mock_video_processing():
    """Mock video processing functions."""
    yield mock_video_processing_functions()

@pytest.fixture(scope="function")
def mock_extension_id():
    """Mock extension ID for testing."""
    return 'EXTENSION_ID_PLACEHOLDER'

@pytest.fixture(scope="function")
def mock_extension_headers(mock_extension_id):
    """Create headers for extension requests."""
    return helper_mock_extension_headers(mock_extension_id)

@pytest.fixture(scope="function")
def test_audio_file():
    """Create a test audio file with proper WAV format."""
    audio_path, temp_dir = create_test_audio_file(duration=5, sample_rate=16000)
    yield audio_path
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def test_video_file():
    """Create a test video file."""
    video_path, temp_dir = create_test_video_file(format='mp4', duration=10)
    yield video_path
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def test_video_data():
    """Create test video data."""
    return create_test_video_data()

@pytest.fixture(scope="function")
def test_summary_data():
    """Create test summary data."""
    return create_test_summary_data()

@pytest.fixture(scope="function")
def test_session_data():
    """Create test session data."""
    return create_test_session_data()

@pytest.fixture
def test_empty_audio_file():
    """Create an empty test audio file for testing."""
    # Create an empty audio file
    audio_path, temp_dir = create_test_audio_file(duration=0, filename='empty_audio.wav')
    
    yield audio_path, temp_dir
    
    # Clean up the temporary directory
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)

@pytest.fixture
def mock_audio_processing():
    """Mock the audio processing functions."""
    def mock_process(audio_file, enhance=True):
        return {
            'success': True,
            'transcription': 'This is a test transcription.',
            'summary': 'This is a test summary.'
        }
    
    # Save original function
    original_process = process_audio
    
    # Replace with mock
    process_audio = mock_process
    
    yield mock_process
    
    # Restore original function
    process_audio = original_process

# Add fixtures for extension testing
@pytest.fixture
def mock_extension_id():
    """Mock the extension ID."""
    return 'test_extension_id'

@pytest.fixture
def mock_extension_headers(mock_extension_id):
    """Mock headers for extension requests."""
    return {
        'Origin': f'chrome-extension://{mock_extension_id}'
    }

# Add fixtures for Google auth mocking
@pytest.fixture
def mock_google_auth():
    """Mock Google auth credentials."""
    return {
        'token': 'test_token',
        'refresh_token': 'test_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': ['profile', 'email']
    }

@pytest.fixture
def mock_google_userinfo():
    """Mock Google userinfo response."""
    return {
        'email': 'test@example.com',
        'name': 'Test User',
        'picture': 'https://example.com/profile.jpg',
        'email_verified': True
    }

# Add fixture for mock video processing
@pytest.fixture
def mock_video_processing():
    """Mock video processing functions."""
    def mock_extract_audio(video_file):
        audio_path, _ = create_test_audio_file()
        return audio_path
    
    return {
        'extract_audio': mock_extract_audio
    } 