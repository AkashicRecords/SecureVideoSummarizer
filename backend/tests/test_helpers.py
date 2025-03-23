import os
import json
import tempfile
import shutil
import wave
import numpy as np
from unittest import mock
from datetime import datetime
from tests.test_constants import (
    TEST_USER_ID,
    TEST_USER_EMAIL,
    TEST_USER_NAME,
    TEST_USER_PICTURE,
    TEST_VIDEO_TITLE,
    TEST_VIDEO_DURATION,
    TEST_VIDEO_SRC,
    TEST_VIDEO_PLATFORM,
    TEST_VIDEO_CURRENT_TIME,
    TEST_VIDEO_PLAYBACK_RATE,
    TEST_SUMMARY_TEXT,
    TEST_SESSION_USER_ID,
    TEST_SESSION_ACCESS_TOKEN,
    TEST_SESSION_SUMMARY_STATUS,
    TEST_EXTENSION_ID,
    TEST_GOOGLE_ACCESS_TOKEN,
    TEST_GOOGLE_TOKEN_TYPE,
    TEST_GOOGLE_EXPIRES_IN,
    TEST_GOOGLE_USER_ID,
    TEST_AUDIO_DURATION,
    TEST_AUDIO_SAMPLE_RATE
)

def create_temp_file(content, suffix='.txt'):
    """Create a temporary file with the given content."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, f'test_file{suffix}')
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path, temp_dir

def cleanup_temp_dir(temp_dir):
    """Clean up a temporary directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def mock_google_auth_response():
    """Create a mock Google auth response."""
    return {
        'access_token': TEST_GOOGLE_ACCESS_TOKEN,
        'token_type': TEST_GOOGLE_TOKEN_TYPE,
        'expires_in': TEST_GOOGLE_EXPIRES_IN
    }

def mock_google_userinfo_response():
    """Create a mock Google userinfo response."""
    return {
        'sub': TEST_GOOGLE_USER_ID,
        'email': TEST_USER_EMAIL,
        'name': TEST_USER_NAME,
        'picture': TEST_USER_PICTURE
    }

def create_test_summary_data():
    """Create test summary data."""
    return {
        'summary': TEST_SUMMARY_TEXT,
        'video_data': {
            'title': TEST_VIDEO_TITLE,
            'duration': TEST_VIDEO_DURATION,
            'src': TEST_VIDEO_SRC,
            'platform': TEST_VIDEO_PLATFORM
        }
    }

def create_test_video_data():
    """Create test video data."""
    return {
        'title': TEST_VIDEO_TITLE,
        'duration': TEST_VIDEO_DURATION,
        'src': TEST_VIDEO_SRC,
        'platform': TEST_VIDEO_PLATFORM,
        'current_time': TEST_VIDEO_CURRENT_TIME,
        'playback_rate': TEST_VIDEO_PLAYBACK_RATE
    }

def create_test_video_data_with_options(title=TEST_VIDEO_TITLE, duration=TEST_VIDEO_DURATION, 
                                       platform=TEST_VIDEO_PLATFORM, src=TEST_VIDEO_SRC, 
                                       current_time=TEST_VIDEO_CURRENT_TIME, 
                                       playback_rate=TEST_VIDEO_PLAYBACK_RATE, 
                                       is_virtual=False, in_iframe=False):
    """Create customizable test video data with optional parameters."""
    return {
        'title': title,
        'duration': duration,
        'src': src,
        'platform': platform,
        'current_time': current_time,
        'playback_rate': playback_rate,
        'is_virtual': is_virtual,
        'in_iframe': in_iframe
    }

def create_test_video_file(format='mp4', duration=TEST_AUDIO_DURATION, filename=None):
    """Create a test video file with dummy content.
    
    Args:
        format (str): Video format extension (mp4, avi, etc.)
        duration (int): Duration in seconds
        filename (str, optional): Custom filename
        
    Returns:
        tuple: (file_path, temp_dir)
    """
    temp_dir = tempfile.mkdtemp()
    if not filename:
        filename = f'test_video.{format}'
    video_path = os.path.join(temp_dir, filename)
    
    # Create a dummy file with some content
    with open(video_path, 'wb') as f:
        # Write a simple dummy video file header
        f.write(b'RIFF' + (duration * 100000).to_bytes(4, byteorder='little'))
        # Add some dummy content
        f.write(b'X' * (duration * 100000))
    
    return video_path, temp_dir

