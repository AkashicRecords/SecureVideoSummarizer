import os
import json
import tempfile
import shutil
from unittest import mock
from datetime import datetime

class TestFixtures:
    """Common test fixtures for the application."""
    
    @staticmethod
    def create_test_user():
        """Create a test user data."""
        return {
            'id': 'test_user_id',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg'
        }
    
    @staticmethod
    def create_test_video():
        """Create test video data."""
        return {
            'title': 'Test Video',
            'duration': 180,
            'src': 'https://example.com/test-video.mp4',
            'platform': 'olympus',
            'current_time': 45,
            'playback_rate': 1.0
        }
    
    @staticmethod
    def create_test_summary():
        """Create test summary data."""
        return {
            'summary': 'This is a test summary of the video content.',
            'video_data': TestFixtures.create_test_video(),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_test_session():
        """Create test session data."""
        return {
            'summary_status': 'idle',
            'summary_text': None,
            'user_id': 'test_user_id',
            'access_token': 'test_access_token'
        }
    
    @staticmethod
    def create_test_audio_file(duration=10, sample_rate=16000):
        """Create a test audio file."""
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, 'test_audio.wav')
        with open(audio_path, 'w') as f:
            f.write('dummy audio content' * (duration * sample_rate // 16))
        return audio_path, temp_dir
    
    @staticmethod
    def create_test_summary_file(summary_data):
        """Create a test summary file."""
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'summary_{timestamp}.json'
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(summary_data, f)
        
        return file_path, temp_dir
    
    @staticmethod
    def create_test_extension_headers(extension_id='EXTENSION_ID_PLACEHOLDER'):
        """Create extension request headers."""
        return {'Origin': f'chrome-extension://{extension_id}'}
    
    @staticmethod
    def create_test_google_auth_response():
        """Create a mock Google auth response."""
        return {
            'access_token': 'mock_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    @staticmethod
    def create_test_google_userinfo_response():
        """Create a mock Google userinfo response."""
        return {
            'sub': '123456789',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/picture.jpg'
        }
    
    @staticmethod
    def create_test_error_response(error_message):
        """Create a test error response."""
        return {
            'success': False,
            'error': error_message
        }
    
    @staticmethod
    def create_test_success_response(data=None):
        """Create a test success response."""
        response = {'success': True}
        if data is not None:
            response.update(data)
        return response
    
    @staticmethod
    def cleanup_temp_dir(temp_dir):
        """Clean up a temporary directory."""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @staticmethod
    def mock_audio_processing():
        """Create mocks for audio processing functions."""
        with mock.patch('app.summarizer.processor') as mock_processor:
            mock_processor.convert_to_wav_enhanced.return_value = 'test_audio.wav'
            mock_processor.validate_audio.return_value = True
            mock_processor.transcribe_audio_enhanced.return_value = 'Test transcription'
            mock_processor.summarize_text_enhanced.return_value = 'Test summary'
            return mock_processor
    
    @staticmethod
    def mock_file_operations():
        """Create mocks for file operations."""
        with mock.patch('os.path.exists') as mock_exists, \
             mock.patch('os.path.getsize') as mock_size, \
             mock.patch('os.makedirs') as mock_makedirs:
            mock_exists.return_value = True
            mock_size.return_value = 1000
            mock_makedirs.return_value = None
            return mock_exists, mock_size, mock_makedirs 