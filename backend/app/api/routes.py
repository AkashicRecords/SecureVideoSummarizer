from flask import Blueprint, request, jsonify, current_app, g, session, make_response
import os
import tempfile
import time
import uuid
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from app.utils.helpers import generate_unique_id, get_video_path, sanitize_input
from app.utils.error_handlers import APIError
from app.auth.routes import login_required
from app.summarizer.processor import (
    process_audio, VideoSummarizer, 
    transcribe_audio_enhanced, 
    summarize_text_enhanced,
    TranscriptionError
)
import logging
import json
import shutil
import subprocess
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Initialize rate limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@api_bp.errorhandler(429)
def handle_ratelimit_error(error):
    """Handle rate limit exceeded errors"""
    logger.warning(
        f"Rate limit exceeded | IP: {request.remote_addr} | "
        f"Endpoint: {request.endpoint}"
    )
    return jsonify(error="Rate limit exceeded. Please try again later."), 429

@api_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """Handle file size exceeded errors"""
    logger.warning(
        f"File too large | IP: {request.remote_addr} | "
        f"Endpoint: {request.endpoint}"
    )
    return jsonify(error="File size exceeds maximum limit."), 413

# Constants
SESSION_TIMEOUT = 3600  # 1 hour
MAX_SESSIONS = 100

def cleanup_old_sessions():
    """Clean up old sessions and their associated files"""
    if 'extension_jobs' not in session:
        return
    
    current_time = time.time()
    jobs = session['extension_jobs']
    expired_jobs = []
    total_size = 0
    
    # Calculate total session size and find expired jobs
    for job_id, job_data in jobs.items():
        # Estimate job data size
        job_size = len(str(job_data))  # Basic size estimation
        total_size += job_size
        
        if current_time - job_data['timestamp'] > SESSION_TIMEOUT:
            expired_jobs.append(job_id)
            # Cleanup associated files
            try:
                job_dir = os.path.join(current_app.config['TEMP_FOLDER'], job_id)
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
            except Exception as e:
                logger.error(f"Failed to cleanup files for job {job_id}: {str(e)}")
    
    # Remove expired jobs from session
    for job_id in expired_jobs:
        del jobs[job_id]
    
    # Check total session size (max 5MB)
    MAX_SESSION_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    if total_size > MAX_SESSION_SIZE:
        # Remove oldest jobs until under size limit
        sorted_jobs = sorted(jobs.items(), key=lambda x: x[1]['timestamp'])
        while total_size > MAX_SESSION_SIZE and sorted_jobs:
            job_id, job_data = sorted_jobs.pop(0)
            total_size -= len(str(job_data))
            del jobs[job_id]
    
    # Limit total number of sessions
    if len(jobs) > MAX_SESSIONS:
        oldest_jobs = sorted(jobs.items(), key=lambda x: x[1]['timestamp'])[:len(jobs) - MAX_SESSIONS]
        for job_id, _ in oldest_jobs:
            del jobs[job_id]
    
    session.modified = True
    
    # Log cleanup metrics
    logger.info(f"Session cleanup completed: {len(expired_jobs)} expired jobs removed, "
                f"{len(jobs)} active jobs remaining, "
                f"Total size: {total_size/1024:.2f}KB")

from app.utils.request_logger import RequestLogger

@api_bp.before_request
def before_request():
    """Set up request context and clean up old sessions"""
    # Generate a unique request ID and start time
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    # Clean up old sessions
    cleanup_old_sessions()
    
    # Log detailed request information
    RequestLogger.log_request()

