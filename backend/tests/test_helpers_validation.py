"""Standalone tests for validating test helpers."""

import unittest
import os
import tempfile
import wave
import numpy as np
import json
import shutil
from datetime import datetime

# Test constants
TEST_AUDIO_DURATION = 10
TEST_AUDIO_SAMPLE_RATE = 16000
TEST_SUMMARY_TEXT = 'This is a test summary of the video content.'
TEST_VIDEO_TITLE = 'Test Video'
TEST_VIDEO_DURATION = 180
TEST_VIDEO_SRC = 'https://example.com/test-video.mp4'
TEST_VIDEO_PLATFORM = 'olympus'


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


def create_test_audio_file(duration=TEST_AUDIO_DURATION, sample_rate=TEST_AUDIO_SAMPLE_RATE, num_channels=1, filename=None):
    """Create a test audio file with proper WAV format."""
    temp_dir = tempfile.mkdtemp()
    if not filename:
        filename = 'test_audio.wav'
    audio_path = os.path.join(temp_dir, filename)
    
    # Write the data to a WAV file
    with wave.open(audio_path, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2)  # 2 bytes for int16
        wav_file.setframerate(sample_rate)
        
        if duration > 0:
            # Generate simple sine wave audio
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            # Generate a 440 Hz sine wave
            data = np.sin(2 * np.pi * 440 * t) * 32767
            data = data.astype(np.int16)
            wav_file.writeframes(data.tobytes())
    
    return audio_path, temp_dir


def create_test_video_file(format='mp4', duration=TEST_AUDIO_DURATION, filename=None):
    """Create a test video file with dummy content."""
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


def create_test_summary_file(summary_data):
    """Create a test summary file."""
    temp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'summary_{timestamp}.json'
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(summary_data, f)
    
    return file_path, temp_dir


def validate_audio_file(file_path):
    """Validate that a file exists and is a valid WAV file."""
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
            # Allow empty files (nframes can be 0)
            if wav_file.getnframes() < 0:
                return False
            return True
    except (wave.Error, EOFError, IOError):
        return False


def validate_video_data(video_data):
    """Validate video data structure."""
    required_fields = ['title', 'duration', 'src']
    return all(field in video_data for field in required_fields)


def validate_summary_file(file_path):
    """Validate that a file exists and contains valid summary JSON data."""
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


class TestHelpers(unittest.TestCase):
    """Tests for helper functions."""
    
    def test_create_temp_file(self):
        """Test creating a temporary file."""
        content = "Test content"
        file_path, temp_dir = create_temp_file(content)
        try:
            self.assertTrue(os.path.exists(file_path))
            with open(file_path, 'r') as f:
                self.assertEqual(f.read(), content)
        finally:
            cleanup_temp_dir(temp_dir)
    
    def test_create_audio_file(self):
        """Test creating an audio file."""
        audio_path, temp_dir = create_test_audio_file()
        try:
            self.assertTrue(os.path.exists(audio_path))
            self.assertTrue(validate_audio_file(audio_path))
            # Check file size
            self.assertGreater(os.path.getsize(audio_path), 0)
        finally:
            cleanup_temp_dir(temp_dir)
    
    def test_create_empty_audio_file(self):
        """Test creating an empty audio file."""
        audio_path, temp_dir = create_test_audio_file(duration=0)
        try:
            self.assertTrue(os.path.exists(audio_path))
            # Even empty files should be valid WAV files
            self.assertTrue(validate_audio_file(audio_path))
            # Check file size - header but no content
            self.assertGreater(os.path.getsize(audio_path), 0)
            self.assertLess(os.path.getsize(audio_path), 100)
        finally:
            cleanup_temp_dir(temp_dir)
    
    def test_create_video_file(self):
        """Test creating a video file."""
        video_path, temp_dir = create_test_video_file()
        try:
            self.assertTrue(os.path.exists(video_path))
            # Check file size
            self.assertGreater(os.path.getsize(video_path), 0)
        finally:
            cleanup_temp_dir(temp_dir)
    
    def test_create_summary_data(self):
        """Test creating summary data."""
        summary_data = create_test_summary_data()
        self.assertEqual(summary_data['summary'], TEST_SUMMARY_TEXT)
        self.assertEqual(summary_data['video_data']['title'], TEST_VIDEO_TITLE)
        self.assertEqual(summary_data['video_data']['duration'], TEST_VIDEO_DURATION)
        self.assertEqual(summary_data['video_data']['src'], TEST_VIDEO_SRC)
        self.assertEqual(summary_data['video_data']['platform'], TEST_VIDEO_PLATFORM)
    
    def test_create_summary_file(self):
        """Test creating a summary file."""
        summary_data = create_test_summary_data()
        summary_path, temp_dir = create_test_summary_file(summary_data)
        try:
            self.assertTrue(os.path.exists(summary_path))
            self.assertTrue(validate_summary_file(summary_path))
            
            # Read back the data and verify
            with open(summary_path, 'r') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data['summary'], summary_data['summary'])
            self.assertEqual(loaded_data['video_data'], summary_data['video_data'])
        finally:
            cleanup_temp_dir(temp_dir)


if __name__ == '__main__':
    unittest.main() 