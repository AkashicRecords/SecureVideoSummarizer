from flask import Blueprint, request, jsonify, current_app, send_file
import os
from werkzeug.utils import secure_filename
from app.utils.helpers import generate_unique_id, validate_video_format
from app.utils.error_handlers import APIError

video = Blueprint('video', __name__)

@video.route('/upload', methods=['POST'])
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
        
        current_app.logger.info(f"Video uploaded successfully: {filename}, ID: {video_id}")
        
        return jsonify({
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "original_filename": filename
        })
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error uploading video: {str(e)}")
        raise APIError(f"Failed to upload video: {str(e)}", 500)

@video.route('/<video_id>', methods=['GET'])
def get_video(video_id):
    """Get a video by its ID"""
    try:
        videos_dir = current_app.config['VIDEOS_DIR']
        file_path = os.path.join(videos_dir, f"{video_id}.mp4")
        
        if not os.path.exists(file_path):
            raise APIError("Video not found", 404)
            
        return send_file(file_path, mimetype='video/mp4')
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error retrieving video: {str(e)}")
        raise APIError(f"Failed to retrieve video: {str(e)}", 500)

@video.route('/videos', methods=['GET'])
def list_videos():
    """List all videos for the authenticated user"""
    try:
        videos = []
        videos_dir = current_app.config['VIDEOS_DIR']
        
        if os.path.exists(videos_dir):
            for filename in os.listdir(videos_dir):
                if filename.endswith('.mp4'):
                    video_id = os.path.splitext(filename)[0]
                    videos.append({
                        "video_id": video_id,
                        "filename": filename
                    })
        
        return jsonify({"videos": videos})
        
    except Exception as e:
        current_app.logger.error(f"Error listing videos: {str(e)}")
        raise APIError(f"Failed to list videos: {str(e)}", 500) 