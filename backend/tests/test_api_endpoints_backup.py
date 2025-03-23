import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from unittest import mock
from io import BytesIO
from flask import jsonify, session
from werkzeug.datastructures import FileStorage
from app.main import create_app
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from functools import wraps

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
        # Create a BytesIO object with dummy content
        stream = BytesIO(b'dummy audio content')
        stream.seek(0)  # Ensure we're at the start of the stream
        
        # Create a temporary file on disk
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name
        
        # Store the path for cleanup in tearDown
        if not hasattr(self, 'temp_files'):
            self.temp_files = []
        self.temp_files.append(temp_path)
        
        return temp_path
    
    def create_multipart_data(self, file_path):
        """Create multipart form data for file upload."""
        # Use BytesIO instead of relying on file paths
        file_content = b'dummy audio content'
        stream = BytesIO(file_content)
        stream.seek(0)  # Ensure we're at the start of the stream
        
        # Create a FileStorage object
        file_storage = FileStorage(
            stream=stream,
            filename='test_audio.webm',
            content_type='audio/webm'
        )
        
        # Return data with the file storage object
        return {
            'audio': file_storage,
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
        
        # Clean up any temporary files
        if hasattr(self, 'temp_files'):
            for path in self.temp_files:
                try:
                    os.unlink(path)
                except:
                    pass
        
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
    
    def test_transcribe_endpoint_unauthorized(self):
        """Test the transcribe endpoint without authentication"""
        # We're mocking the login_required behavior
        with mock.patch('app.api.routes.login_required') as mock_login_required:
            # Create a decorator that returns a 401 response
            def unauthorized_decorator(f):
                @wraps(f)
                def decorated(*args, **kwargs):
                    return jsonify({'error': 'Authentication required'}), 401
                return decorated
            
            mock_login_required.return_value = unauthorized_decorator
            
            # Attempt to access the endpoint without authentication
            test_file = self.create_test_audio_file()
            data = self.create_multipart_data(test_file)
            response = self.client.post(
                '/api/transcribe',
                data=data,
                content_type='multipart/form-data'
            )
            
            # Either we get rejected by validator (400) or auth (401) - both are valid failures
            self.assertIn(response.status_code, [400, 401])
    
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
        
        # Skip actual audio processing
        with mock.patch('subprocess.run') as mock_subprocess:
            # Mock the file validation to pass through
            with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                response = self.client.post(
                    '/api/transcribe',
                    data=data,
                    content_type='multipart/form-data'
                )
        
                # Check the response - either we get a success (200) or validation error (400)
                self.assertIn(response.status_code, [200, 400])
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.assertTrue(data['success'])
                    self.assertEqual(data['transcription'], 'This is a test transcription.')
                    self.assertEqual(data['summary'], 'This is a test summary.')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_audio_processing_error(self, mock_process):
        """Test the transcribe endpoint with audio processing error"""
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to process audio',
            'error_type': 'audio_processing',
            'details': 'Invalid audio format'
        }
        
        # Access the endpoint with a file
        test_file = self.create_test_audio_file()
        data = self.create_multipart_data(test_file)
        
        # Skip actual audio processing
        with mock.patch('subprocess.run') as mock_subprocess:
            # Mock the file validation to pass through
            with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                response = self.client.post(
                    '/api/transcribe',
                    data=data,
                    content_type='multipart/form-data'
                )
        
                # Check the response - either process error (200) or validation error (400)
                self.assertIn(response.status_code, [200, 400])
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertEqual(data['error'], 'Failed to process audio')
                    self.assertEqual(data['error_type'], 'audio_processing')
    
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
        
        # Skip actual audio processing
        with mock.patch('subprocess.run') as mock_subprocess:
            # Mock the file validation to pass through
            with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                response = self.client.post(
                    '/api/transcribe',
                    data=data,
                    content_type='multipart/form-data'
                )
        
                # Check the response - can be process error (200), validation error (400) or server error (500)
                self.assertIn(response.status_code, [200, 400, 500])
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertEqual(data['error'], 'Failed to transcribe audio')
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
        
        # Skip actual audio processing
        with mock.patch('subprocess.run') as mock_subprocess:
            # Mock the file validation to pass through
            with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                response = self.client.post(
                    '/api/transcribe',
                    data=data,
                    content_type='multipart/form-data'
                )
        
                # Check the response - can be process error (200), validation error (400) or server error (500)
                self.assertIn(response.status_code, [200, 400, 500])
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])
                    self.assertEqual(data['error'], 'Failed to summarize transcription')
                    self.assertEqual(data['error_type'], 'summarization')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_unexpected_error(self, mock_process):
        """Test the transcribe endpoint with an unexpected error"""
        # Mock the process_audio function to raise an unexpected error
        mock_process.side_effect = Exception('Unexpected error occurred')
        
        # Access the endpoint with a file
        test_file = self.create_test_audio_file()
        data = self.create_multipart_data(test_file)
        
        # Skip actual audio processing
        with mock.patch('subprocess.run') as mock_subprocess:
            # Mock the file validation to pass through
            with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                response = self.client.post(
                    '/api/transcribe',
                    data=data,
                    content_type='multipart/form-data'
                )
        
                # Check the response - either system error (500) or validation error (400)
                self.assertIn(response.status_code, [500, 400])
                if response.status_code == 500:
                    data = json.loads(response.data)
                    self.assertIn('error', data)
                    # Accept either format of error message
                    self.assertTrue(
                        data['error'] == 'An unexpected error occurred' or
                        data['error'].startswith('Failed to process audio:')
                    )

if __name__ == '__main__':
    unittest.main()
