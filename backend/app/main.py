from app import create_app
from flask import Flask, request, session, g, jsonify, redirect, url_for
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sys
import traceback
from dotenv import load_dotenv
from app.config import config, get_config
from app.auth.routes import auth_bp
from datetime import datetime, timedelta
from app.utils.env_validator import validate_environment_variables
from app.utils.error_handlers import register_error_handlers
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler

# Set up root logger
logger = logging.getLogger(__name__)

def configure_logging(app):
    """Configure application logging."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create rotating file handler for app.log
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Set log level for handlers
    file_handler.setLevel(getattr(logging, log_level))
    console_handler.setLevel(getattr(logging, log_level))
    
    # Add handlers to app logger and root logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Set log level for app logger
    app.logger.setLevel(getattr(logging, log_level))
    
    # Also configure the root logger for import errors
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, log_level))
    
    logger.info("Logging configured successfully")

def create_app(config_name="production"):
    """Create and configure the Flask application."""
    try:
        app = Flask(__name__)
        
        # Load configuration based on environment
        app.config.from_object(config[config_name])
        
        # Configure logging
        configure_logging(app)
        
        # Log important configuration details
        logger.info(f"Starting application with config: {config_name}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Import dependent modules - handle each one separately to catch specific import errors
        try:
            from app.api.routes import api_bp
            from app.api.youtube_routes import youtube_bp
            from app.api.olympus_routes import olympus_bp
            from app.api.admin_routes import admin_bp
            from app.api.dashboard_routes import dashboard_bp
            try:
                from app.api.extension_routes import extension_bp
            except ImportError as e:
                logger.error(f"Failed to import extension_routes: {str(e)}")
                # Create the extension_routes.py file if missing
                create_extension_routes()
                from app.api.extension_routes import extension_bp
                
            from app.video.routes import video_bp
            from flask_cors import CORS
            
        except ImportError as e:
            logger.error(f"Import error during app initialization: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        # Set up CORS
        origins = app.config.get('ALLOWED_ORIGINS', ['http://localhost:8080'])
        # Allow any extension ID since we validate it in the request handlers
        extension_id = app.config.get('BROWSER_EXTENSION_ID', '')
        if extension_id:
            origins.append(f"chrome-extension://{extension_id}")
            
        # Register extension origins from settings to allow multiple extensions
        for ext_id in app.config.get('ALLOWED_EXTENSION_IDS', []):
            if ext_id and ext_id not in origins:
                origins.append(f"chrome-extension://{ext_id}")
        
        CORS(app, 
             resources={r"/api/*": {"origins": origins}},
             supports_credentials=True,
             allow_headers=["Content-Type", "X-Extension-ID", "Authorization"])
        
        # Enable sessions
        app.config["SESSION_PERMANENT"] = False
        app.config["SESSION_TYPE"] = "filesystem"
        Session(app)
        
        # Register blueprints
        app.register_blueprint(api_bp)
        app.register_blueprint(youtube_bp)
        app.register_blueprint(olympus_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(extension_bp)
        app.register_blueprint(admin_bp)  # Register the admin API routes
        app.register_blueprint(dashboard_bp)  # Register the dashboard routes
        try:
            app.register_blueprint(video_bp)
        except Exception as e:
            logger.warning(f"Could not register video blueprint: {str(e)}")
        
        logger.info(f"Application created with config: {config_name}")
        return app
        
    except Exception as e:
        logger.critical(f"Error creating application: {str(e)}")
        logger.critical(traceback.format_exc())
        raise

def create_extension_routes():
    """Create extension_routes.py file if it doesn't exist."""
    extension_routes_path = os.path.join(os.getcwd(), 'app', 'api', 'extension_routes.py')
    if os.path.exists(extension_routes_path):
        return
        
    logger.info("Creating missing extension_routes.py file")
    
    extension_routes_content = '''from flask import Blueprint, jsonify, request, current_app
import logging
from app.utils.validators import validate_extension_origin

extension_bp = Blueprint('extension', __name__, url_prefix='/api/extension')
logger = logging.getLogger(__name__)

@extension_bp.route('/ping', methods=['GET'])
@validate_extension_origin
def ping():
    """Simple ping endpoint to check if backend is running"""
    logger.debug("Extension ping received")
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running',
        'version': '1.0.0',
        'using_ai': 'ollama'
    })

@extension_bp.route('/status', methods=['GET'])
@validate_extension_origin
def status():
    """Get the status of the extension integration"""
    logger.debug("Extension status check")
    return jsonify({
        'status': 'ready',
        'extension_id': current_app.config.get('EXTENSION_ID', 'Unknown'),
        'supported_features': [
            'transcript_generation',
            'summary_generation', 
            'offline_processing'
        ]
    })

@extension_bp.route('/config', methods=['GET'])
@validate_extension_origin
def get_config():
    """Get the extension configuration"""
    logger.debug("Extension config requested")
    return jsonify({
        'config': {
            'api_url': current_app.config.get('API_URL', 'http://localhost:8081'),
            'ai_provider': 'ollama',
            'summary_length': 'medium',
            'transcript_enabled': True,
            'summary_enabled': True,
            'debug_mode': current_app.config.get('DEBUG', False)
        }
    })'''
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(extension_routes_path), exist_ok=True)
    
    # Write the file
    with open(extension_routes_path, 'w') as f:
        f.write(extension_routes_content)
    
    logger.info(f"Created extension_routes.py at {extension_routes_path}")

def run_app():
    """
    Entry point for running the application when installed as a package.
    This function is called by the console script entry point.
    """
    # Set up basic logging before app is created
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    
    parser = argparse.ArgumentParser(description='Secure Video Summarizer')
    parser.add_argument('--port', type=int, default=8081, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--config', type=str, default='production', choices=['development', 'testing', 'production'],
                        help='Configuration to use')
    parser.add_argument('--check-imports', action='store_true', help='Verify all imports and exit')
    
    args = parser.parse_args()
    
    if args.check_imports:
        check_all_imports()
        return
    
    try:
        app = create_app(args.config)
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

def check_all_imports():
    """Test all imports and report any issues."""
    logger.info("Checking all imports...")
    
    def check_import(module_name):
        try:
            __import__(module_name)
            logger.info(f"✓ Successfully imported {module_name}")
            return True
        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {str(e)}")
            return False
    
    # Core Flask dependencies
    dependencies = [
        "flask", "flask_cors", "flask_session", "flask_limiter",
        # Audio processing
        "pydub", "speech_recognition", 
        # File handling
        "magic", "python_magic",
        # Google integration
        "google.auth", "google_auth_oauthlib", "googleapiclient", 
        # AI models
        "elevenlabs"
    ]
    
    success = True
    for dep in dependencies:
        if not check_import(dep):
            success = False
    
    if success:
        logger.info("All imports successful!")
    else:
        logger.error("Some imports failed! Please install missing dependencies.")
        sys.exit(1)

if __name__ == "__main__":
    run_app() 