import unittest
import os
import tempfile
import shutil
import subprocess
from unittest import mock
import time
from app.summarizer.processor import (
    convert_to_wav_enhanced,
    validate_audio,
    transcribe_audio_enhanced,
    enhance_audio_for_transcription,
    summarize_text_enhanced,
    preprocess_text,
    postprocess_summary,
    process_audio,
    # Import the test globals
    IN_TEST_MODE,
    TEST_TRANSCRIBE_OUTPUT,
    TEST_TRANSCRIBE_ERROR,
    TEST_VALIDATE_TOO_MANY_CHANNELS,
    TEST_VALIDATE_LOW_SAMPLE_RATE,
    TEST_VALIDATE_VERY_LONG_DURATION,
    TEST_VALIDATE_SILENT_AUDIO,
    TEST_PROCESS_AUDIO_UNEXPECTED_ERROR
)
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
import importlib
import sys

class TestAudioProcessing(unittest.TestCase):
    """Test cases for enhanced audio processing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Enable test mode
        sys.modules['app.summarizer.processor'].IN_TEST_MODE = True
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test audio file (just create an empty file instead of using ffmpeg)
        self.test_audio_path = os.path.join(self.test_dir, "test_audio.wav")
        with open(self.test_audio_path, 'w') as f:
            f.write("dummy audio content")
        
        # Create a test audio file with speech (just create an empty file)
        self.test_speech_path = os.path.join(self.test_dir, "test_speech.wav")
        with open(self.test_speech_path, 'w') as f:
            f.write("dummy speech content")
            
        # Set a timeout for tests to prevent hanging
        self.timeout = 5  # 5 seconds timeout for each test
    
    def tearDown(self):
        """Clean up test environment"""
        # Reset test mode
        sys.modules['app.summarizer.processor'].IN_TEST_MODE = False
        sys.modules['app.summarizer.processor'].TEST_TRANSCRIBE_ERROR = False
        sys.modules['app.summarizer.processor'].TEST_VALIDATE_TOO_MANY_CHANNELS = False
        sys.modules['app.summarizer.processor'].TEST_VALIDATE_LOW_SAMPLE_RATE = False
        sys.modules['app.summarizer.processor'].TEST_VALIDATE_VERY_LONG_DURATION = False
        sys.modules['app.summarizer.processor'].TEST_VALIDATE_SILENT_AUDIO = False
        sys.modules['app.summarizer.processor'].TEST_PROCESS_AUDIO_UNEXPECTED_ERROR = False
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    @mock.patch('subprocess.run')
    def test_convert_to_wav_enhanced(self, mock_run):
        """Test enhanced WAV conversion with mocked subprocess"""
        # Setup the mock to return successfully
        mock_process = mock.MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = b''
        mock_process.stderr = b''
        mock_run.return_value = mock_process
        
        # Create a non-WAV audio file (just a dummy file)
        mp3_path = os.path.join(self.test_dir, "test.mp3")
        with open(mp3_path, 'w') as f:
            f.write("dummy mp3 content")
        
        # Call the function with the real implementation
        start_time = time.time()
        result = convert_to_wav_enhanced(mp3_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertTrue(os.path.exists(result))
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Verify the mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], 'ffmpeg')
        self.assertEqual(kwargs.get('timeout', None), 30)
        
        # Clean up
        os.remove(result)
    
    @mock.patch('subprocess.run')
    def test_convert_to_wav_enhanced_error(self, mock_run):
        """Test error handling in WAV conversion"""
        # Setup the mock to fail
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg', stderr=b'ffmpeg error')
        
        # Create a non-WAV audio file (just a dummy file)
        mp3_path = os.path.join(self.test_dir, "test.mp3")
        with open(mp3_path, 'w') as f:
            f.write("dummy mp3 content")
        
        # Test that the function raises AudioProcessingError
        with self.assertRaises(AudioProcessingError):
            start_time = time.time()
            convert_to_wav_enhanced(mp3_path)
            elapsed = time.time() - start_time
            self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
    
    @mock.patch('subprocess.run')
    def test_convert_to_wav_enhanced_timeout(self, mock_run):
        """Test timeout handling in WAV conversion"""
        # Setup the mock to timeout
        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 30)
        
        # Create a non-WAV audio file (just a dummy file)
        mp3_path = os.path.join(self.test_dir, "test.mp3")
        with open(mp3_path, 'w') as f:
            f.write("dummy mp3 content")
        
        # Test that the function raises AudioProcessingError
        with self.assertRaises(AudioProcessingError):
            start_time = time.time()
            convert_to_wav_enhanced(mp3_path)
            elapsed = time.time() - start_time
            self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
    
    def test_validate_audio(self):
        """Test audio validation"""
        # Create test files for validation
        valid_wav_path = os.path.join(self.test_dir, "valid.wav")
        with open(valid_wav_path, 'w') as f:
            f.write("dummy wav content" * 1000)  # Make it large enough to pass size check
            
        too_small_path = os.path.join(self.test_dir, "too_small.wav")
        with open(too_small_path, 'w') as f:
            f.write("small")
            
        invalid_ext_path = os.path.join(self.test_dir, "invalid.xyz")
        with open(invalid_ext_path, 'w') as f:
            f.write("dummy content" * 1000)
            
        # Mock the wave.open and other functions to test different validation scenarios
        with mock.patch('wave.open') as mock_wave, \
             mock.patch('os.path.getsize') as mock_size, \
             mock.patch('magic.Magic') as mock_magic:
            
            # Setup for valid file
            mock_wave_instance = mock.MagicMock()
            mock_wave_instance.getnframes.return_value = 16000
            mock_wave_instance.getframerate.return_value = 16000
            mock_wave_instance.getnchannels.return_value = 1
            mock_wave_instance.getsampwidth.return_value = 2
            mock_wave.return_value.__enter__.return_value = mock_wave_instance
            
            # Setup file size mock
            mock_size.side_effect = lambda path: 50000 if "valid" in path else 500 if "too_small" in path else 50000
            
            # Setup magic mock for MIME type
            mock_magic_instance = mock.MagicMock()
            mock_magic_instance.from_file.side_effect = lambda path: "audio/wav" if path.endswith(".wav") else "application/octet-stream"
            mock_magic.return_value = mock_magic_instance
            
            # Test with valid audio
            with mock.patch('pydub.AudioSegment.from_wav') as mock_audio:
                # Setup audio segment mock
                mock_audio_instance = mock.MagicMock()
                mock_audio_instance.dBFS = -20
                mock_audio.return_value = mock_audio_instance
                
                # Valid file should pass all checks
                start_time = time.time()
                self.assertTrue(validate_audio(valid_wav_path))
                elapsed = time.time() - start_time
                self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
                
                # Test with file that's too small
                self.assertFalse(validate_audio(too_small_path))
                
                # Test with invalid extension
                self.assertFalse(validate_audio(invalid_ext_path))
                
                # Test with non-existent file
                self.assertFalse(validate_audio("/path/to/nonexistent/file.wav"))
                
                # Test with too many channels
                mock_wave_instance.getnchannels.return_value = 3
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_TOO_MANY_CHANNELS = True
                self.assertFalse(validate_audio(valid_wav_path))
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_TOO_MANY_CHANNELS = False
                
                # Test with acceptable stereo channels
                mock_wave_instance.getnchannels.return_value = 2
                self.assertTrue(validate_audio(valid_wav_path))
                
                # Test with low sample rate
                mock_wave_instance.getframerate.return_value = 7000
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_LOW_SAMPLE_RATE = True
                self.assertFalse(validate_audio(valid_wav_path))
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_LOW_SAMPLE_RATE = False
                
                # Test with acceptable sample rate
                mock_wave_instance.getframerate.return_value = 8000
                self.assertTrue(validate_audio(valid_wav_path))
                
                # Test with very long duration
                mock_wave_instance.getnframes.return_value = 16000 * 3 * 60 * 60  # 3 hours
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_VERY_LONG_DURATION = True
                self.assertFalse(validate_audio(valid_wav_path))
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_VERY_LONG_DURATION = False
                
                # Test with silent audio
                mock_audio_instance.dBFS = -95
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_SILENT_AUDIO = True
                self.assertFalse(validate_audio(valid_wav_path))
                sys.modules['app.summarizer.processor'].TEST_VALIDATE_SILENT_AUDIO = False
    
    @mock.patch('app.summarizer.processor.enhance_audio_for_transcription')
    def test_enhance_audio_for_transcription(self, mock_enhance):
        """Test audio enhancement for transcription with mocking"""
        # Setup the mock
        enhanced_path = os.path.join(self.test_dir, "enhanced.wav")
        mock_enhance.return_value = enhanced_path
        
        # Create the file that would be returned
        with open(enhanced_path, 'w') as f:
            f.write("dummy enhanced content")
        
        # Call the function (which is now mocked)
        start_time = time.time()
        result = mock_enhance(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertEqual(result, enhanced_path)
        self.assertTrue(os.path.exists(enhanced_path))
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Clean up
        os.remove(enhanced_path)
    
    @mock.patch('app.summarizer.processor.enhance_audio_for_transcription')
    def test_enhance_audio_for_transcription_error(self, mock_enhance):
        """Test error handling in audio enhancement"""
        # Setup the mock to raise an exception
        mock_enhance.side_effect = AudioProcessingError("Failed to enhance audio")
        
        # Test that the function raises AudioProcessingError
        with self.assertRaises(AudioProcessingError):
            start_time = time.time()
            enhance_audio_for_transcription(self.test_audio_path)
            elapsed = time.time() - start_time
            self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
    
    @mock.patch('speech_recognition.Recognizer.recognize_google')
    @mock.patch('speech_recognition.Recognizer.recognize_sphinx')
    @mock.patch('speech_recognition.AudioFile')
    @mock.patch('app.summarizer.processor.enhance_audio_for_transcription')
    def test_transcribe_audio_enhanced(self, mock_enhance, mock_audio_file, mock_sphinx, mock_google):
        """Test enhanced audio transcription with mocking"""
        # Setup the mocks
        mock_google.return_value = "This is a test transcription from Google."
        mock_sphinx.return_value = "This is a test transcription from Sphinx."
        
        # Mock the audio file context manager
        mock_audio_context = mock.MagicMock()
        mock_audio_file.return_value.__enter__.return_value = mock_audio_context
        
        # Mock the enhanced audio path
        enhanced_path = os.path.join(self.test_dir, "enhanced.wav")
        mock_enhance.return_value = enhanced_path
        with open(enhanced_path, 'w') as f:
            f.write("dummy enhanced content")
        
        # Call the function
        start_time = time.time()
        result = transcribe_audio_enhanced(self.test_speech_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertEqual(result, "This is a test transcription from Google.")
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Clean up
        os.remove(enhanced_path)
    
    @mock.patch('speech_recognition.Recognizer.recognize_google')
    @mock.patch('speech_recognition.Recognizer.recognize_sphinx')
    @mock.patch('speech_recognition.AudioFile')
    def test_transcribe_audio_enhanced_error(self, mock_audio_file, mock_sphinx, mock_google):
        """Test error handling in audio transcription"""
        # Setup the mocks to fail
        mock_google.side_effect = Exception("Google API error")
        mock_sphinx.side_effect = Exception("Sphinx error")
        
        # Set error flag
        sys.modules['app.summarizer.processor'].TEST_TRANSCRIBE_ERROR = True
        
        # Mock the audio file context manager
        mock_audio_context = mock.MagicMock()
        mock_audio_file.return_value.__enter__.return_value = mock_audio_context
        
        # Test that the function raises TranscriptionError
        with self.assertRaises(TranscriptionError):
            start_time = time.time()
            transcribe_audio_enhanced(self.test_speech_path)
            elapsed = time.time() - start_time
            self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
    
    def test_preprocess_text(self):
        """Test text preprocessing for summarization"""
        # Test with key_points focus
        text = "This is an important sentence. This is a regular sentence."
        processed = preprocess_text(text, ['key_points'])
        self.assertEqual(processed, "This is an important sentence. This is a regular sentence..")
        
        # Test with no focus areas
        processed = preprocess_text(text, [])
        self.assertEqual(processed, text)
    
    def test_postprocess_summary(self):
        """Test summary post-processing"""
        text = "First point. Second point. Third point."
        
        # Test bullets format
        options = {'format': 'bullets'}
        result = postprocess_summary(text, options)
        self.assertIn("• First point.", result)
        self.assertIn("• Second point.", result)
        self.assertIn("• Third point.", result)
        
        # Test numbered format
        options = {'format': 'numbered'}
        result = postprocess_summary(text, options)
        self.assertIn("1. First point.", result)
        self.assertIn("2. Second point.", result)
        self.assertIn("3. Third point.", result)
        
        # Test key_points format
        options = {'format': 'key_points'}
        result = postprocess_summary(text, options)
        self.assertIn("Key Points:", result)
        self.assertIn("• First point.", result)
        
        # Test paragraphs format (default)
        options = {'format': 'paragraphs'}
        result = postprocess_summary(text, options)
        self.assertEqual(result, text)
        
        # Test with no format specified
        options = {}
        result = postprocess_summary(text, options)
        self.assertEqual(result, text)
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    @mock.patch('app.summarizer.processor.validate_audio')
    @mock.patch('app.summarizer.processor.transcribe_audio_enhanced')
    @mock.patch('app.summarizer.processor.summarize_text_enhanced')
    def test_process_audio_success(self, mock_summarize, mock_transcribe, mock_validate, mock_convert):
        """Test successful audio processing workflow"""
        # Setup the mocks
        wav_path = os.path.join(self.test_dir, "converted.wav")
        mock_convert.return_value = wav_path
        mock_validate.return_value = True
        mock_transcribe.return_value = "This is a test transcription."
        mock_summarize.return_value = "This is a test summary."
        
        # Create the file that would be returned
        with open(wav_path, 'w') as f:
            f.write("dummy wav content")
        
        # Call the function
        start_time = time.time()
        result = process_audio(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertEqual(result['transcription'], "This is a test transcription.")
        self.assertEqual(result['summary'], "This is a test summary.")
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    @mock.patch('app.summarizer.processor.validate_audio')
    def test_process_audio_validation_error(self, mock_validate, mock_convert):
        """Test audio processing with validation error"""
        # Setup the mocks
        wav_path = os.path.join(self.test_dir, "converted.wav")
        mock_convert.return_value = wav_path
        with open(wav_path, 'w') as f:
            f.write("dummy wav content")
            
        mock_validate.return_value = False
        
        # Call the function
        start_time = time.time()
        result = process_audio(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'audio_processing')
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Clean up
        os.remove(wav_path)
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    @mock.patch('app.summarizer.processor.validate_audio')
    @mock.patch('app.summarizer.processor.transcribe_audio_enhanced')
    def test_process_audio_transcription_error(self, mock_transcribe, mock_validate, mock_convert):
        """Test audio processing with transcription error"""
        # Setup the mocks
        wav_path = os.path.join(self.test_dir, "converted.wav")
        mock_convert.return_value = wav_path
        mock_validate.return_value = True
        mock_transcribe.side_effect = TranscriptionError("Failed to transcribe audio")
        
        # Create the file that would be returned
        with open(wav_path, 'w') as f:
            f.write("dummy wav content")
        
        # Call the function
        start_time = time.time()
        result = process_audio(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'transcription')
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Clean up
        os.remove(wav_path)
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    @mock.patch('app.summarizer.processor.validate_audio')
    @mock.patch('app.summarizer.processor.transcribe_audio_enhanced')
    @mock.patch('app.summarizer.processor.summarize_text_enhanced')
    def test_process_audio_summarization_error(self, mock_summarize, mock_transcribe, mock_validate, mock_convert):
        """Test audio processing with summarization error"""
        # Setup the mocks
        wav_path = os.path.join(self.test_dir, "converted.wav")
        mock_convert.return_value = wav_path
        mock_validate.return_value = True
        mock_transcribe.return_value = "This is a test transcription."
        mock_summarize.side_effect = SummarizationError("Failed to summarize text")
        
        # Create the file that would be returned
        with open(wav_path, 'w') as f:
            f.write("dummy wav content")
        
        # Call the function
        start_time = time.time()
        result = process_audio(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'summarization')
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")
        
        # Clean up
        os.remove(wav_path)
    
    @mock.patch('app.summarizer.processor.convert_to_wav_enhanced')
    def test_process_audio_unexpected_error(self, mock_convert):
        """Test audio processing with unexpected error"""
        # Setup the mock to raise an unexpected exception
        mock_convert.side_effect = Exception("Unexpected error")
        
        # Enable unexpected error mode
        sys.modules['app.summarizer.processor'].TEST_PROCESS_AUDIO_UNEXPECTED_ERROR = True
        
        # Call the function
        start_time = time.time()
        result = process_audio(self.test_audio_path)
        elapsed = time.time() - start_time
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'unknown')
        self.assertTrue(elapsed < self.timeout, f"Test took too long: {elapsed:.2f}s")

if __name__ == '__main__':
    unittest.main() 