@api_bp.after_request
def after_request(response):
    """Process a response before it is returned to the client"""
    
    # Handle CORS
    origin = request.headers.get('Origin')
    allowed_origins = current_app.config.get('ALLOWED_ORIGINS', [])
    
    # Handle both string and list types for allowed_origins
    if isinstance(allowed_origins, str):
        origins_list = allowed_origins.split(',') if allowed_origins else []
    else:
        origins_list = allowed_origins
    
    # Log the origin and allowed origins for debugging
    logger.debug(f"Request origin: {origin}")
    logger.debug(f"Allowed origins: {origins_list}")
    
    if origin:
        is_allowed = False
        
        # Check for exact match
        if origin in origins_list:
            is_allowed = True
            logger.debug(f"Origin {origin} found in allowed origins list")
        
        # Check for chrome-extension wildcard match
        elif origin.startswith('chrome-extension://'):
            extension_id = origin.split('/')[-1]
            if f"chrome-extension://{extension_id}" in origins_list or \
               "chrome-extension://*" in origins_list:
                is_allowed = True
                logger.debug(f"Chrome extension {extension_id} allowed")
        
        # Check for localhost with specific ports
        elif origin.startswith('http://localhost:'):
            port = origin.split(':')[-1]
            if f"http://localhost:{port}" in origins_list:
                is_allowed = True
                logger.debug(f"Localhost:{port} allowed")
        
        if is_allowed:
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Headers', 
                               'Content-Type,Authorization,X-Extension-ID')
            response.headers.add('Access-Control-Allow-Methods', 
                               'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Vary', 'Origin')  # Important for caching
        else:
            logger.warning(f"Origin {origin} not allowed")
            # Return a 403 Forbidden response for unauthorized origins
            if request.path.startswith('/api/extension/'):
                error_response = jsonify({
                    'error': {
                        'type': 'CORSError',
                        'message': 'Unauthorized origin',
                        'details': 'This endpoint is only accessible from authorized origins'
                    }
                })
                response = make_response(error_response, 403)
    
    return response

from app.utils.error_types import (
    BaseError, ValidationError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, RateLimitError, FileError, ProcessingError,
    StorageError, ConfigurationError, ExtensionError, SessionError
)

@api_bp.errorhandler(BaseError)
def handle_base_error(error):
    """Handle all custom errors"""
    RequestLogger.log_error(error, error.status_code)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': error.__class__.__name__,
            'details': {
                k: v for k, v in vars(error).items()
                if k not in ('message', 'status_code', 'error_code')
            }
        }
    })
    response.status_code = error.status_code
    return response

@api_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle validation errors"""
    RequestLogger.log_error(error, 400)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': 'ValidationError',
            'field': error.field
        }
    })
    response.status_code = 400
    return response

@api_bp.errorhandler(AuthenticationError)
def handle_authentication_error(error):
    """Handle authentication errors"""
    RequestLogger.log_error(error, 401)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': 'AuthenticationError'
        }
    })
    response.status_code = 401
    return response

@api_bp.errorhandler(RateLimitError)
def handle_rate_limit_error(error):
    """Handle rate limit errors"""
    RequestLogger.log_error(error, 429)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': 'RateLimitError',
            'limit': error.limit,
            'reset_time': error.reset_time
        }
    })
    response.status_code = 429
    return response

@api_bp.errorhandler(FileError)
def handle_file_error(error):
    """Handle file-related errors"""
    RequestLogger.log_error(error, 400)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': 'FileError',
            'file_type': error.file_type,
            'max_size': error.max_size
        }
    })
    response.status_code = 400
    return response

@api_bp.errorhandler(ProcessingError)
def handle_processing_error(error):
    """Handle processing errors"""
    RequestLogger.log_error(error, 500)
    response = jsonify({
        'error': {
            'code': error.error_code,
            'message': error.message,
            'type': 'ProcessingError',
            'stage': error.stage
        }
    })
    response.status_code = 500
    return response

@api_bp.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unexpected errors"""
    RequestLogger.log_error(error)
    response = jsonify({
        'error': {
            'code': 5000,
            'message': 'An unexpected error occurred',
            'type': 'UnexpectedError',
            'details': str(error) if current_app.debug else None
        }
    })
    response.status_code = 500
    return response

# Add CORS error handler
@api_bp.errorhandler(403)
def handle_cors_error(error):
    """Handle CORS-related errors"""
    logger.warning(f"CORS error: {error}")
    response = jsonify({
        'error': {
            'code': 4030,
            'message': 'CORS error: Origin not allowed',
            'type': 'CORSError'
        }
    })
    response.status_code = 403
    return response

