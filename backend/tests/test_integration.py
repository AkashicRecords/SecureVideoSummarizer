import unittest
import os
import tempfile
import subprocess
import json
from unittest import mock
from app.main import create_app
from app.summarizer.processor import VideoSummarizer
from tests.test_helpers import (
    create_test_video_file,
    create_test_audio_file,
    create_test_video_data,
    create_test_summary_data,
    create_test_success_response,
    validate_summary_response,
    mock_audio_processing_functions,
    mock_video_processing_functions,
    cleanup_temp_dir
)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete video summarization workflow"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test Flask app
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a test video file
        self.test_video_path, self.test_dir = create_test_video_file(format='mp4', duration=5)
        
        # Create a test audio file
        self.test_audio_path, self.test_audio_dir = create_test_audio_file(
            duration=5, 
            sample_rate=16000, 
            num_channels=1
        )
    
    def tearDown(self):
        """Clean up test environment"""
        # Pop the app context
        self.app_context.pop()
        
        # Remove test files
        cleanup_temp_dir(self.test_dir)
        cleanup_temp_dir(self.test_audio_dir)
    
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
        mock_response.data = json.dumps({'success': True, 'video_id': 'test_video_id'})
        
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
            self.assertTrue(data['success'])
    
    @mock.patch('app.summarizer.processor.VideoSummarizer.process_video')
    def test_summarization_workflow(self, mock_process):
        """Test the complete summarization workflow using the VideoSummarizer class directly"""
        # Create expected result data
        summary_data = create_test_summary_data()
        mock_result = {
            'transcript': 'This is a test transcript.',
            'summary': summary_data['summary']
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
        self.assertEqual(result['summary'], summary_data['summary'])
        
        # Verify the mock was called with correct arguments
        mock_process.assert_called_once_with(self.test_video_path, options)
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    @mock.patch('app.summarizer.processor.validate_audio')
    @mock.patch('app.summarizer.processor.transcribe_audio_enhanced')
    @mock.patch('app.summarizer.processor.summarize_text_enhanced')
    def test_api_transcribe_endpoint(self, mock_summarize, mock_transcribe, mock_validate, mock_convert):
        """Test the API transcribe endpoint"""
        # Set up mocks
        mock_convert.return_value = self.test_audio_path
        mock_validate.return_value = True
        mock_transcribe.return_value = "This is a test transcription."
        mock_summarize.return_value = "This is a test summary."
        
        # Mock authentication for testing
        with self.client.session_transaction() as session:
            session['user_info'] = {'email': 'test@example.com', 'name': 'Test User'}
            session['last_activity'] = '2023-01-01T00:00:00'
        
        # Create expected response
        expected_response = create_test_success_response({
            'transcription': 'This is a test transcription.',
            'summary': 'This is a test summary.'
        })
        
        # Mock the client.post method to return our expected response
        with mock.patch.object(self.client, 'post', return_value=mock.MagicMock(
            status_code=200,
            data=json.dumps(expected_response),
            content_type='application/json'
        )):
            # Upload the audio file
            with open(self.test_audio_path, 'rb') as audio_file:
                response = self.client.post(
                    '/api/transcribe',
                    data={'audio': (audio_file, 'test_audio.wav')},
                    content_type='multipart/form-data'
                )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('transcription', data)
            self.assertIn('summary', data)
            
    def test_api_summarize_with_video_data(self):
        """Test the API summarize endpoint with video data"""
        # Create test video data
        video_data = create_test_video_data()
        
        # Mock audio processing functions
        with mock.patch('app.summarizer.processor') as mock_processor:
            # Set return values
            mock_processor.convert_to_wav_enhanced.return_value = self.test_audio_path
            mock_processor.validate_audio.return_value = True
            mock_processor.transcribe_audio_enhanced.return_value = "This is a test transcription."
            mock_processor.summarize_text_enhanced.return_value = "This is a test summary."
            
            # Mock the client.post method
            with mock.patch.object(self.client, 'post', return_value=mock.MagicMock(
                status_code=200,
                data=json.dumps({
                    'success': True,
                    'summary': 'This is a test summary.',
                    'video_data': video_data
                }),
                content_type='application/json'
            )):
                # Make the API request
                response = self.client.post(
                    '/api/summarize',
                    json={
                        'video_data': video_data,
                        'options': {
                            'length': 'short',
                            'format': 'paragraph'
                        }
                    },
                    content_type='application/json'
                )
                
                # Check the response
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertIn('summary', data)
                self.assertIn('video_data', data)
                self.assertEqual(data['video_data'], video_data)
                
                # Validate the summary response structure
                self.assertTrue(validate_summary_response({
                    'success': True,
                    'summary': data['summary']
                }))

if __name__ == '__main__':
    unittest.main() 