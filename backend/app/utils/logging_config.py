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
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.path = request.path
            record.user_agent = request.user_agent.string
            # Add user info if available
            if hasattr(request, 'user_info'):
                record.user = request.user_info.get('email', 'anonymous')
            else:
                record.user = 'anonymous'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.path = None
            record.user_agent = None
            record.user = None
        
        return super().format(record)

def setup_logging(app):
    """
    Configure logging for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = app.config.get('LOGS_DIR', os.path.join(app.root_path, '..', 'logs'))
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
    file_handler.setLevel(logging.DEBUG)
    
    # Set up console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s - %(user)s - %(method)s %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )
    error_file_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(error_file_handler)
    root_logger.addHandler(file_handler)
    
    root_logger.addHandler(console_handler)
    
    # Disable default Flask logger
    app.logger.handlers = []
    
    # Add handlers to app logger
    app.logger.addHandler(error_file_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Set log level
    app.logger.setLevel(logging.DEBUG)
    
    # Set specific loggers to DEBUG level
    logging.getLogger('app.api.routes').setLevel(logging.DEBUG)
    
    # Log application startup
    app.logger.info('Application startup with DEBUG logging enabled')
    
    return app 