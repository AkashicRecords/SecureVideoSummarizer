# Helper functions for the application
import os
import uuid
import re
from flask import current_app
import magic
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
import time

logger = logging.getLogger(__name__)

def validate_video_format(file):
    """
    Validates if the uploaded file is a valid video format
    """
    # Save the file temporarily to check its type
    temp_path = os.path.join(current_app.config['VIDEOS_DIR'], 'temp_' + secure_filename(file.filename))
    file.save(temp_path)
    
    try:
        # Use python-magic to detect file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(temp_path)
        
        # Check if it's a video file
        is_valid = file_type.startswith('video/')
        
        # List of allowed video formats
        allowed_formats = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
        is_allowed_format = file_type in allowed_formats
        
        return is_valid and is_allowed_format
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Reset file pointer to beginning for future operations
        file.seek(0)

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

def validate_video_id(video_id):
    """Validate that the video ID is in the correct format"""
    # Our generate_unique_id function returns a UUID without hyphens
    uuid_pattern = re.compile(r'^[0-9a-f]{32}$')
    return bool(uuid_pattern.match(video_id))

def sanitize_input(text):
    """
    Sanitizes user input to prevent injection attacks
    
    Args:
        text (str): The input text to sanitize
        
    Returns:
        str: The sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[<>\'\"&;]', '', text)
    
    # Truncate extremely long inputs
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        
    return sanitized

def get_file_hash(file_path, algorithm='md5', block_size=65536):
    """
    Calculate the hash of a file
    
    Args:
        file_path (str): Path to the file
        algorithm (str): Hash algorithm to use (md5, sha1, sha256)
        block_size (int): Size of blocks to read from file
    
    Returns:
        str: File hash in hexadecimal format
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for hashing: {file_path}")
        return None
        
    hash_func = None
    if algorithm == 'md5':
        hash_func = hashlib.md5()
    elif algorithm == 'sha1':
        hash_func = hashlib.sha1()
    elif algorithm == 'sha256':
        hash_func = hashlib.sha256()
    else:
        logger.error(f"Unsupported hash algorithm: {algorithm}")
        return None
        
    try:
        with open(file_path, 'rb') as f:
            buffer = f.read(block_size)
            while buffer:
                hash_func.update(buffer)
                buffer = f.read(block_size)
                
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {str(e)}")
        return None 