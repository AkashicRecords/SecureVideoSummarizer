from functools import wraps
from flask import request, jsonify
import re
from app.utils.request_logger import RequestLogger
import os

class RequestValidator:
    @staticmethod
    def validate_json(*required_fields):
        """Decorator to validate JSON request data"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not request.is_json:
                    error = "Request must be JSON"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400

                data = request.get_json()
                missing_fields = [field for field in required_fields 
                                if field not in data]
                
                if missing_fields:
                    error = f"Missing required fields: {', '.join(missing_fields)}"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def validate_file_upload(*allowed_extensions, max_size=50*1024*1024):
        """Decorator to validate file uploads"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'audio' not in request.files:
                    error = "No file provided"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400

                file = request.files['audio']
                if not file.filename:
                    error = "No file selected"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400

                # Check file extension
                ext = file.filename.rsplit('.', 1)[1].lower() \
                    if '.' in file.filename else ''
                if ext not in allowed_extensions:
                    error = f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400

                # Check file size
                file.seek(0, 2)  # Seek to end of file
                size = file.tell()
                file.seek(0)  # Reset file pointer
                if size > max_size:
                    error = f"File size exceeds maximum limit of {max_size/1024/1024}MB"
                    RequestLogger.log_error(ValueError(error), 400)
                    return jsonify(error=error), 400

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def validate_extension_origin():
        """Decorator to validate Chrome extension origin"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                origin = request.headers.get('Origin', '')
                if not origin.startswith('chrome-extension://'):
                    error = "Invalid origin. Must be a Chrome extension."
                    RequestLogger.log_error(ValueError(error), 403)
                    return jsonify(error=error), 403
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def sanitize_input(value):
        """Sanitize user input to prevent injection attacks"""
        if not isinstance(value, str):
            return value
        
        # Remove any potential script tags
        value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.I|re.S)
        # Remove any HTML tags
        value = re.sub(r'<[^>]*?>', '', value)
        # Remove any potential SQL injection patterns
        value = re.sub(r'(\b(union|select|insert|update|delete|drop|alter)\b)', 
                      lambda m: ''.join('*' for _ in m.group()), 
                      value, 
                      flags=re.I)
        return value.strip()

    @staticmethod
    def validate_video_data(data):
        """Validate video metadata"""
        required_fields = ['title', 'duration', 'src', 'platform']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValueError(f"Missing required video data fields: {', '.join(missing_fields)}")
        
        # Sanitize string fields
        data['title'] = RequestValidator.sanitize_input(data['title'])
        data['src'] = RequestValidator.sanitize_input(data['src'])
        data['platform'] = RequestValidator.sanitize_input(data['platform'])
        
        # Validate numeric fields
        try:
            data['duration'] = float(data['duration'])
            if data['duration'] <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("Invalid duration value")
        
        return data

    @staticmethod
    def validate_summary_options(options):
        """Validate summary generation options"""
        valid_lengths = {'short', 'medium', 'long'}
        valid_formats = {'paragraph', 'bullets', 'numbered', 'key_points'}
        
        if 'length' in options and options['length'] not in valid_lengths:
            raise ValueError(f"Invalid length option. Must be one of: {', '.join(valid_lengths)}")
        
        if 'format' in options and options['format'] not in valid_formats:
            raise ValueError(f"Invalid format option. Must be one of: {', '.join(valid_formats)}")
        
        if 'focus' in options and not isinstance(options['focus'], list):
            raise ValueError("Focus must be a list of areas to focus on")
        
        return options

# Module-level validator functions
def validate_extension_origin(f):
    """Decorator to validate that request originated from our Chrome extension"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        origin = request.headers.get('Origin', '')
        allowed_extension_ids = os.environ.get('ALLOWED_EXTENSION_IDS', '').split(',')
        
        # Allow localhost development
        if request.remote_addr == '127.0.0.1' or request.remote_addr == 'localhost':
            return f(*args, **kwargs)
            
        # Check for correct chrome extension origin
        is_valid = False
        if origin.startswith('chrome-extension://'):
            extension_id = origin.split('//')[1]
            if extension_id in allowed_extension_ids or not allowed_extension_ids[0]:
                is_valid = True
                
        if not is_valid:
            error = "Invalid origin. Access denied."
            return jsonify(error=error), 403
            
        return f(*args, **kwargs)
    return decorated_function
