import unittest
import json
import os
import io
import sys
from unittest.mock import MagicMock, patch
from flask import session, Flask

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app import create_app
from app.utils.olympus_processor import is_olympus_url, extract_video_id, process_olympus_transcript

class TestOlympusRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SERVER_NAME'] = 'localhost'
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
    def tearDown(self):
        self.app_context.pop()
    
    def test_olympus_url_detection(self):
        # Test valid Olympus URLs
        self.assertTrue(is_olympus_url("https://olympus.com/video/12345"))
        self.assertTrue(is_olympus_url("https://mygreatlearning.com/olympus/course/video"))
        self.assertTrue(is_olympus_url("https://olympuslearning.com/video?id=12345"))
        
        # Test invalid URLs
        self.assertFalse(is_olympus_url("https://youtube.com/watch?v=12345"))
        self.assertFalse(is_olympus_url("https://example.com/video"))
    
    def test_extract_video_id(self):
        # Test with videoId parameter
        video_id = extract_video_id("https://olympus.com/video?videoId=12345")
        self.assertEqual(video_id, "12345")
        
        # Test with id parameter
        video_id = extract_video_id("https://olympus.com/video?id=67890")
        self.assertEqual(video_id, "67890")
        
        # Test with path component
        video_id = extract_video_id("https://olympus.com/video/v-abcde")
        self.assertEqual(video_id, "v-abcde")
        
        # Test with numeric path component
        video_id = extract_video_id("https://olympus.com/video/54321")
        self.assertEqual(video_id, "54321")
        
        # Test fallback to last path component
        video_id = extract_video_id("https://olympus.com/course/lesson")
        self.assertEqual(video_id, "lesson")
    
    @patch('app.summarizer.processor.summarize_text_enhanced')
    def test_process_olympus_transcript(self, mock_summarize):
        # Mock the summarizer
        mock_summarize.return_value = "This is a summary of the video content."
        
        # Create test transcript data
        transcript_data = {
            "text": "This is the transcript text of the video from Olympus platform.",
            "title": "Test Olympus Video",
            "video_id": "test-123"
        }
        
        # Process the transcript
        result = process_olympus_transcript(transcript_data)
        
        # Verify the result
        self.assertEqual(result["title"], "Test Olympus Video")
        self.assertEqual(result["transcript"], transcript_data["text"])
        self.assertEqual(result["summary"], "This is a summary of the video content.")
        self.assertEqual(result["source"], "olympus")
        self.assertEqual(result["video_id"], "test-123")
        
    @patch('app.api.olympus_routes.validate_extension_origin')
    def test_olympus_status_endpoint(self, mock_validate):
        # Mock the validation to always return True
        mock_validate.return_value = True
        
        # Test the status endpoint
        response = self.client.get('/api/olympus/status')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["available"])
        self.assertIn("extension_id", data)
        self.assertIn("supported_features", data)
        
    @patch('app.api.olympus_routes.validate_extension_origin')
    @patch('app.api.olympus_routes.process_olympus_transcript')
    def test_olympus_capture_endpoint(self, mock_process, mock_validate):
        # Mock the validation and processing
        mock_validate.return_value = True
        mock_process.return_value = {
            "transcript": "Test transcript",
            "summary": "Test summary",
            "title": "Test Video",
            "timestamp": 1234567890,
            "source": "olympus",
            "video_id": "test-123"
        }
        
        # Test data
        test_data = {
            "transcript": "Test transcript",
            "title": "Test Video",
            "video_id": "test-123",
            "options": {
                "max_length": 100,
                "min_length": 20
            }
        }
        
        # Test the capture endpoint
        response = self.client.post(
            '/api/olympus/capture',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["summary"], "Test summary")
        self.assertEqual(data["title"], "Test Video")
        self.assertEqual(data["video_id"], "test-123")

if __name__ == '__main__':
    unittest.main()