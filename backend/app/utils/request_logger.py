import logging
import json
from flask import request, g
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class RequestLogger:
    @staticmethod
    def log_request():
        """Log detailed information about the incoming request"""
        try:
            # Basic request info
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': getattr(g, 'request_id', 'no_id'),
                'method': request.method,
                'endpoint': request.endpoint,
                'url': request.url,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
            }

            # Authentication info
            if hasattr(g, 'user'):
                log_data['user'] = g.user
            
            # Request parameters
            if request.args:
                log_data['query_params'] = dict(request.args)
            
            # Request headers (excluding sensitive info)
            sensitive_headers = {'authorization', 'cookie', 'x-csrf-token'}
            headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in sensitive_headers}
            log_data['headers'] = headers
            
            # Request body (if JSON and not a file upload)
            if request.is_json:
                # Mask sensitive fields
                body = request.get_json()
                if isinstance(body, dict):
                    masked_body = RequestLogger.mask_sensitive_data(body)
                    log_data['body'] = masked_body
            
            # File upload info
            if request.files:
                files_info = {}
                for name, file in request.files.items():
                    files_info[name] = {
                        'filename': file.filename,
                        'content_type': file.content_type,
                        'content_length': request.content_length
                    }
                log_data['files'] = files_info
            
            logger.info(f"Incoming request: {json.dumps(log_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error in request logging: {str(e)}\n{traceback.format_exc()}")
    
    @staticmethod
    def log_response(response):
        """Log information about the response"""
        try:
            log_data = {
                'request_id': getattr(g, 'request_id', 'no_id'),
                'status_code': response.status_code,
                'content_type': response.content_type,
                'content_length': response.content_length,
            }
            
            # Add timing information if available
            if hasattr(g, 'start_time'):
                duration = datetime.utcnow().timestamp() - g.start_time
                log_data['duration'] = f"{duration:.3f}s"
            
            # Log response headers (excluding sensitive ones)
            sensitive_headers = {'set-cookie'}
            headers = {k: v for k, v in response.headers.items() 
                      if k.lower() not in sensitive_headers}
            log_data['headers'] = headers
            
            logger.info(f"Outgoing response: {json.dumps(log_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error in response logging: {str(e)}\n{traceback.format_exc()}")
    
    @staticmethod
    def log_error(error, status_code=500):
        """Log detailed error information"""
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': getattr(g, 'request_id', 'no_id'),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'status_code': status_code,
                'endpoint': request.endpoint,
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'traceback': traceback.format_exc()
            }
            
            logger.error(f"Error occurred: {json.dumps(log_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error in error logging: {str(e)}\n{traceback.format_exc()}")
    
    @staticmethod
    def mask_sensitive_data(data, sensitive_fields=None):
        """Mask sensitive information in the data"""
        if sensitive_fields is None:
            sensitive_fields = {
                'password', 'token', 'secret', 'key', 'auth',
                'credential', 'credit_card', 'card_number'
            }
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    masked_data[key] = '***MASKED***'
                elif isinstance(value, (dict, list)):
                    masked_data[key] = RequestLogger.mask_sensitive_data(value, sensitive_fields)
                else:
                    masked_data[key] = value
            return masked_data
        elif isinstance(data, list):
            return [RequestLogger.mask_sensitive_data(item, sensitive_fields) 
                   for item in data]
        return data
