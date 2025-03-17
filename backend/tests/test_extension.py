import unittest
import os
import json
from unittest import mock
from app.main import create_app

class TestExtensionAPI(unittest.TestCase):
    """Test cases for browser extension API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'GOOGLE_CLIENT_SECRETS_FILE': 'dummy_path',
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'EXTENSION_ID_PLACEHOLDER',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://EXTENSION_ID_PLACEHOLDER'
        })
        self.env_patcher.start()
        
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        self.app.config['ALLOWED_ORIGINS'] = 'http://localhost:3000,chrome-extension://EXTENSION_ID_PLACEHOLDER'
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        self.app_context.pop()
    
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
    
    def test_summary_status_endpoint(self):
        """Test the summary status endpoint"""
        # Test when no summary is in progress
        response = self.client.get('/api/extension/summary_status')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'idle')
        
        # Mock a summary in progress
        with mock.patch('app.api.routes.get_summary_status', return_value=('processing', None)):
            response = self.client.get('/api/extension/summary_status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'processing')
        
        # Mock a completed summary
        summary_text = "This is a test summary of the video."
        with mock.patch('app.api.routes.get_summary_status', return_value=('completed', summary_text)):
            response = self.client.get('/api/extension/summary_status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'completed')
            self.assertEqual(data['summary'], summary_text)
    
    def test_save_summary_endpoint(self):
        """Test the save summary endpoint"""
        test_data = {
            'summary': 'This is a test summary.',
            'video_data': {
                'title': 'Test Video',
                'duration': 120,
                'src': 'https://example.com/video.mp4',
                'platform': 'olympus'
            }
        }
        
        # Mock successful save
        with mock.patch('app.api.routes.save_summary', return_value=True):
            response = self.client.post(
                '/api/extension/save_summary',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
        
        # Mock failed save
        with mock.patch('app.api.routes.save_summary', return_value=False):
            response = self.client.post(
                '/api/extension/save_summary',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
    
    def test_unauthorized_access(self):
        """Test unauthorized access to extension endpoints"""
        # Test with incorrect Origin header
        response = self.client.get(
            '/api/extension/status',
            headers={'Origin': 'https://malicious-site.com'}
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_cors_headers(self):
        """Test CORS headers in response"""
        response = self.client.get(
            '/api/extension/status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'],
            'chrome-extension://EXTENSION_ID_PLACEHOLDER'
        )

if __name__ == '__main__':
    unittest.main()