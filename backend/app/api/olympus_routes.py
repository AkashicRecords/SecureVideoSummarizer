from flask import Blueprint, request, jsonify, current_app, session
import os
import json
import traceback
import logging
from werkzeug.exceptions import BadRequest
from datetime import datetime
import time
import uuid
import tempfile

from app.utils.youtube_downloader import youtube_downloader, download_stream, extract_audio_from_video
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from app.utils.helpers import generate_unique_id
from app.summarizer.processor import process_audio, summarize_text_enhanced
from app.auth.routes import login_required
from app.utils.validators import validate_extension_origin
from app.utils import validators
from app.utils.audio_processor import generate_transcript, generate_summary

# Create a blueprint for Olympus routes
olympus_bp = Blueprint('olympus', __name__, url_prefix='/api/olympus')

# Set up logging
logger = logging.getLogger(__name__)

@olympus_bp.route('/status', methods=['GET'])
def check_status():
    """Check the status of the Olympus integration."""
    logger.debug("Checking Olympus integration status")
    return jsonify({
        'status': 'ready',
        'extension_id': current_app.config.get('EXTENSION_ID', 'Unknown'),
        'supported_features': [
            'transcript_generation',
            'summary_generation',
            'cloudfront_streaming'
        ]
    })

@olympus_bp.route('/capture', methods=['POST'])
@validators.validate_extension_origin
def capture_transcript():
    """Process the transcript data from the Olympus player."""
    data = request.get_json()
    
    if not data:
        logger.warning("No data received in capture request")
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    logger.debug(f"Received transcript capture request: {data.keys()}")
    
    # Validate the required fields
    required_fields = ['transcript', 'videoMetadata']
    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    # Extract data
    transcript = data['transcript']
    video_metadata = data['videoMetadata']
    
    # Generate a session ID if not provided
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    try:
        # Process the transcript
        logger.info(f"Processing transcript for Olympus video: {video_metadata.get('title', 'Unknown')}")
        
        # Generate summary
        summary = generate_summary(transcript)
        
        # Store in session history
        session_data = {
            'id': session_id,
            'timestamp': int(time.time()),
            'platform': 'olympus',
            'videoMetadata': video_metadata,
            'transcript': transcript,
            'summary': summary
        }
        
        # Store in history (append to session history)
        if 'history' not in current_app.config:
            current_app.config['history'] = []
        
        current_app.config['history'].append(session_data)
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"Error processing Olympus transcript: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@olympus_bp.route('/process-url', methods=['POST'])
@validators.validate_extension_origin
def process_url():
    """Process a video URL from Olympus Learning Platform."""
    data = request.get_json()
    
    if not data or 'url' not in data:
        logger.warning("Missing URL in process-url request")
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    logger.info(f"Processing Olympus video URL: {url}")
    
    # Extract video metadata if provided
    video_metadata = data.get('videoMetadata', {})
    
    # Check if this is a test request with mock data
    is_test_mode = data.get('_test_mode', False)
    if is_test_mode:
        logger.info("Processing test request with mock data")
        
        # Use mock data if provided or generate default mock data
        mock_transcript = data.get('mock_transcript', "This is a mock transcript for testing the Olympus video platform API. The content discusses educational technology and secure learning environments.")
        mock_summary = data.get('mock_summary', "The video provides an overview of educational technology with a focus on secure learning environments in the Olympus platform.")
        
        # Generate a session ID
        session_id = str(uuid.uuid4())
        
        # Store in session history with mock data
        title = video_metadata.get('title', os.path.basename(url))
        session_data = {
            'id': session_id,
            'timestamp': int(time.time()),
            'platform': 'olympus',
            'videoMetadata': {
                'title': title,
                'src': url,
                'duration': video_metadata.get('duration', 0),
                'platform': 'olympus'
            },
            'transcript': mock_transcript,
            'summary': mock_summary,
            'is_mock': True
        }
        
        # Store in history
        if 'history' not in current_app.config:
            current_app.config['history'] = []
        
        current_app.config['history'].append(session_data)
        
        logger.info(f"Successfully processed test request with mock data, session ID: {session_id}")
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'transcript': mock_transcript,
            'summary': mock_summary,
            'is_mock': True
        })
    
    try:
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temp directory: {temp_dir}")
        
        # Handle CloudFront streaming URLs
        if 'cloudfront.net' in url or url.startswith('blob:'):
            logger.info("Detected CloudFront streaming URL or blob URL")
            
            # If we have direct stream sources in metadata, use those instead
            stream_sources = video_metadata.get('streamSources', [])
            if stream_sources and len(stream_sources) > 0:
                # Find the best quality MP4 or HLS source
                best_source = None
                for source in stream_sources:
                    if source.get('type') == 'video/mp4' or source.get('src', '').endswith('.mp4'):
                        best_source = source.get('src')
                        break
                
                # If no MP4, try HLS
                if not best_source:
                    for source in stream_sources:
                        if source.get('type') == 'application/x-mpegURL' or source.get('src', '').endswith('.m3u8'):
                            best_source = source.get('src')
                            break
                
                if best_source:
                    url = best_source
                    logger.info(f"Using stream source from metadata: {url}")
        
        # Create a timestamped output audio file
        timestamp = int(time.time())
        output_audio_file = os.path.join(temp_dir, f"olympus_audio_{timestamp}.wav")
        
        # Download and process the audio
        logger.info(f"Downloading audio from {url}")
        
        if url.startswith('blob:'):
            logger.warning("Cannot directly download blob URL, requesting download from extension")
            return jsonify({
                'success': False,
                'error': 'Blob URL not supported for direct download',
                'request_client_download': True  # Signal to extension to download via browser
            }), 400
        
        video_file = download_stream(url, temp_dir)
        if not video_file:
            return jsonify({
                'success': False,
                'error': 'Failed to download video'
            }), 500
        
        logger.info(f"Downloaded video to {video_file}")
        
        # Extract audio from the video file
        extract_audio_from_video(video_file, output_audio_file)
        logger.info(f"Extracted audio to {output_audio_file}")
        
        # Process the audio file
        transcript, summary = process_audio(output_audio_file)
        
        # Generate a session ID
        session_id = str(uuid.uuid4())
        
        # Store in session history
        title = video_metadata.get('title', os.path.basename(url))
        session_data = {
            'id': session_id,
            'timestamp': timestamp,
            'platform': 'olympus',
            'videoMetadata': {
                'title': title,
                'src': url,
                'duration': video_metadata.get('duration', 0),
                'platform': 'olympus'
            },
            'transcript': transcript,
            'summary': summary
        }
        
        # Store in history
        if 'history' not in current_app.config:
            current_app.config['history'] = []
        
        current_app.config['history'].append(session_data)
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'transcript': transcript,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"Error processing Olympus video: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@olympus_bp.route('/history', methods=['GET'])
def get_history():
    """Get the history of processed videos."""
    logger.debug("Retrieving Olympus processing history")
    
    # Filter history to only include Olympus videos
    olympus_history = [
        item for item in current_app.config.get('history', [])
        if item.get('platform') == 'olympus'
    ]
    
    return jsonify({
        'success': True,
        'history': olympus_history
    }) 