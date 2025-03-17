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
import json
import shutil
import subprocess

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
def transcribe():
    """
    Transcribe and summarize audio received from the frontend or browser extension.
    """
    start_time = time.time()
    
    try:
        # Check if audio file is in the request
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        
        # Get video data and options if provided
        video_data = {}
        options = {}
        playback_rate = 1.0  # Default playback rate
        
        if 'video_data' in request.form:
            try:
                video_data = json.loads(request.form['video_data'])
            except json.JSONDecodeError:
                logger.warning("Invalid video_data JSON format")
        
        if 'options' in request.form:
            try:
                options = json.loads(request.form['options'])
            except json.JSONDecodeError:
                logger.warning("Invalid options JSON format")
        
        if 'playback_rate' in request.form:
            try:
                playback_rate = float(request.form['playback_rate'])
                if playback_rate <= 0:
                    playback_rate = 1.0  # Reset to default if invalid
            except ValueError:
                logger.warning("Invalid playback_rate value")
        
        logger.info(f"Received audio for transcription with playback rate: {playback_rate}x")
        
        # Save the audio file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'audio.webm')
        audio_file.save(temp_path)
        
        # Process the audio file
        transcription = transcribe_audio(temp_path, playback_rate)
        
        # Generate summary based on transcription
        summary = summarize_text(
            transcription, 
            length=options.get('length', 'medium'),
            format_type=options.get('format', 'paragraph'),
            focus=options.get('focus', ['key_points'])
        )
        
        # Store the summary in the session for the extension to retrieve
        session['summary_status'] = 'completed'
        session['summary_text'] = summary
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'summary': summary,
            'processing_time': f"{processing_time:.2f}s",
            'video_data': video_data
        })
        
    except Exception as e:
        logger.error(f"Error in transcribe endpoint: {str(e)}")
        session['summary_status'] = 'error'
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
            subprocess.run(command, check=True, capture_output=True)
            
            # Use the adjusted audio for transcription
            transcription_path = adjusted_path
        else:
            # Use the original audio if playback rate is close to 1.0
            transcription_path = audio_path
        
        # TODO: Replace with actual transcription code
        # This is a placeholder for the actual transcription logic
        # In a real implementation, you would use a speech-to-text service
        # such as Google Speech-to-Text, AWS Transcribe, or Whisper
        
        # Placeholder transcription
        transcription = "This is a placeholder transcription. In a real implementation, this would be the transcribed text from the audio file."
        
        # Clean up temporary files if created
        if playback_rate != 1.0 and abs(playback_rate - 1.0) > 0.01:
            shutil.rmtree(temp_dir)
        
        return transcription
        
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise Exception(f"Failed to transcribe audio: {str(e)}")

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

@api_bp.route('/extension/summary_status', methods=['GET'])
def check_summary_status():
    """Check the status of the current summary operation."""
    logger.info(f"Request {g.request_id} | Checking summary status")
    
    # Get the summary status from the session or some storage mechanism
    status, summary = get_summary_status()
    
    response = {'status': status}
    
    if status == 'completed' and summary:
        response['summary'] = summary
        logger.info(f"Request {g.request_id} | Summary is complete, returning summary of length {len(summary)}")
    else:
        logger.info(f"Request {g.request_id} | Summary status: {status}")
    
    return jsonify(response)

@api_bp.route('/extension/save_summary', methods=['POST'])
def extension_save_summary():
    """Save a summary generated from the extension."""
    logger.info(f"Request {g.request_id} | Extension request to save summary")
    
    data = request.get_json()
    
    if not data or 'summary' not in data or 'video_data' not in data:
        logger.warning(f"Request {g.request_id} | Invalid request data for saving summary")
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    summary = data['summary']
    video_data = data['video_data']
    
    # Save the summary
    logger.info(f"Request {g.request_id} | Saving summary for video: {video_data.get('title', 'Unknown video')}")
    success = save_summary(summary, video_data)
    
    if success:
        logger.info(f"Request {g.request_id} | Summary saved successfully")
        return jsonify({'success': True})
    else:
        logger.error(f"Request {g.request_id} | Failed to save summary")
        return jsonify({'success': False, 'error': 'Failed to save summary'}), 500

# Helper functions for extension endpoints
def get_summary_status():
    """Get the status of the current summary operation.
    
    Returns:
        tuple: (status, summary) where status is one of ['idle', 'processing', 'completed', 'error']
              and summary is the generated summary text (or None if not completed)
    """
    # In a real implementation, this would check the status in a database or cache
    # For now, we'll just return a mock status
    from flask import session
    
    session_key = 'summary_status'
    summary_key = 'summary_text'
    
    status = session.get(session_key, 'idle')
    summary = session.get(summary_key, None)
    
    logger.debug(f"Summary status: {status}, Summary present: {'Yes' if summary else 'No'}")
    
    return status, summary

def save_summary(summary, video_data):
    """Save a summary to the database.
    
    Args:
        summary (str): The generated summary text
        video_data (dict): Metadata about the source video
        
    Returns:
        bool: True if the summary was saved successfully, False otherwise
    """
    try:
        import datetime
        import json
        
        # In a real implementation, this would save to a database
        # For now, we'll just save to a file
        summary_dir = current_app.config.get('SUMMARIES_DIR', 'summaries')
        os.makedirs(summary_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"summary_{timestamp}.json"
        
        with open(os.path.join(summary_dir, filename), 'w') as f:
            json.dump({
                'summary': summary,
                'video_data': video_data,
                'timestamp': timestamp
            }, f, indent=2)
        
        logger.info(f"Saved summary to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving summary: {str(e)}", exc_info=True)
        return False 