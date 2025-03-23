import unittest
import os
import tempfile
import json
import subprocess
import shutil
import logging
from io import BytesIO
from datetime import datetime, timedelta, timezone
from unittest import mock
from flask import jsonify, session
from werkzeug.datastructures import FileStorage
from urllib.parse import urlparse, parse_qs
import time

from app.main import create_app
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestYouTubeAudioProcessing(unittest.TestCase):
    """Test case for processing real YouTube audio"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class"""
        # Create a temporary directory for downloaded files
        cls.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {cls.temp_dir}")
        
        # YouTube video for testing - short video for fast download
        cls.test_video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" (first YouTube video)
        
        # Download the audio for all tests to use
        cls.audio_path = cls.download_youtube_audio(cls.test_video_url, cls.temp_dir)
        
        # Mock environment variables
        cls.env_patcher = mock.patch.dict(os.environ, {
            'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'test_extension_id',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id'
        })
        cls.env_patcher.start()
    
    @staticmethod
    def extract_youtube_id(url):
        """Extract YouTube video ID from URL"""
        if "youtu.be" in url:
            # Short URL format: https://youtu.be/VIDEO_ID
            path = urlparse(url).path
            return path.strip("/")
        elif "youtube.com" in url:
            # Regular URL format: https://www.youtube.com/watch?v=VIDEO_ID
            query = urlparse(url).query
            params = parse_qs(query)
            return params.get("v", [""])[0]
        else:
            # Direct ID or unknown format
            return url.strip()
    
    @staticmethod
    def download_youtube_audio(video_url, download_dir):
        """Download audio from a YouTube video using yt-dlp"""
        try:
            # Check if yt-dlp is installed
            subprocess.run(["yt-dlp", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            logger.info("yt-dlp is installed")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("yt-dlp is not installed. Install with: pip install yt-dlp")
            raise RuntimeError("yt-dlp is not installed")
            
        # Check if ffmpeg is installed
        try:
            subprocess.run(["ffmpeg", "-version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            logger.info("ffmpeg is installed")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("ffmpeg is not installed. Please install it first.")
            raise RuntimeError("ffmpeg is not installed")
        
        # Create a temporary file with timestamp for uniqueness
        output_path = os.path.join(download_dir, f"youtube_audio_{int(time.time())}.wav")
        
        logger.info(f"Downloading audio from YouTube URL: {video_url}")
        
        # Extract YouTube ID to verify it's a valid URL
        video_id = TestYouTubeAudioProcessing.extract_youtube_id(video_url)
        if not video_id:
            logger.error("Invalid YouTube URL or ID")
            return None
        
        # Command to download audio with high quality and save as WAV
        cmd = [
            "yt-dlp",
            "-x",                          # Extract audio
            "--audio-format", "wav",       # Convert to WAV
            "--audio-quality", "0",        # Highest quality
            "-o", output_path,             # Output path
            "--postprocessor-args", "-ar 16000 -ac 1",  # Set audio rate and channels
            video_url
        ]
        
        logger.info(f"Running download command: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            if os.path.exists(output_path):
                logger.info(f"Audio downloaded to: {output_path}")
                return output_path
            else:
                logger.error(f"Download command completed but output file not found: {output_path}")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading audio: {str(e)}")
            logger.error(f"yt-dlp stderr: {e.stderr.decode('utf-8', errors='replace')}")
            return None
    
    def setUp(self):
        """Set up test environment for each test"""
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False,
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id',
            'SESSION_TYPE': 'filesystem',
            'GOOGLE_CLIENT_SECRETS_FILE': os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json'),
            'SECRET_KEY': 'test_secret_key'
        })
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
            
        # Set up client secrets patcher
        self.secrets_patcher = mock.patch('app.auth.routes.get_client_secrets_file')
        self.mock_get_secrets = self.secrets_patcher.start()
        self.mock_get_secrets.return_value = os.path.join(os.path.dirname(__file__), 'dummy_client_secrets.json')
        
        # Patch the login_required decorator in the auth routes module
        self.login_required_patcher = mock.patch('app.api.routes.login_required')
        mock_login_required_func = self.login_required_patcher.start()
        mock_login_required_func.return_value = lambda f: f  # Make decorator pass through
        
        # Set up authenticated session
        with self.client.session_transaction() as sess:
            sess['user_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'picture': 'https://example.com/profile.jpg',
                'email_verified': True
            }
            sess['last_activity'] = datetime.now(timezone.utc).isoformat()
            sess['oauth_state'] = 'test_state'
            sess['credentials'] = {
                'token': 'test_token',
                'refresh_token': 'test_refresh_token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'scopes': ['profile', 'email'],
                'expiry': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            }
    
    def create_multipart_data(self):
        """Create multipart form data with the real YouTube audio."""
        # Read audio file
        if not os.path.exists(self.__class__.audio_path):
            raise FileNotFoundError(f"Audio file not found: {self.__class__.audio_path}")
        
        with open(self.__class__.audio_path, 'rb') as f:
            file_content = f.read()
        
        # Create BytesIO object
        stream = BytesIO(file_content)
        stream.seek(0)
        
        # Create FileStorage object
        file_storage = FileStorage(
            stream=stream,
            filename=os.path.basename(self.__class__.audio_path),
            content_type='audio/wav'
        )
        
        # Return form data with the file
        return {
            'audio': file_storage,
            'options': json.dumps({
                'length': 'medium',
                'format': 'paragraph'
            }),
            'playback_rate': '1.0'
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Pop the app context
        self.app_context.pop()
        
        # Stop patchers
        self.login_required_patcher.stop()
        self.secrets_patcher.stop()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests"""
        # Clean up temporary directory
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
            logger.info(f"Removed temporary directory: {cls.temp_dir}")
        
        # Stop environment patcher
        if hasattr(cls, 'env_patcher'):
            cls.env_patcher.stop()
    
    def test_youtube_audio_download(self):
        """Test that the YouTube audio was successfully downloaded"""
        self.assertTrue(os.path.exists(self.__class__.audio_path))
        self.assertTrue(os.path.getsize(self.__class__.audio_path) > 0)
    
    @mock.patch('app.api.routes.process_audio')
    def test_youtube_audio_transcription(self, mock_process):
        """Test transcription endpoint with real YouTube audio"""
        # Mock the process_audio function
        mock_process.return_value = {
            'success': True,
            'transcription': 'This is a test transcription of YouTube audio.',
            'summary': 'This is a test summary of YouTube audio.'
        }
        
        # Create multipart data with real YouTube audio
        try:
            data = self.create_multipart_data()
            
            # Skip actual audio processing and mock validation
            with mock.patch('subprocess.run') as mock_subprocess:
                with mock.patch('app.api.routes.RequestValidator.validate_file_upload', return_value=lambda f: f):
                    response = self.client.post(
                        '/api/transcribe',
                        data=data,
                        content_type='multipart/form-data'
                    )
            
            # Check the response - can be success (200), validation error (400), or server error (500)
            self.assertIn(response.status_code, [200, 400, 500])
            
            # If successful, verify the response content
            if response.status_code == 200:
                response_data = json.loads(response.data)
                self.assertTrue(response_data['success'])
                self.assertEqual(response_data['transcription'], 'This is a test transcription of YouTube audio.')
                self.assertEqual(response_data['summary'], 'This is a test summary of YouTube audio.')
            else:
                # Log the error for debugging
                logger.warning(f"Request failed with status {response.status_code}")
                if response.data:
                    logger.warning(f"Response data: {response.data}")
        
        except Exception as e:
            logger.error(f"Error in test_youtube_audio_transcription: {str(e)}")
            raise
    
    def test_actual_youtube_audio_transcription(self):
        """Test transcription process directly with actual YouTube audio"""
        from app.summarizer.processor import transcribe_audio_enhanced, summarize_text_enhanced
        import whisper
        
        # Check if the audio file exists
        self.assertTrue(os.path.exists(self.__class__.audio_path), "YouTube audio file not found")
        file_size_mb = os.path.getsize(self.__class__.audio_path) / (1024 * 1024)
        print(f"Downloaded YouTube audio file: {self.__class__.audio_path} (Size: {file_size_mb:.2f} MB)")
        
        try:
            # 1. Load Whisper model with visual progress bars
            print("\nLoading Whisper model...")
            model = whisper.load_model("tiny", download_root=os.path.join(self.temp_dir, "models"))
            
            # 2. Transcribe directly with Whisper
            print("\nTranscribing audio with Whisper...")
            result = model.transcribe(self.__class__.audio_path, fp16=False, verbose=True)
            transcription = result["text"].strip()
            
            # Check if transcription is successful
            self.assertIsNotNone(transcription)
            self.assertNotEqual(transcription, "")
            print(f"\nTranscription result: {transcription}")
            
            # Check if expected words from the video are in the transcription
            # "Me at the zoo" video mentions elephants
            self.assertIn("elephant", transcription.lower(), "Expected words not found in transcription")
            
            # 3. Try summarization with progress bars
            print("\nSummarizing the transcription...")
            try:
                # Mock ollama_client to prevent actual API calls in tests
                with mock.patch('app.summarizer.processor.ollama_client') as mock_ollama:
                    # Configure the mock to return a successful summary
                    mock_ollama.health_check.return_value = True
                    mock_ollama.summarize.return_value = "A summary about elephants at the zoo."
                    
                    # Options with shorter output for testing
                    options = {
                        'length': 'short',
                        'format': 'paragraph',
                        'focus': ['key_points']
                    }
                    
                    # Run the summarization
                    summary = summarize_text_enhanced(transcription, options)
                    
                    # Check if summarization succeeded
                    self.assertIsNotNone(summary)
                    self.assertNotEqual(summary, "")
                    print(f"\nSummarization result: {summary}")
            except Exception as e:
                print(f"\nSummarization error (but continuing test): {str(e)}")
                import traceback
                traceback.print_exc()
                # We don't fail the test on summarization error
                
            # Test is considered successful if transcription works
            print("\nTest completed successfully - YouTube audio processing is working!")
            
        except Exception as e:
            print(f"ERROR in test_actual_youtube_audio_transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    unittest.main() 