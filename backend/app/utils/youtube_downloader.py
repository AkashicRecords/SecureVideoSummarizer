import os
import subprocess
import logging
import tempfile
import time
import re
import shutil
from urllib.parse import urlparse, parse_qs
import uuid
import requests

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """Utility class for downloading and processing YouTube audio"""
    
    def __init__(self, temp_dir=None, cache_dir=None):
        """
        Initialize the YouTube downloader
        
        Args:
            temp_dir (str, optional): Directory for temporary files
            cache_dir (str, optional): Directory for caching downloaded audio
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cache_dir = cache_dir
        
        # Create cache directory if provided and doesn't exist
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def extract_video_id(self, url):
        """
        Extract the YouTube video ID from a URL
        
        Args:
            url (str): YouTube URL
            
        Returns:
            str: Video ID or None if not found
        """
        if not url:
            return None
            
        # Try direct ID (11 characters)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
            
        # Parse URL
        parsed_url = urlparse(url)
        
        # youtu.be format
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path.strip('/')
            
        # youtube.com format
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
            return video_id
            
        return None
    
    def validate_youtube_url(self, url):
        """
        Validate that a URL is a valid YouTube video URL
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        video_id = self.extract_video_id(url)
        return video_id is not None
    
    def check_cached_audio(self, video_id):
        """
        Check if audio for a video ID is already cached
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            str: Path to cached audio file or None if not found
        """
        if not self.cache_dir or not video_id:
            return None
            
        # Look for any file with video ID in the filename
        for filename in os.listdir(self.cache_dir):
            if video_id in filename and filename.endswith('.wav'):
                file_path = os.path.join(self.cache_dir, filename)
                
                # Check if file exists and is not empty
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logger.info(f"Found cached audio for video {video_id}: {file_path}")
                    return file_path
        
        return None
    
    def download_audio(self, url, output_path=None, cookies_file=None, format='wav', 
                       sample_rate=16000, channels=1, max_duration=None):
        """
        Download audio from YouTube URL
        
        Args:
            url (str): YouTube URL or video ID
            output_path (str, optional): Path to save the audio file
            cookies_file (str, optional): Path to cookies file for authentication
            format (str, optional): Audio format (default: wav)
            sample_rate (int, optional): Sample rate in Hz (default: 16000)
            channels (int, optional): Number of audio channels (default: 1)
            max_duration (int, optional): Maximum duration in seconds to download
            
        Returns:
            str: Path to downloaded audio file or None if failed
        """
        # Validate URL and extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL or video ID: {url}")
            return None
        
        # Check cache first
        cached_audio = self.check_cached_audio(video_id)
        if cached_audio:
            # If output_path was specified, copy to that location
            if output_path:
                shutil.copy2(cached_audio, output_path)
                logger.info(f"Copied cached audio to {output_path}")
                return output_path
            return cached_audio
        
        # Generate output path if not provided
        if not output_path:
            unique_id = f"{video_id}_{uuid.uuid4().hex[:8]}"
            output_path = os.path.join(self.temp_dir, f"yt_{unique_id}.{format}")
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(["yt-dlp", "--version"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE, 
                           check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("yt-dlp is not installed. Required for YouTube audio download.")
            return None
        
        # Check if ffmpeg is installed
        try:
            subprocess.run(["ffmpeg", "-version"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE, 
                           check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("ffmpeg is not installed. Required for audio conversion.")
            return None
        
        # Prepare yt-dlp command
        cmd = [
            "yt-dlp",
            "-x",                                   # Extract audio
            f"--audio-format", format,              # Set audio format
            "--audio-quality", "0",                 # Highest quality
            "-o", output_path,                      # Output path
            "--no-playlist",                        # Don't download playlists
        ]
        
        # Add postprocessor args for format conversion
        postprocess_args = f"-ar {sample_rate} -ac {channels}"
        cmd.extend(["--postprocessor-args", postprocess_args])
        
        # Add max duration if specified
        if max_duration:
            cmd.extend(["--max-filesize", f"{max_duration}s"])
        
        # Add cookies file if provided
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(["--cookies", cookies_file])
        
        # Add the video URL/ID
        cmd.append(url)
        
        logger.info(f"Running YouTube download: {' '.join(cmd)}")
        
        try:
            # Execute the download command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Collect output for logging
            output_lines = []
            for line in process.stdout:
                output_lines.append(line.strip())
                logger.debug(line.strip())
            
            # Wait for process to complete
            process.wait()
            
            # Check if download was successful
            if process.returncode != 0:
                error_output = "\n".join(output_lines[-10:])  # Last 10 lines
                logger.error(f"YouTube download failed with code {process.returncode}:\n{error_output}")
                return None
            
            # Verify the output file exists
            if not os.path.exists(output_path):
                logger.error(f"Output file not found after download: {output_path}")
                
                # Check for file with extension (yt-dlp sometimes adds extensions)
                parent_dir = os.path.dirname(output_path)
                filename = os.path.basename(output_path)
                name_without_ext = os.path.splitext(filename)[0]
                
                # Look for any file with the same name but different extension
                for file in os.listdir(parent_dir):
                    if file.startswith(name_without_ext) and file != filename:
                        actual_path = os.path.join(parent_dir, file)
                        logger.info(f"Found downloaded file with different name: {actual_path}")
                        return actual_path
                
                return None
            
            # Save to cache if available
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, f"yt_{video_id}.{format}")
                try:
                    shutil.copy2(output_path, cache_path)
                    logger.info(f"Cached audio in {cache_path}")
                except Exception as e:
                    logger.warning(f"Failed to cache audio: {str(e)}")
            
            logger.info(f"YouTube audio downloaded successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during YouTube download: {str(e)}")
            return None
    
    def cleanup_temp_files(self, max_age_hours=24):
        """
        Clean up temporary files older than the specified age
        
        Args:
            max_age_hours (int): Maximum age in hours
        """
        if not self.temp_dir:
            return
            
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Find all audio files in the temporary directory
        for filename in os.listdir(self.temp_dir):
            if filename.startswith('yt_') and (filename.endswith('.wav') or filename.endswith('.mp3')):
                file_path = os.path.join(self.temp_dir, filename)
                
                # Check if file is older than max age
                file_age = now - os.path.getctime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")

def download_stream(url, output_dir=None):
    """
    Download streaming videos using yt-dlp
    
    Args:
        url (str): URL of the video stream
        output_dir (str, optional): Directory to save the downloaded video
        
    Returns:
        str: Path to the downloaded video file or None if download failed
    """
    logger.info(f"Downloading streaming video from: {url}")
    
    # Create temp directory if not provided
    if not output_dir:
        output_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {output_dir}")
    
    # Generate a unique filename
    output_file = os.path.join(output_dir, f"stream_{int(time.time())}.mp4")
    
    # Check if yt-dlp is installed
    try:
        subprocess.run(["yt-dlp", "--version"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE, 
                       check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("yt-dlp is not installed. Required for video download.")
        return None
    
    try:
        # Set up the command with appropriate headers for CloudFront
        cmd = ["yt-dlp"]
        
        # For CloudFront URLs, add special headers
        if "cloudfront.net" in url:
            logger.info("Detected CloudFront URL, adding special headers")
            cmd.extend([
                "--add-header", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
                "--add-header", "Referer: https://olympus-learning.com/",
                "--add-header", "Origin: https://olympus-learning.com"
            ])
        
        # Add output file path
        cmd.extend(["-o", output_file])
        
        # Add URL
        cmd.append(url)
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        # Execute the download command
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Collect output for logging
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.strip())
            logger.debug(line.strip())
        
        # Wait for process to complete
        process.wait()
        
        # Check if download was successful
        if process.returncode != 0:
            error_output = "\n".join(output_lines[-10:])  # Last 10 lines
            logger.error(f"Video download failed with code {process.returncode}:\n{error_output}")
            return None
        
        # Verify the output file exists
        if not os.path.exists(output_file):
            logger.error(f"Output file not found after download: {output_file}")
            
            # Check directory for downloaded file (yt-dlp sometimes adds extensions)
            for file in os.listdir(output_dir):
                if file.startswith("stream_") and os.path.isfile(os.path.join(output_dir, file)):
                    actual_path = os.path.join(output_dir, file)
                    logger.info(f"Found downloaded file with different name: {actual_path}")
                    return actual_path
            
            return None
        
        logger.info(f"Video downloaded successfully: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        return None

def extract_audio_from_video(video_path, output_audio_path):
    """
    Extract audio from a video file using ffmpeg
    
    Args:
        video_path (str): Path to the video file
        output_audio_path (str): Path for the output audio file
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    logger.info(f"Extracting audio from video: {video_path}")
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE, 
                       check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("ffmpeg is not installed. Required for audio extraction.")
        return False
    
    try:
        # Construct the ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",                # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit encoding
            "-ar", "16000",         # 16kHz sample rate (good for speech recognition)
            "-ac", "1",             # Mono audio
            "-y",                   # Overwrite output file if exists
            output_audio_path
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        # Execute the command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Verify output file exists
        if not os.path.exists(output_audio_path):
            logger.error(f"Output audio file not created: {output_audio_path}")
            return False
        
        # Check if output file has content
        if os.path.getsize(output_audio_path) < 1000:  # Less than 1KB
            logger.error(f"Output audio file is too small: {os.path.getsize(output_audio_path)} bytes")
            return False
        
        logger.info(f"Audio extracted successfully: {output_audio_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error during audio extraction: {str(e)}")
        return False

# Create a singleton instance
youtube_downloader = YouTubeDownloader(
    cache_dir=os.environ.get('YOUTUBE_CACHE_DIR')
)

def youtube_downloader(video_url, output_dir=None):
    """Convenience function to download a YouTube video"""
    downloader = YouTubeDownloader(temp_dir=output_dir)
    return downloader.download_audio(video_url) 