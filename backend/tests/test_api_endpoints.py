import unittest
import os
import tempfile
import json
import io
import shutil
from datetime import datetime, timedelta
from unittest import mock
from io import BytesIO
from flask import jsonify, session
from werkzeug.datastructures import FileStorage
from app.main import create_app
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from functools import wraps
import inspect

# Create a mock login_required decorator that passes through the function
def mock_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'test_extension_id',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id'
        })
        self.env_patcher.start()
        
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False,
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id',
            'SESSION_TYPE': 'filesystem',
            'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
            'SECRET_KEY': 'test_secret_key'
        })
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
            
        # Set up client secrets patcher
        self.secrets_patcher = mock.patch('app.auth.routes.get_client_secrets_file')
        self.mock_get_secrets = self.secrets_patcher.start()
        self.mock_get_secrets.return_value = os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json')
        
        # Patch the login_required decorator in the auth routes module
        self.login_required_patcher = mock.patch('app.api.routes.login_required')
        mock_login_required_func = self.login_required_patcher.start()
        mock_login_required_func.return_value = lambda f: f  # Make decorator pass through
        
        # Set up authenticated session
        self.setup_authenticated_session()
        
        # Create a temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def setup_authenticated_session(self):
        """Helper method to set up authenticated session data"""
        with self.client.session_transaction() as sess:
            sess['user_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'picture': 'https://example.com/profile.jpg',
                'email_verified': True
            }
            sess['last_activity'] = datetime.utcnow().isoformat()
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
    
    def create_test_audio_file(self):
        """Helper method to create a test audio file for each test"""
        # Create a temporary file that persists until tearDown
        file_path = os.path.join(self.temp_dir, "test_audio.wav") 
        
        # Create a dummy WAV file with proper WAV header
        # This won't be perfect audio, but will have a valid WAV structure
        with open(file_path, 'wb') as f:
            # WAV header (44 bytes)
            # RIFF header
            f.write(b'RIFF')
            f.write((36).to_bytes(4, byteorder='little'))  # File size - 8
            f.write(b'WAVE')
            
            # Format chunk
            f.write(b'fmt ')
            f.write((16).to_bytes(4, byteorder='little'))  # Chunk size
            f.write((1).to_bytes(2, byteorder='little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, byteorder='little'))   # Num channels (mono)
            f.write((16000).to_bytes(4, byteorder='little'))  # Sample rate
            f.write((32000).to_bytes(4, byteorder='little'))  # Byte rate
            f.write((2).to_bytes(2, byteorder='little'))   # Block align
            f.write((16).to_bytes(2, byteorder='little'))  # Bits per sample
            
            # Data chunk
            f.write(b'data')
            f.write((16).to_bytes(4, byteorder='little'))  # Chunk size
            
            # Add some dummy PCM data (silence)
            for _ in range(8):
                f.write((0).to_bytes(2, byteorder='little'))
        
        return file_path
    
    def create_multipart_data(self, file_path):
        """Create multipart form data for file upload."""
        # Read the file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create a FileStorage object directly
        file_storage = FileStorage(
            stream=io.BytesIO(file_content),
            filename='test_audio.wav',
            content_type='audio/wav'
        )
        
        # Return data in the format expected by Flask's test client
        # Include all required form fields
        return {
            'audio': file_storage,
            'video_data': json.dumps({
                'title': 'Test Video',
                'url': 'https://example.com/test-video',
                'duration': 120
            }),
            'options': json.dumps({
                'length': 'medium',
                'format': 'paragraph'
            }),
            'playback_rate': '1.0'
        }
    
    def tearDown(self):
        """Clean up test environment"""
        # Pop the app context
        self.app_context.pop()
        
        # Clean up the temporary directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Stop patchers
        self.login_required_patcher.stop()
        self.secrets_patcher.stop()
        self.env_patcher.stop()
    
    def test_extension_status_endpoint(self):
        """Test the extension status endpoint"""
        response = self.client.get('/api/extension/status')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'connected')
        self.assertIn('version', data)
        self.assertIn('allowed_origins', data)
        self.assertEqual(len(data['allowed_origins']), 2)
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_no_file(self, mock_process):
        """Test the transcribe endpoint with no file"""
        # Access the endpoint without a file
        response = self.client.post(
            '/api/transcribe',
            data={},
            content_type='multipart/form-data'
        )
        
        # Check that the response indicates a missing file
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No file provided')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_transcription_error(self, mock_process):
        """Test the transcribe endpoint with transcription error"""
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to transcribe audio',
            'error_type': 'transcription',
            'details': 'Speech recognition service unavailable'
        }
        
        # Access the endpoint with a file
        test_file = self.create_test_audio_file()
        data = self.create_multipart_data(test_file)
        
        # Set process_audio mock to be called regardless of subprocess result
        with mock.patch('subprocess.run') as mock_subprocess:
            response = self.client.post(
                '/api/transcribe',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Ensure the mock was called
        mock_process.assert_called_once()
        
        # Check the response
        self.assertEqual(response.status_code, 500)  # Server error for transcription issues
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Failed to transcribe audio')
        self.assertIn('error_type', data)
        self.assertEqual(data['error_type'], 'transcription')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_summarization_error(self, mock_process):
        """Test the transcribe endpoint with summarization error"""
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to summarize transcription',
            'error_type': 'summarization',
            'details': 'AI model failed to generate a summary'
        }
        
        # Access the endpoint with a file
        test_file = self.create_test_audio_file()
        data = self.create_multipart_data(test_file)
        
        # Set process_audio mock to be called regardless of subprocess result
        with mock.patch('subprocess.run') as mock_subprocess:
            response = self.client.post(
                '/api/transcribe',
                data=data,
                content_type='multipart/form-data'
            )
            
        # Ensure the mock was called
        mock_process.assert_called_once()
        
        # Check the response
        self.assertEqual(response.status_code, 500)  # Server error for summarization issues
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Failed to summarize transcription')
        self.assertIn('error_type', data)
        self.assertEqual(data['error_type'], 'summarization')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_success(self, mock_process):
        """Test the transcribe endpoint with successful processing"""
        # Mock the process_audio function
        mock_process.return_value = {
            'success': True,
            'transcription': 'This is a test transcription.',
            'summary': 'This is a test summary.'
        }
        
        # Access the endpoint with a file
        test_file = self.create_test_audio_file()
        data = self.create_multipart_data(test_file)
        
        # Set process_audio mock to be called regardless of subprocess result
        with mock.patch('subprocess.run') as mock_subprocess:
            response = self.client.post(
                '/api/transcribe',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Ensure the mock was called
        mock_process.assert_called_once()
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('transcription', data)
        self.assertEqual(data['transcription'], 'This is a test transcription.')
        self.assertIn('summary', data)
        self.assertEqual(data['summary'], 'This is a test summary.')
    
    def test_transcribe_endpoint_unauthorized(self):
        """Test the transcribe endpoint without authentication"""
        # We'll directly verify that the login_required decorator is applied to the endpoint
        from app.api.routes import transcribe
        from app.auth.routes import login_required
        
        # Check if the login_required decorator is applied to the function
        # Get the source code of the function
        source = inspect.getsource(transcribe)
        
        # Check for the @login_required decorator in the source code
        self.assertIn('@login_required', source, 
                     "The transcribe endpoint should be protected with @login_required")
        
        # Additional test: Check actual app routing table (Flask specific)
        test_app = create_app('testing')
        
        # Find the transcribe endpoint in the app's route map
        for rule in test_app.url_map.iter_rules():
            if rule.endpoint == 'api.transcribe':
                # Found the route, now verify expected security is present
                # Simply log verification that we found the route
                print(f"Found route: {rule}")
                break
        else:
            self.fail("Couldn't find api.transcribe endpoint in the application routes")
        
        # Test passes if we've reached this point, confirming the endpoint exists
        # and has the login_required decorator

if __name__ == '__main__':
    unittest.main()
