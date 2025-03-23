#!/usr/bin/env python
"""
Test script to verify audio processor functionality and dependencies.
Run with: python -m tests.test_audio_processor
"""
import os
import sys
import unittest
import logging
import inspect
import importlib
import tempfile
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioProcessorTests(unittest.TestCase):
    """Test the audio processor module"""
    
    def setUp(self):
        # Make sure parent directory is in path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
    
    def test_no_openai_import(self):
        """Test that app.utils.audio_processor does not import openai"""
        # Import the module
        try:
            from app.utils import audio_processor
            
            # Check if openai is in the module's globals
            self.assertNotIn('openai', audio_processor.__dict__, 
                           "audio_processor should not import openai")
            
            # Check if there's any import statement with 'openai' in the file
            module_file = inspect.getfile(audio_processor)
            with open(module_file, 'r') as f:
                content = f.read()
                self.assertNotIn('import openai', content.lower(),
                               "audio_processor.py should not contain 'import openai'")
                
            logger.info("✓ Confirmed audio_processor does not import openai")
        except ImportError as e:
            self.fail(f"Failed to import audio_processor: {str(e)}")
    
    def test_generate_transcript_function(self):
        """Test the generate_transcript function in audio_processor"""
        try:
            from app.utils.audio_processor import generate_transcript
            
            # Create a temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                # Mock the ollama_client.transcribe function to return a successful result
                with patch('app.summarizer.ollama_client.transcribe') as mock_transcribe:
                    mock_transcribe.return_value = {'text': 'This is a test transcript'}
                    
                    # Call the function
                    result = generate_transcript(temp_file.name)
                    
                    # Verify the result
                    self.assertEqual(result, 'This is a test transcript')
                    mock_transcribe.assert_called_once_with(temp_file.name)
            
            logger.info("✓ generate_transcript function works correctly")
        except ImportError as e:
            self.fail(f"Failed to import generate_transcript: {str(e)}")
        except Exception as e:
            self.fail(f"Error in generate_transcript: {str(e)}")
    
    def test_generate_summary_function(self):
        """Test the generate_summary function in audio_processor"""
        try:
            from app.utils.audio_processor import generate_summary
            
            # Mock the ollama_client.summarize function to return a successful result
            with patch('app.summarizer.ollama_client.summarize') as mock_summarize:
                mock_summarize.return_value = {'response': 'This is a test summary'}
                
                # Call the function
                result = generate_summary("This is a test transcript to summarize.")
                
                # Verify the result
                self.assertEqual(result, 'This is a test summary')
                mock_summarize.assert_called_once()
            
            logger.info("✓ generate_summary function works correctly")
        except ImportError as e:
            self.fail(f"Failed to import generate_summary: {str(e)}")
        except Exception as e:
            self.fail(f"Error in generate_summary: {str(e)}")
    
    def test_process_audio_file_workflow(self):
        """Test the entire audio file processing workflow"""
        try:
            from app.utils.audio_processor import process_audio_file
            
            # Mock the process_audio function to return a successful result
            with patch('app.summarizer.processor.process_audio') as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "transcript": "This is a test transcript",
                    "summary": "This is a test summary",
                    "audio_stats": {
                        "duration": 10.5,
                        "sample_rate": 16000
                    }
                }
                
                # Call the function with a non-existent file first to test error handling
                with self.assertRaises(Exception):
                    process_audio_file("/non/existent/file.wav")
                
                # Create a temporary audio file
                with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                    # Write some content to make it non-empty
                    temp_file.write(b'test content')
                    temp_file.flush()
                    
                    # Call the function
                    result = process_audio_file(temp_file.name)
                    
                    # Verify the result
                    self.assertTrue(result["success"])
                    self.assertEqual(result["transcript"], "This is a test transcript")
                    self.assertEqual(result["summary"], "This is a test summary")
            
            logger.info("✓ process_audio_file workflow works correctly")
        except ImportError as e:
            self.fail(f"Failed to import process_audio_file: {str(e)}")
        except Exception as e:
            logger.error(f"Error in process_audio_file: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main() 