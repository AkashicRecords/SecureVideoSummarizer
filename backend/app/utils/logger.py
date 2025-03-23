import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Set up paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
logs_dir = os.path.join(project_root, 'logs')

# Ensure logs directory exists
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

def get_logger(name, log_file=None, level=logging.INFO):
    """
    Creates a logger configured to write to both a file and console.
    
    Args:
        name (str): Name of the logger, typically __name__
        log_file (str, optional): Filename for the log. If None, uses name_YYYY-MM-DD.log
        level (int, optional): Logging level. Defaults to logging.INFO.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if handlers haven't been added yet
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler
        if log_file is None:
            today = datetime.now().strftime('%Y-%m-%d')
            log_filename = f"{name.split('.')[-1]}_{today}.log"
            log_file = os.path.join(logs_dir, log_filename)
        
        # Set up rotating file handler (max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Predefined loggers for common components
def get_api_logger():
    """Get a logger for the API endpoints"""
    return get_logger('app.api')

def get_olympus_logger():
    """Get a logger for the Olympus integration"""
    return get_logger('app.olympus')

def get_youtube_logger():
    """Get a logger for the YouTube integration"""
    return get_logger('app.youtube')

def get_test_logger(test_name):
    """Get a logger for tests"""
    return get_logger(f'test.{test_name}') 