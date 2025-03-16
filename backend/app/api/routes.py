from flask import Blueprint, request, jsonify, current_app, g
import os
import tempfile
import time
import uuid
from werkzeug.utils import secure_filename
from app.utils.helpers import generate_unique_id, get_video_path
from app.utils.error_handlers import APIError
from app.auth.routes import login_required
from app.summarizer.processor import process_audio, VideoSummarizer
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.before_request
def before_request():
    """Set up request context for logging"""
    # Generate a unique request ID
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    # Log the incoming request
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    endpoint = request.endpoint
    method = request.method
    
    logger.info(
        f"Request started | ID: {g.request_id} | IP: {client_ip} | "
        f"Method: {method} | Endpoint: {endpoint} | User-Agent: {user_agent}"
    )
    
    # Log request parameters (if any)
    if request.args:
        logger.debug(f"Request {g.request_id} | Query params: {dict(request.args)}")
    
    # Log request JSON body (if any)
    if request.is_json:
        logger.debug(f"Request {g.request_id} | JSON body: {request.json}")
    
    # Log files (if any)
    if request.files:
        file_info = {name: f.filename for name, f in request.files.items()}
        logger.debug(f"Request {g.request_id} | Files: {file_info}")

@api_bp.after_request
def after_request(response):
    """Log request completion and timing"""
    if hasattr(g, 'request_id') and hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        status_code = response.status_code
        
        logger.info(
            f"Request completed | ID: {g.request_id} | "
            f"Status: {status_code} | Duration: {duration:.3f}s"
        )
    
    return response

@api_bp.errorhandler(APIError)
def handle_api_error(error):
    """Handle API errors with proper logging"""
    if hasattr(g, 'request_id'):
        logger.error(
            f"API Error | Request ID: {g.request_id} | "
            f"Status: {error.status_code} | Error: {error.message}"
        )
    
    response = jsonify(error=error.message)
    response.status_code = error.status_code
    return response

@api_bp.route('/extension/status', methods=['GET'])
def extension_status():
    """Check if the extension is properly connected to the backend"""
    logger.info(f"Request {g.request_id} | Checking extension status")
    
    allowed_origins = current_app.config.get('ALLOWED_ORIGINS', '')
    origins_list = allowed_origins.split(',') if allowed_origins else []
    
    logger.debug(f"Request {g.request_id} | Allowed origins: {origins_list}")
    
    return jsonify({
        "status": "connected",
        "version": "1.0.0",
        "allowed_origins": origins_list
    })

@api_bp.route('/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    """Transcribe and summarize audio from the React UI"""
    try:
        # Log user information
        user_info = request.headers.get('X-User-Email') or 'Unknown user'
        logger.info(f"Request {g.request_id} | Transcribe request from {user_info}")
        
        if 'audio' not in request.files:
            logger.warning(f"Request {g.request_id} | No audio file provided")
            raise APIError("No audio file provided", 400)
            
        audio_file = request.files['audio']
        filename = audio_file.filename
        file_size = 0
        
        # Log file information
        logger.info(f"Request {g.request_id} | Processing audio file: {filename}")
        
        # Save the audio file temporarily
        temp_dir = current_app.config.get('TEMP_DIR', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_audio_path = os.path.join(temp_dir, f"temp_{generate_unique_id()}.webm")
        audio_file.save(temp_audio_path)
        
        # Get file size for logging
        file_size = os.path.getsize(temp_audio_path)
        logger.info(f"Request {g.request_id} | Saved temporary file: {temp_audio_path} | Size: {file_size} bytes")
        
        # Process the audio file
        logger.info(f"Request {g.request_id} | Starting audio processing")
        start_process = time.time()
        result = process_audio(temp_audio_path)
        process_time = time.time() - start_process
        
        # Log processing result
        if result.get('success', False):
            transcription_length = len(result.get('transcription', ''))
            summary_length = len(result.get('summary', ''))
            logger.info(
                f"Request {g.request_id} | Processing successful | "
                f"Duration: {process_time:.3f}s | "
                f"Transcription length: {transcription_length} chars | "
                f"Summary length: {summary_length} chars"
            )
        else:
            error_type = result.get('error_type', 'unknown')
            error_msg = result.get('error', 'Unknown error')
            logger.error(
                f"Request {g.request_id} | Processing failed | "
                f"Error type: {error_type} | Error: {error_msg}"
            )
        
        # Clean up
        try:
            os.remove(temp_audio_path)
            logger.debug(f"Request {g.request_id} | Removed temporary file: {temp_audio_path}")
        except Exception as e:
            logger.warning(f"Request {g.request_id} | Failed to remove temporary file: {str(e)}")
        
        return jsonify(result)
        
    except APIError as e:
        # This will be caught by the errorhandler
        raise
    except Exception as e:
        logger.error(
            f"Request {g.request_id} | Unexpected error processing audio: {str(e)}",
            exc_info=True  # Include stack trace
        )
        raise APIError(f"Failed to process audio: {str(e)}", 500)

@api_bp.route('/summarize/video/<video_id>', methods=['POST'])
@login_required
def summarize_video(video_id):
    """Summarize a video file that has been previously uploaded"""
    try:
        # Get summarization options from request
        options = request.json or {}
        
        # Log request details
        logger.info(f"Request {g.request_id} | Video summarization request for video_id: {video_id}")
        logger.debug(f"Request {g.request_id} | Summarization options: {options}")
        
        # Get the video path
        video_path = get_video_path(video_id)
        
        # Check if video exists
        if not os.path.exists(video_path):
            logger.warning(f"Request {g.request_id} | Video not found: {video_id}")
            raise APIError("Video not found", 404)
        
        # Prepare options
        summary_options = {
            'length': options.get('length', 'medium'),  # short, medium, long
            'format': options.get('format', 'bullets'),  # paragraph, bullets, numbered, key_points
            'focus': options.get('focus', ['key_points']),  # key_points, detailed
            'min_length': options.get('min_length', 50),
            'max_length': options.get('max_length', 150)
        }
        
        # Log processing start
        logger.info(f"Request {g.request_id} | Starting video processing with options: {summary_options}")
        
        # Initialize the VideoSummarizer and process the video
        start_time = time.time()
        summarizer = VideoSummarizer()
        result = summarizer.process_video(video_path, summary_options)
        processing_time = time.time() - start_time
        
        # Log processing result
        if result and 'transcript' in result:
            transcript_length = len(result.get('transcript', ''))
            summary_length = len(result.get('summary', ''))
            logger.info(
                f"Request {g.request_id} | Video processing successful | "
                f"Duration: {processing_time:.3f}s | "
                f"Transcript length: {transcript_length} chars | "
                f"Summary length: {summary_length} chars"
            )
            
            # Return the result with additional metadata
            return jsonify({
                "success": True,
                "video_id": video_id,
                "transcript": result.get('transcript', ''),
                "summary": result.get('summary', ''),
                "processing_time": f"{processing_time:.2f}s"
            })
        else:
            # If there was an error in the result
            logger.error(f"Request {g.request_id} | Video processing failed: {result}")
            return jsonify({
                "success": False,
                "video_id": video_id,
                "error": "Failed to process video",
                "details": result
            }), 500
            
    except APIError as e:
        # This will be caught by the errorhandler
        raise
    except Exception as e:
        logger.error(
            f"Request {g.request_id} | Unexpected error summarizing video: {str(e)}",
            exc_info=True  # Include stack trace
        )
        raise APIError(f"Failed to summarize video: {str(e)}", 500) 