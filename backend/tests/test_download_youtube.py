import unittest
import os
import tempfile
import shutil
import subprocess
import logging
import time
import wave
import sys
from unittest import mock
import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestYouTubeAudio(unittest.TestCase):
    """Simple test for YouTube audio download and processing"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class"""
        # Create a temporary directory for downloaded files
        cls.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {cls.temp_dir}")
        
        # YouTube video for testing - short video for fast download
        cls.test_video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" (first YouTube video)
        
        # Age-restricted video for testing (optional)
        cls.age_restricted_url = "https://www.youtube.com/watch?v=KYniUCGPGLs"  # Example of age-restricted video
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests"""
        # Clean up temporary directory
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
            logger.info(f"Removed temporary directory: {cls.temp_dir}")
    
    def download_youtube_audio(self, video_url, download_dir, cookie_file=None):
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
        
        # Command to download audio with high quality and save as WAV
        cmd = [
            "yt-dlp",
            "-x",                          # Extract audio
            "--audio-format", "wav",       # Convert to WAV
            "--audio-quality", "0",        # Highest quality
            "-o", output_path,             # Output path
            "--progress",                  # Show progress bar
            "--postprocessor-args", "-ar 16000 -ac 1",  # Set audio rate and channels
            "--no-playlist",               # Don't download playlists
        ]
        
        # Add cookie file for age-restricted videos if provided
        if cookie_file and os.path.exists(cookie_file):
            cmd.extend(["--cookies", cookie_file])
        
        # Add the video URL
        cmd.append(video_url)
        
        logger.info(f"Running download command: {' '.join(cmd)}")
        
        try:
            # Run the command and show output in real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Print output in real-time
            print("\nDownloading YouTube audio:")
            for line in process.stdout:
                print(line.strip())
            
            # Wait for the process to complete
            process.wait()
            
            # Check if the download was successful
            if process.returncode != 0:
                logger.error(f"yt-dlp failed with return code {process.returncode}")
                return None
            
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
    
    def verify_audio_file(self, audio_path):
        """Verify the audio file properties"""
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            return False
            
        try:
            # Check file size
            file_size = os.path.getsize(audio_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size < 1000:  # Less than 1KB
                logger.error(f"Audio file too small: {file_size} bytes")
                return False
                
            logger.info(f"Audio file size: {file_size_mb:.2f} MB")
            
            # Check WAV format properties
            with wave.open(audio_path, 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                frames = wf.getnframes()
                duration = frames / frame_rate
                
                logger.info(f"WAV properties: channels={channels}, sample_width={sample_width}, "
                           f"frame_rate={frame_rate}, duration={duration:.2f}s")
                
                # Basic validation
                if duration < 0.5:
                    logger.error("Audio duration too short")
                    return False
                    
                return True
                
        except Exception as e:
            logger.error(f"Error verifying audio: {str(e)}")
            return False
    
    def transcribe_audio(self, audio_path, model_name="tiny"):
        """Transcribe audio using Whisper model with progress bars"""
        try:
            import whisper
            print(f"\nLoading Whisper model ({model_name})...")
            
            # Show model loading
            with tqdm.tqdm(total=100, desc="Loading model", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                model = whisper.load_model(model_name)
                pbar.update(100)
            
            print("\nTranscribing audio...")
            result = model.transcribe(audio_path, fp16=False, verbose=True)
            transcription = result["text"].strip()
            
            print(f"\nTranscription result: {transcription}")
            return transcription
            
        except ImportError as e:
            print(f"Cannot transcribe: {str(e)}")
            return None
    
    def test_download_youtube_audio(self):
        """Test downloading YouTube audio and verifying the file"""
        # Download the audio
        audio_path = self.download_youtube_audio(self.__class__.test_video_url, self.__class__.temp_dir)
        self.assertIsNotNone(audio_path, "Failed to download YouTube audio")
        
        # Verify the audio file
        is_valid = self.verify_audio_file(audio_path)
        self.assertTrue(is_valid, "Downloaded audio file failed validation")
        
        # Print info about the downloaded file
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"\nDownloaded YouTube audio: {audio_path}")
        print(f"File size: {file_size_mb:.2f} MB")
        
        # Transcribe the audio
        transcription = self.transcribe_audio(audio_path)
        self.assertIsNotNone(transcription, "Failed to transcribe audio")
        self.assertGreater(len(transcription), 0, "Transcription is empty")
        
        # Check for expected content
        self.assertIn("elephant", transcription.lower(), 
                     "Expected word 'elephant' not found in transcription")
        
        # Mock the summarizer function to test directly
        try:
            # Import the relevant function from our app
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from app.summarizer.processor import summarize_text_enhanced
            
            print("\nTesting summarization function...")
            
            # Mock the ollama_client to avoid external API calls
            with mock.patch('app.summarizer.processor.ollama_client') as mock_ollama:
                # Configure mock
                mock_ollama.health_check.return_value = True
                mock_ollama.summarize.return_value = "This video shows elephants at the zoo with cool features."
                
                # Test the summarization
                options = {
                    'length': 'short',
                    'format': 'paragraph'
                }
                
                summary = summarize_text_enhanced(transcription, options)
                print(f"\nSummary result: {summary}")
                
                self.assertGreater(len(summary), 0, "Summary is empty")
                
        except ImportError as e:
            print(f"Cannot test summarization: {str(e)}")
    
    def test_handle_age_restricted_video(self):
        """Test handling of age-restricted videos"""
        # This test is skipped by default as it requires authentication
        if not os.environ.get('YOUTUBE_TEST_AGE_RESTRICTED'):
            self.skipTest("Skipping age-restricted video test. Set YOUTUBE_TEST_AGE_RESTRICTED=1 to enable.")
        
        # Location for cookie file (if provided)
        cookie_file = os.environ.get('YOUTUBE_COOKIE_FILE')
        
        print("\n=== Testing age-restricted video downloading ===")
        if cookie_file:
            print(f"Using cookie file: {cookie_file}")
        else:
            print("No cookie file provided. Will attempt to download without authentication.")
            
        # Download the audio
        audio_path = self.download_youtube_audio(self.__class__.age_restricted_url, self.__class__.temp_dir, cookie_file)
        
        # If download succeeded, verify the file
        if audio_path:
            is_valid = self.verify_audio_file(audio_path)
            self.assertTrue(is_valid, "Downloaded audio file failed validation")
            
            # Print info about the downloaded file
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            print(f"\nDownloaded age-restricted YouTube audio: {audio_path}")
            print(f"File size: {file_size_mb:.2f} MB")
            
            # Test transcription (optional)
            transcription = self.transcribe_audio(audio_path)
            if transcription:
                self.assertGreater(len(transcription), 0, "Transcription is empty")
        else:
            print("Download of age-restricted video failed - this may be expected without proper authentication.")
            self.skipTest("Age-restricted video download failed. Provide cookie file for authentication.")
    
    def test_integration_with_app(self):
        """Test integration with the main app processing pipeline"""
        # Skip if SKIP_INTEGRATION_TEST environment variable is set
        if os.environ.get('SKIP_INTEGRATION_TEST'):
            self.skipTest("Skipping integration test. Set SKIP_INTEGRATION_TEST=0 to enable.")
        
        # Download the audio
        audio_path = self.download_youtube_audio(self.__class__.test_video_url, self.__class__.temp_dir)
        self.assertIsNotNone(audio_path, "Failed to download YouTube audio")
        
        # Import the process_audio function
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from app.summarizer.processor import process_audio
            
            print("\nTesting integration with app.summarizer.processor.process_audio")
            
            # Mock the ollama_client to avoid external API calls during integration test
            with mock.patch('app.summarizer.processor.ollama_client') as mock_ollama:
                # Configure mock
                mock_ollama.health_check.return_value = True
                mock_ollama.summarize.return_value = "This video shows elephants at the zoo with cool features."
                
                # Process the audio
                result = process_audio(audio_path)
                
                # Check the result
                self.assertTrue(result.get('success', False), f"Processing failed: {result.get('error', 'Unknown error')}")
                self.assertIn('transcription', result, "No transcription in result")
                self.assertIn('summary', result, "No summary in result")
                
                # Print the results
                print(f"\nTranscription: {result['transcription']}")
                print(f"Summary: {result['summary']}")
                
        except ImportError as e:
            print(f"Cannot test integration: {str(e)}")
            self.skipTest(f"Integration test failed due to import error: {str(e)}")

if __name__ == '__main__':
    unittest.main() 