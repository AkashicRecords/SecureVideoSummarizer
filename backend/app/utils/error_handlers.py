from flask import jsonify, current_app, request, g
import traceback
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception class for API errors"""
    def __init__(self, message, status_code=400, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert the error to a dictionary for JSON response"""
        error_dict = {
            'error': self.message,
            'status_code': self.status_code
        }
        if self.details:
            error_dict['details'] = self.details
        return error_dict

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        # Get request information for logging
        client_ip = request.remote_addr
        endpoint = request.endpoint
        method = request.method
        
        # Log with request ID if available
        if hasattr(g, 'request_id'):
            logger.error(
                f"Request {g.request_id} | API Error | IP: {client_ip} | "
                f"Method: {method} | Endpoint: {endpoint} | "
                f"Status: {error.status_code} | Error: {error.message}"
            )
        else:
            logger.error(
                f"API Error | IP: {client_ip} | Method: {method} | "
                f"Endpoint: {endpoint} | Status: {error.status_code} | "
                f"Error: {error.message}"
            )
        
        # Create response
        response = jsonify(error.to_dict() if hasattr(error, 'to_dict') else {
            'error': error.message,
            'status_code': error.status_code
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def bad_request(error):
        # Get request information for logging
        client_ip = request.remote_addr
        endpoint = request.endpoint
        method = request.method
        
        # Log with request ID if available
        if hasattr(g, 'request_id'):
            logger.error(
                f"Request {g.request_id} | Bad Request | IP: {client_ip} | "
                f"Method: {method} | Endpoint: {endpoint} | Error: {str(error)}"
            )
        else:
            logger.error(
                f"Bad Request | IP: {client_ip} | Method: {method} | "
                f"Endpoint: {endpoint} | Error: {str(error)}"
            )
        
        return jsonify({
            'error': 'Bad request',
            'status_code': 400
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        # Get request information for logging
        client_ip = request.remote_addr
        path = request.path
        method = request.method
        
        # Log with request ID if available
        if hasattr(g, 'request_id'):
            logger.warning(
                f"Request {g.request_id} | Not Found | IP: {client_ip} | "
                f"Method: {method} | Path: {path}"
            )
        else:
            logger.warning(
                f"Not Found | IP: {client_ip} | Method: {method} | Path: {path}"
            )
        
        return jsonify({
            'error': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        # Get request information for logging
        client_ip = request.remote_addr
        path = request.path
        method = request.method
        
        # Log with request ID if available
        if hasattr(g, 'request_id'):
            logger.warning(
                f"Request {g.request_id} | Method Not Allowed | IP: {client_ip} | "
                f"Method: {method} | Path: {path}"
            )
        else:
            logger.warning(
                f"Method Not Allowed | IP: {client_ip} | Method: {method} | Path: {path}"
            )
        
        return jsonify({
            'error': 'Method not allowed',
            'status_code': 405
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        # Get request information for logging
        client_ip = request.remote_addr
        endpoint = request.endpoint
        method = request.method
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Log with request ID if available
        if hasattr(g, 'request_id'):
            logger.error(
                f"Request {g.request_id} | Internal Server Error | IP: {client_ip} | "
                f"Method: {method} | Endpoint: {endpoint} | Error: {str(error)}\n"
                f"Stack trace: {stack_trace}"
            )
        else:
            logger.error(
                f"Internal Server Error | IP: {client_ip} | Method: {method} | "
                f"Endpoint: {endpoint} | Error: {str(error)}\n"
                f"Stack trace: {stack_trace}"
            )
        
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500
        }), 500
    
    return app 