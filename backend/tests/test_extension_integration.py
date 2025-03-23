import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest import mock
from flask import session
from app.main import create_app

class TestExtensionIntegration(unittest.TestCase):
    """Integration tests for browser extension API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for summaries
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'GOOGLE_CLIENT_SECRETS_FILE': 'dummy_path',
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'EXTENSION_ID_PLACEHOLDER',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://EXTENSION_ID_PLACEHOLDER',
            'SUMMARIES_DIR': self.temp_dir
        })
        self.env_patcher.start()
        
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        self.app.config['ALLOWED_ORIGINS'] = 'http://localhost:3000,chrome-extension://EXTENSION_ID_PLACEHOLDER'
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Enable cookies/sessions for the test client
        self.client.testing = True
        
    def tearDown(self):
        """Clean up after tests"""
        # Stop patchers
        self.env_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_complete_extension_flow(self):
        """Test the complete extension flow from status check to saving summary"""
        # 1. Check extension status
        response = self.client.get(
            '/api/extension/status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'connected')
        
        # 2. Setup extension job in session
        with self.client.session_transaction() as sess:
            job_id = 'test-job-123'
            sess['extension_jobs'] = {
                job_id: {
                    'status': 'processing',
                    'timestamp': datetime.now().timestamp(),
                    'summary': None,
                    'error': None
                }
            }
        
        # 3. Check summary status when processing
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'processing')
        
        # 4. Update job to completed
        with self.client.session_transaction() as sess:
            sess['extension_jobs'][job_id]['status'] = 'complete'
            sess['extension_jobs'][job_id]['summary'] = 'This is a test summary.'
        
        # 5. Check summary status when complete
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'complete')
        self.assertEqual(data['summary'], 'This is a test summary.')
        
        # 6. Save the summary
        response = self.client.post(
            '/api/extension/save_summary',
            data=json.dumps({
                'summary': 'This is a test summary.',
                'video_data': {
                    'title': 'Test Video',
                    'duration': 120,
                    'src': 'https://example.com/video.mp4'
                }
            }),
            content_type='application/json',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
    def test_error_handling(self):
        """Test error handling in the extension flow"""
        # 1. Test missing required fields
        response = self.client.post(
            '/api/extension/save_summary',
            data=json.dumps({
                'summary': 'Test summary'
                # Missing video_data
            }),
            content_type='application/json',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        # Some error information should be present in the response
        self.assertIn('error', data)
        
        # 2. Test unauthorized access
        response = self.client.get(
            '/api/extension/status',
            headers={'Origin': 'https://malicious-site.com'}
        )
        
        self.assertEqual(response.status_code, 403)
        
        # 3. Test error status handling
        with self.client.session_transaction() as sess:
            job_id = 'test-job-error'
            sess['extension_jobs'] = {
                job_id: {
                    'status': 'error',
                    'timestamp': datetime.now().timestamp(),
                    'summary': None,
                    'error': 'Test error message'
                }
            }
        
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Test error message')
        
    def test_session_management(self):
        """Test session management for summary status"""
        # 1. Set up a job in the session
        with self.client.session_transaction() as sess:
            job_id = 'test-job-456'
            sess['extension_jobs'] = {
                job_id: {
                    'status': 'processing',
                    'timestamp': datetime.now().timestamp(),
                    'summary': None,
                    'error': None
                }
            }
        
        # 2. Check that status is correctly retrieved
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'processing')
        
        # 3. Change status to completed with a summary
        test_summary = "Completed summary text."
        with self.client.session_transaction() as sess:
            sess['extension_jobs'][job_id]['status'] = 'complete'
            sess['extension_jobs'][job_id]['summary'] = test_summary
        
        # 4. Check that both status and summary are correctly retrieved
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'complete')
        self.assertEqual(data['summary'], test_summary)

if __name__ == '__main__':
    unittest.main() 