@api_bp.route('/extension/status', methods=['GET'])
@limiter.limit("60 per minute")
def extension_status():
    """Check if the extension is properly connected to the backend"""
    logger.info(f"Request {g.request_id} | Checking extension status")
    
    # Get the raw value from the environment
    raw_env_value = os.environ.get('ALLOWED_ORIGINS', 'NOT_SET')
    logger.info(f"Request {g.request_id} | Raw ALLOWED_ORIGINS from env: {raw_env_value}")
    
    # Get the value from the config
    allowed_origins = current_app.config.get('ALLOWED_ORIGINS', [])
    logger.info(f"Request {g.request_id} | ALLOWED_ORIGINS from config: {allowed_origins}")
    
    # Handle both string and list types for allowed_origins
    if isinstance(allowed_origins, str):
        origins_list = allowed_origins.split(',') if allowed_origins else []
        logger.info(f"Request {g.request_id} | Split string into list: {origins_list}")
    else:
        origins_list = allowed_origins
        logger.info(f"Request {g.request_id} | Using existing list: {origins_list}")
    
    # Check for extension_id_placeholder
    for i, origin in enumerate(origins_list):
        if 'extension_id_placeholder' in origin.lower():
            logger.warning(f"Request {g.request_id} | Found placeholder in origin: {origin}")
            # Replace with wildcard
            origins_list[i] = "chrome-extension://*"
            logger.info(f"Request {g.request_id} | Replaced with wildcard: {origins_list[i]}")
    
    # Force update port 3000 to 8080
    for i, origin in enumerate(origins_list):
        if 'localhost:3000' in origin:
            origins_list[i] = origin.replace('localhost:3000', 'localhost:8080')
            logger.info(f"Request {g.request_id} | Replaced port 3000 with 8080: {origins_list[i]}")
    
    # Log the client's origin
    client_origin = request.headers.get('Origin', 'None')
    logger.info(f"Request {g.request_id} | Client origin: {client_origin}")
    
    # Check if the client's origin is in the allowed origins
    is_allowed = False
    if client_origin:
        # Check for exact match
        if client_origin in origins_list:
            is_allowed = True
            logger.info(f"Request {g.request_id} | Client origin is allowed (exact match)")
        # Check for wildcard match
        elif any(allowed.endswith('*') and client_origin.startswith(allowed[:-1]) for allowed in origins_list):
            is_allowed = True
            logger.info(f"Request {g.request_id} | Client origin is allowed (wildcard match)")
    
    logger.debug(f"Request {g.request_id} | Final allowed origins: {origins_list}")
    logger.debug(f"Request {g.request_id} | Client origin allowed: {is_allowed}")
    
    return jsonify({
        "status": "connected",
        "version": "1.0.0",
        "allowed_origins": origins_list,
        "client_origin": client_origin,
        "is_allowed": is_allowed
    })

@api_bp.route('/extension/ping', methods=['GET'])
@limiter.limit("60 per minute")
def extension_ping():
    """Simple ping endpoint for the extension to check backend connectivity"""
    logger.info(f"Request {g.request_id} | Extension ping received")
    
    # Extract extension ID from headers for logging
    extension_id = request.headers.get('X-Extension-ID', 'Unknown')
    logger.info(f"Request {g.request_id} | Extension ID: {extension_id}")
    
    # Log origin for debugging
    origin = request.headers.get('Origin', 'None')
    logger.info(f"Request {g.request_id} | Origin: {origin}")
    
    return jsonify({
        'success': True,
        'message': 'Backend connection successful',
        'timestamp': time.time()
    })

from app.utils.validators import RequestValidator