def mock_video_processing_functions():
    """Create mocks for video processing functions."""
    with mock.patch('app.video_processor.extract_audio') as mock_extract, \
         mock.patch('app.video_processor.validate_video') as mock_validate:
        mock_extract.return_value = 'test_audio.wav'
        mock_validate.return_value = True
        return mock_extract, mock_validate

def mock_extension_headers(extension_id=TEST_EXTENSION_ID):
    """Create headers for extension requests."""
    return {'Origin': f'chrome-extension://{extension_id}'}

def create_test_audio_file(duration=TEST_AUDIO_DURATION, sample_rate=TEST_AUDIO_SAMPLE_RATE, num_channels=1, filename=None):
    """Create a test audio file with proper WAV format.
    
    Args:
        duration (int): Duration in seconds
        sample_rate (int): Sample rate in Hz
        num_channels (int): Number of audio channels
        filename (str, optional): Custom filename
        
    Returns:
        tuple: (file_path, temp_dir)
    """
    temp_dir = tempfile.mkdtemp()
    if not filename:
        filename = 'test_audio.wav'
    audio_path = os.path.join(temp_dir, filename)
    
    # Generate simple sine wave audio
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Generate a 440 Hz sine wave
    data = np.sin(2 * np.pi * 440 * t) * 32767
    data = data.astype(np.int16)
    
    # Write the data to a WAV file
    with wave.open(audio_path, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2)  # 2 bytes for int16
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data.tobytes())
    
    return audio_path, temp_dir

def mock_audio_processing_functions():
    """Create mocks for audio processing functions."""
    with mock.patch('app.summarizer.processor') as mock_processor:
        mock_processor.convert_to_wav_enhanced.return_value = 'test_audio.wav'
        mock_processor.validate_audio.return_value = True
        mock_processor.transcribe_audio_enhanced.return_value = 'Test transcription'
        mock_processor.summarize_text_enhanced.return_value = 'Test summary'
        return mock_processor

def create_test_session_data():
    """Create test session data."""
    return {
        'summary_status': TEST_SESSION_SUMMARY_STATUS,
        'summary_text': TEST_SESSION_SUMMARY_STATUS,
        'user_id': TEST_SESSION_USER_ID,
        'access_token': TEST_SESSION_ACCESS_TOKEN
    }

def create_test_error_response(error_message):
    """Create a test error response."""
    return {
        'success': False,
        'error': error_message
    }

def create_test_success_response(data=None):
    """Create a test success response."""
    response = {'success': True}
    if data is not None:
        response.update(data)
    return response

def mock_file_operations():
    """Create mocks for file operations."""
    with mock.patch('os.path.exists') as mock_exists, \
         mock.patch('os.path.getsize') as mock_size, \
         mock.patch('os.makedirs') as mock_makedirs:
        mock_exists.return_value = True
        mock_size.return_value = 1000
        mock_makedirs.return_value = None
        return mock_exists, mock_size, mock_makedirs

def create_test_summary_file(summary_data):
    """Create a test summary file."""
    temp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'summary_{timestamp}.json'
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(summary_data, f)
    
    return file_path, temp_dir

# Validation helper functions

def validate_summary_response(response):
    """Validate a summary response structure.
    
    Args:
        response (dict): Summary API response
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['success', 'summary']
    if not all(field in response for field in required_fields):
        return False
    
    if response.get('success') is not True:
        return False
        
    if not isinstance(response.get('summary'), str):
        return False
        
    return True

def validate_audio_file(file_path):
    """Validate that a file exists and is a valid WAV file.
    
    Args:
        file_path (str): Path to the audio file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        with wave.open(file_path, 'rb') as wav_file:
            # Check basic WAV file properties
            if wav_file.getnchannels() < 1:
                return False
            if wav_file.getsampwidth() < 1:
                return False
            if wav_file.getframerate() < 1:
                return False
            if wav_file.getnframes() < 1:
                return False
            return True
    except (wave.Error, EOFError, IOError):
        return False

def validate_video_data(video_data):
    """Validate video data structure.
    
    Args:
        video_data (dict): Video data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['title', 'duration', 'src']
    return all(field in video_data for field in required_fields)

def validate_summary_file(file_path):
    """Validate that a file exists and contains valid summary JSON data.
    
    Args:
        file_path (str): Path to the summary file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Check for required fields
        if 'summary' not in data:
            return False
            
        # Check for video data
        if 'video_data' in data:
            if not validate_video_data(data['video_data']):
                return False
                
        return True
    except (json.JSONDecodeError, IOError):
        return False 