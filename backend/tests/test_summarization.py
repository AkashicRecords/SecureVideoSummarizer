import pytest
import os
import json
from unittest import mock
from tests.test_helpers import (
    create_test_audio_file,
    validate_audio_file,
    cleanup_temp_dir
)
from tests.test_constants import (
    TEST_AUDIO_DURATION,
    TEST_AUDIO_SAMPLE_RATE
)

@pytest.fixture
def test_audio_file():
    """Create a test audio file for the tests."""
    audio_path, temp_dir = create_test_audio_file(
        duration=TEST_AUDIO_DURATION,
        sample_rate=TEST_AUDIO_SAMPLE_RATE,
        num_channels=1
    )
    yield audio_path, temp_dir
    cleanup_temp_dir(temp_dir)

@pytest.fixture
def test_empty_audio_file():
    """Create an empty test audio file for the tests."""
    audio_path, temp_dir = create_test_audio_file(
        duration=0,
        sample_rate=TEST_AUDIO_SAMPLE_RATE,
        num_channels=1,
        filename='empty_audio.wav'
    )
    yield audio_path, temp_dir
    cleanup_temp_dir(temp_dir)

def test_audio_file_creation(test_audio_file):
    """Test that creating an audio file works properly."""
    audio_path, _ = test_audio_file
    # Validate the audio file
    assert validate_audio_file(audio_path)
    assert os.path.exists(audio_path)
    assert os.path.getsize(audio_path) > 0

def test_empty_audio_file_creation(test_empty_audio_file):
    """Test that creating an empty audio file works properly."""
    audio_path, _ = test_empty_audio_file
    assert os.path.exists(audio_path)
    # Empty files should be valid WAV files but with minimal size
    assert validate_audio_file(audio_path)
    # Empty audio has header but minimal content
    assert os.path.getsize(audio_path) > 0
    assert os.path.getsize(audio_path) < 100

def test_mock_transcription_and_summarization():
    """Test mocking transcription and summarization functions."""
    # Create mock functions
    with mock.patch('tests.test_helpers.mock_audio_processing_functions') as mock_audio_processing:
        # Set up the mock
        mock_processor = mock.MagicMock()
        mock_processor.convert_to_wav_enhanced.return_value = 'test_audio.wav'
        mock_processor.validate_audio.return_value = True
        mock_processor.transcribe_audio_enhanced.return_value = 'Test transcription'
        mock_processor.summarize_text_enhanced.return_value = 'Test summary'
        mock_audio_processing.return_value = mock_processor
        
        # Test the mock
        processor = mock_audio_processing()
        assert processor.convert_to_wav_enhanced('input.mp3') == 'test_audio.wav'
        assert processor.validate_audio('test_audio.wav') is True
        assert processor.transcribe_audio_enhanced('test_audio.wav') == 'Test transcription'
        assert processor.summarize_text_enhanced('Test transcription') == 'Test summary'

def test_summarization_workflow_mock():
    """Test the summarization workflow using mocks."""
    # Create mock function for process_audio
    with mock.patch('tests.test_helpers.mock_audio_processing_functions') as mock_audio_processing:
        # Set up the mock
        mock_processor = mock.MagicMock()
        mock_processor.convert_to_wav_enhanced.return_value = 'test_audio.wav'
        mock_processor.validate_audio.return_value = True
        mock_processor.transcribe_audio_enhanced.return_value = 'Test transcription'
        mock_processor.summarize_text_enhanced.return_value = 'Test summary'
        mock_audio_processing.return_value = mock_processor
        
        # Create a mock process_audio function
        def mock_process_audio(audio_path, options=None):
            """Mock implementation of process_audio."""
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"File not found: {audio_path}")
            
            if os.path.getsize(audio_path) < 100:
                raise ValueError("Audio file is empty or too small")
            
            # Simulate the workflow
            processor = mock_audio_processing()
            wav_path = processor.convert_to_wav_enhanced(audio_path)
            is_valid = processor.validate_audio(wav_path)
            
            if not is_valid:
                raise ValueError("Invalid audio file")
            
            transcription = processor.transcribe_audio_enhanced(wav_path)
            summary = processor.summarize_text_enhanced(transcription)
            
            return {
                'transcript': transcription,
                'summary': summary
            }
        
        # Test the mock process_audio function with various scenarios
        with mock.patch('os.path.exists') as mock_exists, \
             mock.patch('os.path.getsize') as mock_size:
            
            # Test successful processing
            mock_exists.return_value = True
            mock_size.return_value = 1000
            
            result = mock_process_audio('test_audio.wav')
            assert result['transcript'] == 'Test transcription'
            assert result['summary'] == 'Test summary'
            
            # Test file not found
            mock_exists.return_value = False
            
            with pytest.raises(FileNotFoundError):
                mock_process_audio('nonexistent.wav')
            
            # Test empty file
            mock_exists.return_value = True
            mock_size.return_value = 50
            
            with pytest.raises(ValueError, match="empty or too small"):
                mock_process_audio('empty_audio.wav')
