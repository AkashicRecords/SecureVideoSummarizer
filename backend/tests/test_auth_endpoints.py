import unittest
import os
import json
from unittest import mock
from datetime import datetime, timedelta
from app.main import create_app
from app.utils.errors import AuthenticationError
from functools import wraps

# Create a mock login_required decorator that passes through the function
def mock_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

class TestAuthEndpoints(unittest.TestCase):
    """Test cases for authentication endpoints"""
    
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
        
        # Set up client secrets patcher
        self.secrets_patcher = mock.patch('app.auth.routes.get_client_secrets_file')
        self.mock_get_secrets = self.secrets_patcher.start()
        self.mock_get_secrets.return_value = 'dummy_path'
        
        # Set up login_required patcher
        self.login_required_patcher = mock.patch('app.auth.routes.login_required', mock_login_required)
        self.login_required_patcher.start()
    
    def tearDown(self):
        """Clean up test environment"""
        # Pop the app context
        self.app_context.pop()
        
        # Stop patchers
        self.login_required_patcher.stop()
        self.secrets_patcher.stop()
        self.env_patcher.stop()
    
    @mock.patch('google_auth_oauthlib.flow.Flow.from_client_secrets_file')
    def test_login_endpoint(self, mock_flow_from_secrets):
        """Test the login endpoint"""
        # Mock the Flow instance
        mock_flow_instance = mock.MagicMock()
        mock_flow_instance.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/auth?mock=true', 'state_token')
        mock_flow_from_secrets.return_value = mock_flow_instance
        
        # Access the login endpoint
        response = self.client.get('/auth/login')
        
        # Check that the response is a redirect to Google's auth page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].startswith('https://accounts.google.com/o/oauth2/auth'))
    
    @mock.patch('google_auth_oauthlib.flow.Flow.from_client_secrets_file')
    @mock.patch('app.auth.routes.get_user_info')
    def test_callback_endpoint_success(self, mock_get_user_info, mock_flow_from_secrets):
        """Test the callback endpoint with successful authentication"""
        # Mock the Flow instance
        mock_flow_instance = mock.MagicMock()
        mock_credentials = mock.MagicMock()
        mock_credentials.token = 'mock_token'
        mock_credentials.refresh_token = 'mock_refresh_token'
        mock_credentials.token_uri = 'https://oauth2.googleapis.com/token'
        mock_credentials.client_id = 'mock_client_id'
        mock_credentials.client_secret = 'mock_client_secret'
        mock_credentials.scopes = ['profile', 'email']
        mock_flow_instance.credentials = mock_credentials
        mock_flow_from_secrets.return_value = mock_flow_instance
        
        # Mock the user info
        mock_get_user_info.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/profile.jpg',
            'email_verified': True
        }
        
        # Set up the session with a state token
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'valid_state'
        
        # Access the callback endpoint
        response = self.client.get('/auth/callback?state=valid_state&code=mock_code')
        
        # Check that the response is a redirect to the frontend
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].startswith('http://localhost:3000'))
        
        # Check that the session contains the user info
        with self.client.session_transaction() as sess:
            self.assertIn('user_info', sess)
            self.assertEqual(sess['user_info']['email'], 'test@example.com')
            self.assertEqual(sess['user_info']['name'], 'Test User')
            self.assertIn('credentials', sess)
            self.assertIn('last_activity', sess)
    
    def test_callback_endpoint_error(self):
        """Test the callback endpoint with authentication error"""
        # Set up the session with a state token
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = 'valid_state'
        
        # Mock get_client_secrets_file to raise an exception
        with mock.patch('app.auth.routes.get_client_secrets_file') as mock_get_secrets:
            mock_get_secrets.side_effect = FileNotFoundError("Google client secrets file not found")
            
            # Access the callback endpoint
            response = self.client.get('/auth/callback?state=valid_state&code=mock_code')
        
        # Check that the response is a redirect to the frontend with an error
        self.assertEqual(response.status_code, 302)
        self.assertTrue('error' in response.headers['Location'])
    
    def test_logout_endpoint(self):
        """Test the logout endpoint"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            sess['credentials'] = {'token': 'mock_token'}
            sess['last_activity'] = datetime.utcnow().isoformat()
        
        # Access the logout endpoint
        response = self.client.post('/auth/logout')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Successfully logged out')
        
        # Check that the session no longer contains the user info
        with self.client.session_transaction() as sess:
            self.assertNotIn('user_info', sess)
            self.assertNotIn('credentials', sess)
            self.assertNotIn('last_activity', sess)
    
    def test_current_user_endpoint_authenticated(self):
        """Test the current user endpoint with an authenticated user"""
        # Set up a session with user info
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            sess['last_activity'] = datetime.utcnow().isoformat()
        
        # Access the current user endpoint
        response = self.client.get('/auth/user')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['name'], 'Test User')
    
    def test_current_user_endpoint_unauthenticated(self):
        """Test the current user endpoint with an unauthenticated user"""
        # Access the current user endpoint without a session
        response = self.client.get('/auth/user')
        
        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Authentication required')
    
    @mock.patch('app.auth.routes.Credentials')
    def test_refresh_token_endpoint_success(self, mock_credentials_class):
        """Test the refresh token endpoint with successful refresh"""
        # Set up a session with credentials
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            sess['credentials'] = {
                'token': 'old_token',
                'refresh_token': 'mock_refresh_token',
                'token_uri': 'token_uri',
                'client_id': 'client_id',
                'client_secret': 'client_secret',
                'scopes': ['scope1', 'scope2'],
                'expiry': (datetime.utcnow() - timedelta(hours=1)).isoformat()  # Expired token
            }
            sess['last_activity'] = datetime.utcnow().isoformat()
        
        # Mock the credentials
        mock_creds_instance = mock.MagicMock()
        mock_creds_instance.token = 'new_token'
        mock_creds_instance.refresh_token = 'mock_refresh_token'
        mock_creds_instance.expired = True
        mock_credentials_class.return_value = mock_creds_instance
        
        # Access the refresh token endpoint
        response = self.client.post('/auth/refresh-token')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertEqual(data['access_token'], 'new_token')
    
    def test_refresh_token_endpoint_unauthenticated(self):
        """Test the refresh token endpoint with an unauthenticated user"""
        # Access the refresh token endpoint without a session
        response = self.client.post('/auth/refresh-token')
        
        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No credentials found')
    
    @mock.patch('app.auth.routes.Credentials')
    def test_refresh_token_endpoint_error(self, mock_credentials_class):
        """Test the refresh token endpoint with a refresh error"""
        # Set up a session with credentials
        with self.client.session_transaction() as sess:
            sess['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            sess['credentials'] = {
                'token': 'old_token',
                'refresh_token': 'mock_refresh_token',
                'token_uri': 'token_uri',
                'client_id': 'client_id',
                'client_secret': 'client_secret',
                'scopes': ['scope1', 'scope2'],
                'expiry': (datetime.utcnow() - timedelta(hours=1)).isoformat()  # Expired token
            }
            sess['last_activity'] = datetime.utcnow().isoformat()
        
        # Mock the credentials to raise an exception during refresh
        mock_creds_instance = mock.MagicMock()
        mock_creds_instance.expired = True
        mock_creds_instance.refresh.side_effect = Exception("Token refresh failed")
        mock_credentials_class.return_value = mock_creds_instance
        
        # Access the refresh token endpoint
        response = self.client.post('/auth/refresh-token')
        
        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Token refresh failed, please login again')

if __name__ == '__main__':
    unittest.main() 