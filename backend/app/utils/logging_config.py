import os
import logging
from logging.handlers import RotatingFileHandler
from flask import request, has_request_context

class RequestFormatter(logging.Formatter):
    """
    Custom formatter that includes request information when available
    """
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.remote_addr = request.remote_addr
            record.user_agent = request.user_agent.string if request.user_agent else 'Unknown'
        else:
            record.url = 'No request context'
            record.method = 'No request context'
            record.remote_addr = 'No request context'
            record.user_agent = 'No request context'
        
        return super().format(record)

def setup_logging(app):
    """
    Configure logging for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up file handler for error logs
    error_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # Set up file handler for all logs
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s - %(method)s %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )
    error_file_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(error_file_handler)
    app.logger.addHandler(file_handler)
    
    # Set log level
    app.logger.setLevel(logging.INFO)
    
    # Log application startup
    app.logger.info('Application startup')
    
    return app 