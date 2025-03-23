from flask import Blueprint, request, jsonify, current_app, session
import os
import json
import traceback
import logging
from werkzeug.exceptions import BadRequest, InternalServerError
from datetime import datetime
import tempfile
import time

from app.utils.youtube_downloader import youtube_downloader
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from app.utils.helpers import generate_unique_id, get_file_hash
from app.summarizer.processor import process_audio, validate_audio
from app.auth.routes import login_required

# Create a blueprint for YouTube routes
youtube_bp = Blueprint('youtube', __name__, url_prefix='/api/youtube')

# Set up logging
logger = logging.getLogger(__name__)

@youtube_bp.route('/validate-url', methods=['POST'])
def validate_url():
    """Validate a YouTube URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'valid': False, 'error': 'URL is required'}), 400
        
        url = data['url']
        is_valid = youtube_downloader.validate_youtube_url(url)
        
        if is_valid:
            video_id = youtube_downloader.extract_video_id(url)
            return jsonify({
                'valid': True,
                'video_id': video_id
            })
        else:
            return jsonify({
                'valid': False,
                'error': 'Invalid YouTube URL'
            })
            
    except Exception as e:
        logger.error(f"Error validating YouTube URL: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

@youtube_bp.route('/process', methods=['POST'])
@login_required
def process_youtube_audio():
    """Process audio from a YouTube video"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'YouTube URL is required'}), 400
        
        url = data.get('url')
        options = data.get('options', {})
        
        # Extract video_id for logging and caching
        video_id = youtube_downloader.extract_video_id(url)
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid YouTube URL'}), 400
        
        # Generate a unique job ID for tracking
        job_id = generate_unique_id()
        session_id = session.get('session_id', 'anonymous')
        
        logger.info(f"Starting YouTube processing job {job_id} for video {video_id} (session: {session_id})")
        
        # Get cookies file from config if available (for age-restricted videos)
        cookies_file = current_app.config.get('YOUTUBE_COOKIES_FILE')
        
        # Download audio
        start_time = time.time()
        audio_path = youtube_downloader.download_audio(
            url=url,
            cookies_file=cookies_file,
            format='wav',
            sample_rate=16000,
            channels=1,
            max_duration=None  # No maximum duration
        )
        
        if not audio_path:
            return jsonify({
                'success': False,
                'error': 'Failed to download audio from YouTube',
                'error_type': 'download_error'
            }), 500
        
        download_time = time.time() - start_time
        logger.info(f"Downloaded YouTube audio in {download_time:.2f}s: {audio_path}")
        
        # Validate audio file
        if not validate_audio(audio_path):
            return jsonify({
                'success': False,
                'error': 'Invalid audio file downloaded from YouTube',
                'error_type': 'validation_error'
            }), 500
        
        # Get file info for logging
        file_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
        file_hash = get_file_hash(audio_path)
        
        logger.info(f"Processing YouTube audio: {audio_path} ({file_size:.2f} MB, hash: {file_hash})")
        
        # Process the audio
        try:
            result = process_audio(audio_path, options)
            
            # Add metadata
            result['metadata'] = {
                'video_id': video_id,
                'job_id': job_id,
                'processing_time': time.time() - start_time,
                'download_time': download_time,
                'file_size_mb': file_size,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(result)
            
        except (AudioProcessingError, TranscriptionError, SummarizationError) as e:
            logger.error(f"Error processing YouTube audio: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in YouTube processing: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': 'server_error'
        }), 500

@youtube_bp.route('/status', methods=['GET'])
def youtube_status():
    """Check the status of the YouTube processing service"""
    try:
        # Check if yt-dlp is installed
        yt_dlp_installed = True
        try:
            import subprocess
            subprocess.run(["yt-dlp", "--version"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
        except:
            yt_dlp_installed = False
        
        # Check if ffmpeg is installed
        ffmpeg_installed = True
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
        except:
            ffmpeg_installed = False
        
        # Get cache info if available
        cache_info = {}
        cache_dir = os.environ.get('YOUTUBE_CACHE_DIR')
        if cache_dir and os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.startswith('yt_')]
            cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files) / (1024 * 1024)
            
            cache_info = {
                'enabled': True,
                'directory': cache_dir,
                'files': len(cache_files),
                'size_mb': round(cache_size, 2)
            }
        else:
            cache_info = {
                'enabled': False
            }
            
        return jsonify({
            'status': 'ok' if (yt_dlp_installed and ffmpeg_installed) else 'degraded',
            'dependencies': {
                'yt_dlp': yt_dlp_installed,
                'ffmpeg': ffmpeg_installed
            },
            'cache': cache_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking YouTube status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500 