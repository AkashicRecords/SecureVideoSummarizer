import unittest
import os
import tempfile
import json
from unittest import mock
from io import BytesIO
from flask import jsonify, session
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
            'GOOGLE_CLIENT_SECRETS_FILE': 'dummy_path',
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'dummy_extension_id',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://dummy_extension_id'
        })
        self.env_patcher.start()
        
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        self.app.config['ALLOWED_ORIGINS'] = 'http://localhost:3000,chrome-extension://dummy_extension_id'
        self.app.config['SESSION_TYPE'] = 'filesystem'
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test audio file
        self.test_audio_path = os.path.join(self.test_dir, "test_audio.webm")
        with open(self.test_audio_path, 'wb') as f:
            f.write(b'dummy audio content')
            
        # Set up client secrets patcher
        self.secrets_patcher = mock.patch('app.auth.routes.get_client_secrets_file')
        self.mock_get_secrets = self.secrets_patcher.start()
        self.mock_get_secrets.return_value = 'dummy_path'
        
        # Patch the login_required decorator in the auth routes module
        self.login_required_patcher = mock.patch('app.api.routes.login_required', mock_login_required)
        self.login_required_patcher.start()
    
    def tearDown(self):
        """Clean up test environment"""
        # Pop the app context
        self.app_context.pop()
        
        # Remove test files
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
        
        # Remove the temporary directory
        os.rmdir(self.test_dir)
        
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
        # Temporarily restore the original login_required behavior
        with mock.patch('app.api.routes.login_required') as mock_login_required:
            # Create a decorator that returns a 401 response
            def unauthorized_decorator(f):
                @wraps(f)
                def decorated(*args, **kwargs):
                    return jsonify({'error': 'Authentication required'}), 401
                return decorated
            
            mock_login_required.return_value = unauthorized_decorator
            
            # Attempt to access the endpoint without authentication
            with open(self.test_audio_path, 'rb') as audio_file:
                response = self.client.post(
                    '/api/transcribe',
                    data={'audio': (audio_file, 'test_audio.webm')},
                    content_type='multipart/form-data'
                )
            
            # Check that the response is unauthorized
            self.assertEqual(response.status_code, 401)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Authentication required')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_no_file(self, mock_process):
        """Test the transcribe endpoint with no file"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
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
        self.assertEqual(data['error'], 'No audio file provided')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_success(self, mock_process):
        """Test the transcribe endpoint with successful processing"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
        # Mock the process_audio function
        mock_process.return_value = {
            'success': True,
            'transcription': 'This is a test transcription.',
            'summary': 'This is a test summary.'
        }
        
        # Access the endpoint with a file
        with open(self.test_audio_path, 'rb') as audio_file:
            response = self.client.post(
                '/api/transcribe',
                data={'audio': (audio_file, 'test_audio.webm')},
                content_type='multipart/form-data'
            )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('transcription', data)
        self.assertEqual(data['transcription'], 'This is a test transcription.')
        self.assertIn('summary', data)
        self.assertEqual(data['summary'], 'This is a test summary.')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_audio_processing_error(self, mock_process):
        """Test the transcribe endpoint with audio processing error"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to process audio',
            'error_type': 'audio_processing',
            'details': 'Invalid audio format'
        }
        
        # Access the endpoint with a file
        with open(self.test_audio_path, 'rb') as audio_file:
            response = self.client.post(
                '/api/transcribe',
                data={'audio': (audio_file, 'test_audio.webm')},
                content_type='multipart/form-data'
            )
        
        # Check the response
        self.assertEqual(response.status_code, 200)  # API still returns 200 but with error details
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Failed to process audio')
        self.assertIn('error_type', data)
        self.assertEqual(data['error_type'], 'audio_processing')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_transcription_error(self, mock_process):
        """Test the transcribe endpoint with transcription error"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to transcribe audio',
            'error_type': 'transcription',
            'details': 'Speech recognition service unavailable'
        }
        
        # Access the endpoint with a file
        with open(self.test_audio_path, 'rb') as audio_file:
            response = self.client.post(
                '/api/transcribe',
                data={'audio': (audio_file, 'test_audio.webm')},
                content_type='multipart/form-data'
            )
        
        # Check the response
        self.assertEqual(response.status_code, 200)  # API still returns 200 but with error details
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
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
        # Mock the process_audio function to return an error
        mock_process.return_value = {
            'success': False,
            'error': 'Failed to summarize text',
            'error_type': 'summarization',
            'details': 'Text too short for meaningful summarization'
        }
        
        # Access the endpoint with a file
        with open(self.test_audio_path, 'rb') as audio_file:
            response = self.client.post(
                '/api/transcribe',
                data={'audio': (audio_file, 'test_audio.webm')},
                content_type='multipart/form-data'
            )
        
        # Check the response
        self.assertEqual(response.status_code, 200)  # API still returns 200 but with error details
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Failed to summarize text')
        self.assertIn('error_type', data)
        self.assertEqual(data['error_type'], 'summarization')
    
    @mock.patch('app.api.routes.process_audio')
    def test_transcribe_endpoint_unexpected_error(self, mock_process):
        """Test the transcribe endpoint with an unexpected error"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
        
        # Mock the process_audio function to raise an exception
        mock_process.side_effect = Exception("Unexpected error")
        
        # Access the endpoint with a file
        with open(self.test_audio_path, 'rb') as audio_file:
            response = self.client.post(
                '/api/transcribe',
                data={'audio': (audio_file, 'test_audio.webm')},
                content_type='multipart/form-data'
            )
        
        # Check the response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'An unexpected error occurred')
        self.assertIn('details', data)

if __name__ == '__main__':
    unittest.main() 