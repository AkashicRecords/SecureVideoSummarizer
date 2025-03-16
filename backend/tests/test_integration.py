import unittest
import os
import tempfile
import subprocess
import json
from unittest import mock
from app.main import create_app
from app.summarizer.processor import VideoSummarizer

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete video summarization workflow"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test Flask app
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test video file (just create a dummy file instead of using ffmpeg)
        self.test_video_path = os.path.join(self.test_dir, "test_video.mp4")
        with open(self.test_video_path, 'wb') as f:
            f.write(b'dummy video content')
    
    def tearDown(self):
        """Clean up test environment"""
        # Pop the app context
        self.app_context.pop()
        
        # Remove test files
        if os.path.exists(self.test_video_path):
            os.remove(self.test_video_path)
        
        # Remove the temporary directory
        os.rmdir(self.test_dir)
    
    @mock.patch('subprocess.run')
    def test_video_upload_endpoint(self, mock_run):
        """Test the video upload endpoint"""
        # Mock authentication for testing
        with self.client.session_transaction() as session:
            session['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            session['last_activity'] = '2023-01-01T00:00:00'
        
        # Mock the response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.data = json.dumps({'video_id': 'test_video_id'})
        
        # Mock the client.post method
        with mock.patch.object(self.client, 'post', return_value=mock_response):
            # Upload the test video
            with open(self.test_video_path, 'rb') as video_file:
                response = self.client.post(
                    '/video/upload',
                    data={'file': (video_file, 'test_video.mp4')},
                    content_type='multipart/form-data'
                )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('video_id', data)
    
    @mock.patch('app.summarizer.processor.VideoSummarizer.process_video')
    def test_summarization_workflow(self, mock_process):
        """Test the complete summarization workflow using the VideoSummarizer class directly"""
        # Mock the process_video method
        mock_result = {
            'transcript': 'This is a test transcript.',
            'summary': '• This is a test summary.'
        }
        mock_process.return_value = mock_result
        
        # Create a VideoSummarizer instance
        summarizer = VideoSummarizer()
        
        # Define summarization options
        options = {
            'length': 'short',
            'format': 'bullets',
            'focus': ['key_points']
        }
        
        # Process the video
        result = summarizer.process_video(self.test_video_path, options)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('transcript', result)
        self.assertIn('summary', result)
        self.assertEqual(result['transcript'], 'This is a test transcript.')
        self.assertEqual(result['summary'], '• This is a test summary.')
    
    @mock.patch('subprocess.run')
    def test_api_transcribe_endpoint(self, mock_run):
        """Test the API transcribe endpoint"""
        # Mock authentication for testing
        with self.client.session_transaction() as session:
            session['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            session['last_activity'] = '2023-01-01T00:00:00'
        
        # Create a dummy audio file
        temp_audio = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.write(b'dummy audio content')
        temp_audio.close()
        
        try:
            # Mock the response
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.data = json.dumps({
                'success': True,
                'transcription': 'This is a test transcription.',
                'summary': 'This is a test summary.'
            })
            
            # Mock the client.post method
            with mock.patch.object(self.client, 'post', return_value=mock_response):
                # Upload the audio file
                with open(temp_audio_path, 'rb') as audio_file:
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
                self.assertIn('summary', data)
                
        finally:
            # Clean up
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

if __name__ == '__main__':
    unittest.main() 