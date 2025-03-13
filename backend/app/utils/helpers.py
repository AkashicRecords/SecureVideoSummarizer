# Helper functions for the application
import os
import uuid
from flask import current_app
import magic
import hashlib
from datetime import datetime

def validate_video_format(file):
    """
    Validates if the uploaded file is a valid video format
    """
    # Check file extension
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    if '.' not in file.filename:
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False
    
    # Check MIME type
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)  # Reset file pointer
    
    return mime.startswith('video/')

def generate_unique_id():
    """
    Generates a unique ID for videos and summaries
    """
    # Generate a UUID and remove hyphens
    return str(uuid.uuid4()).replace('-', '')

def get_video_path(video_id):
    """
    Returns the path to a video file based on its ID
    """
    videos_dir = current_app.config.get('VIDEOS_DIR', 'videos')
    return os.path.join(videos_dir, f"{video_id}.mp4")

def create_summary_directory(summary_id):
    """
    Creates a directory for storing summary data
    """
    summaries_dir = current_app.config.get('SUMMARIES_DIR', 'summaries')
    summary_dir = os.path.join(summaries_dir, summary_id)
    
    # Create directories if they don't exist
    os.makedirs(summary_dir, exist_ok=True)
    
    return summary_dir

def hash_password(password):
    """
    Hashes a password using SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()

def secure_filename(filename):
    """
    Makes a filename secure by removing potentially dangerous characters
    """
    # Remove path information
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
    
    # Add timestamp to make it unique
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    name, ext = os.path.splitext(filename)
    
    return f"{name}_{timestamp}{ext}" 