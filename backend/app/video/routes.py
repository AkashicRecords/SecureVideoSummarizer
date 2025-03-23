from flask import Blueprint, request, jsonify, current_app, send_file, abort, session
import os
from werkzeug.utils import secure_filename
from app.utils.helpers import generate_unique_id, validate_video_format, get_video_path, validate_video_id
from app.utils.error_handlers import APIError
from app.auth.routes import login_required
import mimetypes
import logging
from datetime import datetime

video_bp = Blueprint('video', __name__)
logger = logging.getLogger(__name__)

@video_bp.route('/upload', methods=['POST'])
@login_required
def upload_video():
    """Upload a video file"""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            raise APIError("No file part in the request", 400)
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            raise APIError("No selected file", 400)
            
        # Validate file format
        if not validate_video_format(file):
            raise APIError("Invalid video format", 400)
            
        # Generate a unique ID for the video
        video_id = generate_unique_id()
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        videos_dir = current_app.config['VIDEOS_DIR']
        file_path = os.path.join(videos_dir, f"{video_id}.mp4")
        
        file.save(file_path)
        
        # Store video metadata (in a real app, this would go to a database)
        # For now, we'll store it in a JSON file
        metadata = {
            "video_id": video_id,
            "original_filename": filename,
            "upload_time": datetime.now().isoformat(),
            "uploader": session.get('user_info', {}).get('email', 'anonymous'),
            "file_size": os.path.getsize(file_path),
            "mime_type": mimetypes.guess_type(filename)[0]
        }
        
        # In a real app, save metadata to database
        # For now, log it
        logger.info(f"Video uploaded: {metadata}")
        
        return jsonify({
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "original_filename": filename
        })
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise APIError(f"Failed to upload video: {str(e)}", 500)

@video_bp.route('/<video_id>', methods=['GET'])
@login_required
def get_video(video_id):
    """Retrieve a video file by ID"""
    try:
        # Validate video ID format
        if not validate_video_id(video_id):
            raise APIError("Invalid video ID format", 400)
        
        # Get the video path
        video_path = get_video_path(video_id)
        
        # Check if video exists
        if not os.path.exists(video_path):
            logger.warning(f"Video not found: {video_id}")
            raise APIError("Video not found", 404)
        
        # Log access
        logger.info(f"Video accessed: {video_id} by {session.get('user_info', {}).get('email', 'anonymous')}")
        
        # Return the video file
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"video_{video_id}.mp4"
        )
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        logger.error(f"Error retrieving video: {str(e)}")
        raise APIError(f"Failed to retrieve video: {str(e)}", 500)

@video_bp.route('/<video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    """Delete a video file by ID"""
    try:
        # Validate video ID format
        if not validate_video_id(video_id):
            raise APIError("Invalid video ID format", 400)
        
        # Get the video path
        video_path = get_video_path(video_id)
        
        # Check if video exists
        if not os.path.exists(video_path):
            logger.warning(f"Video not found for deletion: {video_id}")
            raise APIError("Video not found", 404)
        
        # Delete the video file
        os.remove(video_path)
        
        # Log deletion
        logger.info(f"Video deleted: {video_id} by {session.get('user_info', {}).get('email', 'anonymous')}")
        
        return jsonify({
            "message": "Video deleted successfully",
            "video_id": video_id
        })
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        raise APIError(f"Failed to delete video: {str(e)}", 500)

@video_bp.route('/list', methods=['GET'])
@login_required
def list_videos():
    """List all videos available to the user"""
    try:
        videos_dir = current_app.config['VIDEOS_DIR']
        videos = []
        
        # In a real app, this would query a database
        # For now, we'll just list files in the videos directory
        for filename in os.listdir(videos_dir):
            if filename.endswith('.mp4'):
                video_id = filename.split('.')[0]
                video_path = os.path.join(videos_dir, filename)
                
                videos.append({
                    "video_id": video_id,
                    "file_size": os.path.getsize(video_path),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(video_path)).isoformat()
                })
        
        return jsonify({
            "videos": videos,
            "count": len(videos)
        })
        
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        raise APIError(f"Failed to list videos: {str(e)}", 500) 