@api_bp.route('/extension/summarize', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
@RequestValidator.validate_json('video_data', 'options')
@RequestValidator.validate_extension_origin()
def extension_summarize():
    """Process video data from the extension and start summarization"""
    logger.info(f"Request {g.request_id} | Extension summarize request received")
    
    data = request.get_json()
    
    try:
        # Validate and sanitize video data
        video_data = RequestValidator.validate_video_data(data['video_data'])
        
        # Validate summary options
        options = RequestValidator.validate_summary_options(data['options'])
        
        # Generate job ID and store sanitized data
        job_id = generate_unique_id()
        
        if 'extension_jobs' not in session:
            session['extension_jobs'] = {}
        
        session['extension_jobs'][job_id] = {
            'video_data': video_data,
            'options': options,
            'status': 'processing',
            'summary': None,
            'timestamp': time.time(),
            'error': None
        }
        session.modified = True
        
        # Start processing in background
        import threading
        thread = threading.Thread(target=process_summary_job, args=(job_id, video_data, options))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Summarization started'
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise APIError(f'Validation error: {str(e)}', status_code=400)
    except Exception as e:
        logger.error(f"Failed to start summarization job: {str(e)}")
        raise APIError('Failed to start summarization', status_code=500)

@api_bp.route('/extension/summary_status', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
def extension_summary_status():
    """Check the status of a summarization job"""
    logger.info(f"Request {g.request_id} | Extension summary status request received")
    
    # Extract extension ID from headers for logging
    extension_id = request.headers.get('X-Extension-ID', 'Unknown')
    logger.info(f"Request {g.request_id} | Extension ID: {extension_id}")
    
    # Debug session contents
    logger.debug(f"Request {g.request_id} | Session contents: {dict(session)}")
    logger.debug(f"Request {g.request_id} | Session extension_jobs: {session.get('extension_jobs', 'None')}")
    
    # Check for test environment - flask.testing will be True in test mode
    is_test_env = current_app.config.get('TESTING', False)
    if is_test_env:
        logger.info(f"Request {g.request_id} | Running in test environment")
        
        # In test mode, ensure we're using the exact session data that was set in the test
        extension_jobs = session.get('extension_jobs', {})
        if extension_jobs:
            logger.info(f"Request {g.request_id} | Found test jobs in session: {list(extension_jobs.keys())}")
            latest_job_id = sorted(extension_jobs.keys(), 
                                 key=lambda k: extension_jobs[k]['timestamp'], 
                                 reverse=True)[0]
            job = extension_jobs[latest_job_id]
            
            status = job['status']
            logger.info(f"Request {g.request_id} | Test job {latest_job_id} status: {status}")
            
            if status == 'complete':
                return jsonify({
                    'success': True,
                    'status': 'complete',
                    'job_id': latest_job_id,
                    'summary': job['summary']
                })
            elif status == 'processing':
                return jsonify({
                    'success': True,
                    'status': 'processing',
                    'job_id': latest_job_id
                })
            else:  # error
                return jsonify({
                    'success': False,
                    'status': 'error',
                    'job_id': latest_job_id,
                    'message': job.get('error', 'Unknown error occurred')
                })
    
    # Get the latest job from session
    if 'extension_jobs' not in session or not session['extension_jobs']:
        logger.info(f"Request {g.request_id} | No active summarization jobs found, returning idle status")
        return jsonify({
            'success': True,
            'status': 'idle',
            'message': 'No active summarization jobs found'
        })
    
    # Get the most recent job (simpler than tracking job_id for demo purposes)
    extension_jobs = session.get('extension_jobs', {})
    logger.debug(f"Request {g.request_id} | Extension jobs: {extension_jobs}")
    
    if not extension_jobs:
        logger.info(f"Request {g.request_id} | No active summarization jobs found (empty dict), returning idle status")
        return jsonify({
            'success': True,
            'status': 'idle',
            'message': 'No active summarization jobs found'
        })
    
    latest_job_id = sorted(extension_jobs.keys(), 
                          key=lambda k: extension_jobs[k]['timestamp'], 
                          reverse=True)[0]
    job = extension_jobs[latest_job_id]
    
    logger.info(f"Request {g.request_id} | Job {latest_job_id} status: {job['status']}")
    
    if job['status'] == 'complete':
        return jsonify({
            'success': True,
            'status': 'complete',
            'job_id': latest_job_id,
            'summary': job['summary']
        })
    elif job['status'] == 'processing':
        return jsonify({
            'success': True,
            'status': 'processing',
            'job_id': latest_job_id
        })
    else:  # error
        return jsonify({
            'success': False,
            'status': 'error',
            'job_id': latest_job_id,
            'message': job.get('error', 'Unknown error occurred')
        })

@api_bp.route('/extension/save_summary', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
@RequestValidator.validate_json('summary', 'video_data')
@RequestValidator.validate_extension_origin()
def extension_save_summary():
    """Save a summary from the extension"""
    logger.info(f"Request {g.request_id} | Extension save summary request received")
    
    # Extract extension ID from headers for logging
    extension_id = request.headers.get('X-Extension-ID', 'Unknown')
    logger.info(f"Request {g.request_id} | Extension ID: {extension_id}")
    
    try:
        data = request.get_json()
        if save_summary(data):
            return jsonify({
                'success': True,
                'message': 'Summary saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save summary'
            }), 500
            
    except Exception as e:
        logger.error(f"Request {g.request_id} | Error saving summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def save_summary(summary_data):
    """Save a summary to the filesystem.
    
    Args:
        summary_data (dict): Dictionary containing summary and video data
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Generate a unique ID for this summary
        summary_id = generate_unique_id()
        
        # Create a summary object
        summary_obj = {
            'id': summary_id,
            'summary': summary_data.get('summary'),
            'video_data': summary_data.get('video_data'),
            'created_at': time.time(),
            'source': 'extension'
        }
        
        # Save the summary to a file
        summaries_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'summaries')
        os.makedirs(summaries_dir, exist_ok=True)
        
        summary_file = os.path.join(summaries_dir, f'summary_{summary_id}.json')
        with open(summary_file, 'w') as f:
            json.dump(summary_obj, f, indent=2)
        
        logger.info(f"Summary saved successfully with ID: {summary_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving summary: {str(e)}")
        return False

# Helper function to process the summary job (simulates async processing)
def process_summary_job(job_id, video_data, options):
    """Process a summarization job in the background"""
    logger.info(f"Background job {job_id} | Starting processing")
    
    try:
        # Sleep to simulate processing time
        import time
        time.sleep(5)  # Simulate 5 seconds of processing
        
        # Generate a mock summary for demo purposes
        title = video_data.get('title', 'Untitled Video')
        platform = video_data.get('platform', 'unknown')
        duration = video_data.get('duration', 0)
        minutes = int(duration / 60)
        seconds = int(duration % 60)
        
        summary = f"Summary of '{title}' ({minutes}:{seconds:02d}) from {platform} platform:\n\n"
        
        if 'key_points' in options.get('focus', []):
            summary += "Key points:\n"
            summary += "• The video explains the main concepts clearly\n"
            summary += "• Several examples are provided to illustrate the application\n"
            summary += "• The presenter emphasizes important techniques and methodologies\n\n"
        
        if 'detailed' in options.get('focus', []):
            summary += "Detailed notes:\n"
            summary += "The video begins with an introduction to the topic, followed by "
            summary += "a thorough explanation of the core concepts. Multiple examples "
            summary += "are used to demonstrate practical applications. The presenter "
            summary += "highlights key techniques that can be applied in various scenarios."
        
        if not options.get('focus'):
            summary += "This is a demonstration summary generated for testing purposes. "
            summary += "In a real implementation, this would be an actual summary of the video content "
            summary += "generated through audio transcription and analysis."
        
        # Update the job in the session
        from flask import session
        if 'extension_jobs' in session and job_id in session['extension_jobs']:
            session['extension_jobs'][job_id]['status'] = 'complete'
            session['extension_jobs'][job_id]['summary'] = summary
            session.modified = True
            logger.info(f"Background job {job_id} | Completed successfully")
        else:
            logger.error(f"Background job {job_id} | Job not found in session")
    
    except Exception as e:
        logger.exception(f"Background job {job_id} | Error during processing: {str(e)}")
        # Update job with error status
        from flask import session
        if 'extension_jobs' in session and job_id in session['extension_jobs']:
            session['extension_jobs'][job_id]['status'] = 'error'
            session['extension_jobs'][job_id]['error'] = str(e)
            session.modified = True

@api_bp.route('/transcribe', methods=['POST'])
@limiter.limit("30 per minute")
@RequestValidator.validate_file_upload('webm', 'wav', 'mp3', 'ogg', max_size=50*1024*1024)
@login_required
def transcribe():
    """
    Transcribe uploaded audio to text
    If video is provided, extract audio first
    Returns transcription and summary
    """
    try:
        # Track time for performance monitoring
        start_time = time.time()
        
        if 'audio' not in request.files:
            raise ValidationError("No audio file provided", field="audio")
            
        file = request.files['audio']
        
        if file.filename == '':
            raise ValidationError("No selected file", field="audio")
        
        # Get the playback rate modifier
        playback_rate = float(request.form.get('playback_rate', 1.0))
        logger.info(f"Received audio for transcription with playback rate: {playback_rate}x")
            
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save the uploaded file temporarily
        temp_path = os.path.join(temp_dir, "audio.wav")
        file.save(temp_path)
        logger.info(f"Audio file saved to: {temp_path}")
        
        # Convert audio to PCM WAV format for better compatibility
        transcription_path = os.path.join(temp_dir, "transcription.wav")
        cmd = [
            'ffmpeg', '-i', temp_path,
            '-vn',                    # No video
            '-acodec', 'pcm_s16le',   # PCM 16-bit encoding
            '-ar', '16000',          # 16kHz sample rate
            '-ac', '1',              # Mono channel
            '-f', 'wav',             # Force WAV format
            '-y',                    # Overwrite output if exists
            transcription_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Audio converted to PCM WAV format: {transcription_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting audio: {str(e)}")
            logger.error(f"FFmpeg stderr: {e.stderr.decode('utf-8', errors='replace')}")
            raise ProcessingError("Failed to convert audio to compatible format", stage='preprocessing')
        
        # Process the audio file
        try:
            # Process audio using our utility function
            result = process_audio(transcription_path)
            
            # Check if processing was successful
            if not result.get('success', False):
                error_msg = result.get('error', 'An error occurred during processing')
                error_type = result.get('error_type', 'unknown')
                
                # Determine appropriate status code based on error type
                status_code = 500
                if error_type == 'audio_processing':
                    status_code = 400
                
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'error_type': error_type,
                    'details': result.get('details', '')
                }), status_code
            
            # Extract results
            transcription = result.get('transcription', '')
            summary = result.get('summary', '')
        except Exception as e:
            # This should not happen since process_audio handles errors internally,
            # but we'll catch it just in case
            logger.error(f"Unexpected error during audio processing: {str(e)}")
            raise ProcessingError(f"Failed to process audio: {str(e)}", stage='processing')
        
        # Get video metadata if provided
        video_id = request.form.get('video_id', '')
        video_title = request.form.get('video_title', '')
        channel_name = request.form.get('channel_name', '')
        
        video_data = {}
        if video_id:
            video_data['id'] = video_id
        if video_title:
            video_data['title'] = video_title
        if channel_name:
            video_data['channel'] = channel_name
            
        # Generate a unique job ID
        job_id = uuid.uuid4().hex
        
        # Store in session for later retrieval if session is available
        try:
            if 'transcriptions' not in session:
                session['transcriptions'] = {}
                
            session['transcriptions'][job_id] = {
                'timestamp': datetime.now().isoformat(),
                'transcription': transcription,
                'summary': summary,
                'video_data': video_data
            }
            session.modified = True
        except Exception as e:
            logger.warning(f"Could not store in session: {str(e)}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return response with transcription, summary, and job_id
        return jsonify({
            'job_id': job_id,
            'processing_time': f"{processing_time:.2f}s",
            'success': True,
            'transcription': transcription,
            'summary': summary,
            'video_data': video_data
        })
        
    except ValidationError as e:
        # Handle validation errors
        logger.warning(f"Validation error in transcription: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'field': e.field if hasattr(e, 'field') else None
        }), 400
        
    except ProcessingError as e:
        # Handle processing errors
        logger.error(f"Processing error in transcribe endpoint: {str(e)}")
        
        # Extract stage from error if available
        stage = e.stage if hasattr(e, 'stage') else 'unknown'
        
        # Determine appropriate status code based on stage
        status_code = 500  # Default to server error
        if stage == 'preprocessing' or stage == 'audio_processing':
            status_code = 400  # Bad request for audio processing issues
        
        return jsonify({
            'success': False,
            'error': str(e),
            'stage': stage
        }), status_code
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in transcribe endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}",
            'stage': 'processing'
        }), 500
    
    finally:
        # Clean up temporary files
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Could not remove temp directory: {str(e)}")

def transcribe_audio(audio_path, playback_rate=1.0):
    """
    Transcribe audio file to text, accounting for playback rate.
    
    Args:
        audio_path: Path to the audio file
        playback_rate: The rate at which the audio was played (e.g., 1.5x, 2x)
        
    Returns:
        Transcribed text
    """
    try:
        logger.info(f"Transcribing audio with playback rate: {playback_rate}x")
        
        # If playback rate is not 1.0, we may need to adjust the audio
        if playback_rate != 1.0 and abs(playback_rate - 1.0) > 0.01:
            # Create a temporary file for the adjusted audio
            temp_dir = tempfile.mkdtemp()
            adjusted_path = os.path.join(temp_dir, 'adjusted_audio.webm')
            
            # Use ffmpeg to adjust the audio speed
            # For higher playback rates, we slow down the audio to normal speed
            # For lower playback rates, we speed up the audio to normal speed
            tempo_factor = 1.0 / playback_rate
            
            command = [
                'ffmpeg',
                '-i', audio_path,
                '-filter:a', f'atempo={tempo_factor}',
                '-y',  # Overwrite output file if it exists
                adjusted_path
            ]
            
            logger.info(f"Adjusting audio speed with factor: {tempo_factor}")
            try:
                subprocess.run(command, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg error: {e.stderr.decode()}")
                raise ProcessingError("Failed to adjust audio speed", stage='audio_processing')
            
            # Use the adjusted audio for transcription
            transcription_path = adjusted_path
        else:
            # Use the original audio if playback rate is close to 1.0
            transcription_path = audio_path
        
        # Use the processor module for transcription
        transcription = transcribe_audio_enhanced(transcription_path)
        
        # Clean up temporary files if created
        if playback_rate != 1.0 and abs(playback_rate - 1.0) > 0.01:
            shutil.rmtree(temp_dir)
        
        if not transcription:
            raise ProcessingError("Failed to transcribe audio: No transcription generated", stage='transcription')
        
        return transcription
        
    except ProcessingError:
        raise
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise ProcessingError(f"Failed to transcribe audio: {str(e)}", stage='transcription')

def summarize_text(text, length='medium', format_type='paragraph', focus=None):
    """
    Summarize text based on specified parameters.
    
    Args:
        text: The text to summarize
        length: The desired length of the summary ('short', 'medium', 'long')
        format_type: The format of the summary ('paragraph', 'bullets', 'numbered', 'key_points')
        focus: List of focus areas ('key_points', 'detailed')
        
    Returns:
        Summarized text
    """
    try:
        logger.info(f"Summarizing text with length: {length}, format: {format_type}, focus: {focus}")
        
        # Set word count limits based on length
        word_limits = {
            'short': (30, 100),
            'medium': (50, 150),
            'long': (100, 250)
        }
        
        min_words, max_words = word_limits.get(length, (50, 150))
        
        # TODO: Replace with actual summarization code
        # This is a placeholder for the actual summarization logic
        # In a real implementation, you would use a summarization service
        # or a local model like BART, T5, or GPT
        
        # Placeholder summary
        if format_type == 'paragraph':
            summary = "This is a placeholder paragraph summary. In a real implementation, this would be a concise summary of the transcribed text, formatted as a paragraph."
        elif format_type == 'bullets':
            summary = "• This is the first bullet point of a placeholder summary.\n• This is the second bullet point.\n• This is the third bullet point."
        elif format_type == 'numbered':
            summary = "1. This is the first point of a placeholder summary.\n2. This is the second point.\n3. This is the third point."
        elif format_type == 'key_points':
            summary = "KEY POINTS:\n• Main concept one\n• Main concept two\n• Main concept three"
        else:
            summary = "This is a placeholder summary in default format."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in summarize_text: {str(e)}")
        raise Exception(f"Failed to summarize text: {str(e)}")

@api_bp.route('/summarize/video/<video_id>', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
@RequestValidator.validate_json('options')
def summarize_video(video_id):
    """Summarize a video file that has been previously uploaded"""
    try:
        # Get summarization options from request
        options = request.get_json()
        
        # Log request details
        logger.info(f"Request {g.request_id} | Video summarization request for video_id: {video_id}")
        logger.debug(f"Request {g.request_id} | Summarization options: {options}")
        
        # Get the video path
        video_path = get_video_path(video_id)
        
        # Check if video exists
        if not os.path.exists(video_path):
            logger.warning(f"Request {g.request_id} | Video not found: {video_id}")
            raise ResourceNotFoundError(f"Video {video_id} not found", resource_type='video')
        
        try:
            # Validate and prepare options
            valid_lengths = {'short', 'medium', 'long'}
            valid_formats = {'paragraph', 'bullets', 'numbered', 'key_points'}
            valid_focus = {'key_points', 'detailed'}
            
            length = options.get('length', 'medium')
            format_type = options.get('format', 'bullets')
            focus = options.get('focus', ['key_points'])
            
            if length not in valid_lengths:
                raise ValidationError(f"Invalid length option: {length}", field='length')
            if format_type not in valid_formats:
                raise ValidationError(f"Invalid format option: {format_type}", field='format')
            if not all(f in valid_focus for f in focus):
                raise ValidationError("Invalid focus option", field='focus')
            
            summary_options = {
                'length': length,
                'format': format_type,
                'focus': focus,
                'min_length': max(50, int(options.get('min_length', 50))),
                'max_length': min(500, int(options.get('max_length', 150)))
            }
            
            # Log processing start
            logger.info(f"Request {g.request_id} | Starting video processing with options: {summary_options}")
            
            try:
                # Initialize the VideoSummarizer and process the video
                start_time = time.time()
                summarizer = VideoSummarizer()
                result = summarizer.process_video(video_path, summary_options)
                processing_time = time.time() - start_time
                
                if not result or 'transcript' not in result:
                    raise ProcessingError("Failed to process video", stage='summarization')
                
                # Log processing result
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
                
            except Exception as e:
                raise ProcessingError(f"Failed to process video: {str(e)}", stage='summarization')
                
        except ValueError as e:
            raise ValidationError(str(e), field='options')
            
    except ValidationError:
        raise
    except ResourceNotFoundError:
        raise
    except ProcessingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in summarize_video: {str(e)}", exc_info=True)
        raise ProcessingError(str(e), stage='initialization')

# Remove duplicate route - consolidated into extension_summary_status

@api_bp.route('/transcribe_url', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
@RequestValidator.validate_json('video_url')
def transcribe_url():
    """
    Transcribe and summarize a video from a direct URL.
    This is used for videos that are embedded in iframes or use custom players.
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        video_url = data['video_url']
        logger.info(f"Received direct video URL for transcription: {video_url}")
        
        # Get optional video data and options
        video_data = data.get('video_data', {})
        options = data.get('options', {})
        
        try:
            # For direct video URLs, we'll use a placeholder transcription and summary
            # In a real implementation, you would download the video and process it
            
            # Simulate processing time
            time.sleep(2)
            
            # Generate a placeholder transcription
            transcription = f"This is a placeholder transcription for the video: {video_data.get('title', 'Unknown video')}. In a real implementation, this would be the transcribed text from the video."
            
            # Generate a placeholder summary
            summary = f"Summary of '{video_data.get('title', 'Unknown video')}': This is a placeholder summary. In a real implementation, this would be a concise summary of the video content."
            
            # Store the summary in the session for the extension to retrieve
            if 'extension_jobs' not in session:
                session['extension_jobs'] = {}
            
            job_id = generate_unique_id()
            session['extension_jobs'][job_id] = {
                'status': 'completed',
                'summary': summary,
                'timestamp': time.time()
            }
            session.modified = True
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'transcription': transcription,
                'summary': summary,
                'processing_time': f"{processing_time:.2f}s",
                'video_data': video_data
            })
            
        except Exception as e:
            logger.error(f"Error processing video URL: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to process video URL: {str(e)}", stage='transcription')
            
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcribe_url: {str(e)}", exc_info=True)
        raise ProcessingError(str(e), stage='initialization')
