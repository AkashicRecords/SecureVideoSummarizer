import unittest
import os
import json
import tempfile
import shutil
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
        self.app.config['SUMMARIES_DIR'] = self.temp_dir
        
        # Enable sessions in testing
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        self.app_context.pop()
        
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
        
        # 2. Check summary status when idle
        with self.client.session_transaction() as sess:
            sess['summary_status'] = 'idle'
            sess['summary_text'] = None
        
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'idle')
        self.assertNotIn('summary', data)
        
        # 3. Check summary status when processing
        with self.client.session_transaction() as sess:
            sess['summary_status'] = 'processing'
            sess['summary_text'] = None
        
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'processing')
        self.assertNotIn('summary', data)
        
        # 4. Check summary status when completed
        test_summary = "This is a test summary of the video content."
        with self.client.session_transaction() as sess:
            sess['summary_status'] = 'completed'
            sess['summary_text'] = test_summary
        
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['summary'], test_summary)
        
        # 5. Save the summary
        test_video_data = {
            'title': 'Integration Test Video',
            'duration': 180,
            'src': 'https://example.com/test-video.mp4',
            'platform': 'olympus'
        }
        
        response = self.client.post(
            '/api/extension/save_summary',
            data=json.dumps({
                'summary': test_summary,
                'video_data': test_video_data
            }),
            content_type='application/json',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # 6. Verify the summary was saved to a file
        summary_files = os.listdir(self.temp_dir)
        self.assertGreater(len(summary_files), 0)
        
        # Read the saved summary file
        with open(os.path.join(self.temp_dir, summary_files[0]), 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['summary'], test_summary)
        self.assertEqual(saved_data['video_data']['title'], test_video_data['title'])
    
    def test_error_handling(self):
        """Test error handling in the extension flow"""
        # 1. Test invalid request data for save summary
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
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid request data')
        
        # 2. Test unauthorized access
        response = self.client.get(
            '/api/extension/status',
            headers={'Origin': 'https://malicious-site.com'}
        )
        
        self.assertEqual(response.status_code, 403)
        
        # 3. Test save summary failure
        test_summary = "This is a test summary."
        test_video_data = {
            'title': 'Test Video',
            'duration': 120
        }
        
        # Mock save_summary to return False (failure)
        with mock.patch('app.api.routes.save_summary', return_value=False):
            response = self.client.post(
                '/api/extension/save_summary',
                data=json.dumps({
                    'summary': test_summary,
                    'video_data': test_video_data
                }),
                content_type='application/json',
                headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
            )
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['error'], 'Failed to save summary')
    
    def test_session_management(self):
        """Test session management for summary status"""
        # 1. Set summary status to processing
        with self.client.session_transaction() as sess:
            sess['summary_status'] = 'processing'
        
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
            sess['summary_status'] = 'completed'
            sess['summary_text'] = test_summary
        
        # 4. Check that both status and summary are correctly retrieved
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['summary'], test_summary)
        
        # 5. Change status to error
        with self.client.session_transaction() as sess:
            sess['summary_status'] = 'error'
            sess['summary_text'] = None
        
        # 6. Check that error status is correctly retrieved
        response = self.client.get(
            '/api/extension/summary_status',
            headers={'Origin': 'chrome-extension://EXTENSION_ID_PLACEHOLDER'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertNotIn('summary', data)

if __name__ == '__main__':
    unittest.main() 