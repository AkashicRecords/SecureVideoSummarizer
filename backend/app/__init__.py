from flask import Flask
from app.utils.logging_config import setup_logging
from app.utils.error_handlers import register_error_handlers
import os
import sys
import traceback
import logging
from dotenv import load_dotenv
from flask_cors import CORS
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.api.admin_routes import admin_bp
from app.api.dashboard_routes import dashboard_bp
from oauthlib.oauth2 import WebApplicationClient

# Define version information
__version__ = "0.1.0"

# Set up root logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
session = Session()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name="production"):
    """
    Create and configure the Flask application.
    This is the single application factory for the entire application.
    
    Args:
        config_name (str): The name of the configuration to use (development, testing, production)
        
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize Flask extensions
    CORS(app, supports_credentials=True)
    session.init_app(app)
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Setup OAuth client for Google
    app.config["OAUTH2_CLIENT"] = WebApplicationClient(
        os.environ.get("GOOGLE_CLIENT_ID", "")
    )
    
    # Configure logging
    setup_logging(app)
    logger.info(f"Starting application with config: {config_name}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Ensure required directories exist
    directories = [
        app.config.get('VIDEOS_DIR', os.path.join(app.root_path, '..', 'videos')),
        app.config.get('SUMMARIES_DIR', os.path.join(app.root_path, '..', 'summaries')),
        app.config.get('LOGS_DIR', os.path.join(app.root_path, '..', 'logs')),
        app.config.get('TEMP_FOLDER', os.path.join(app.root_path, '..', 'uploads'))
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    
    # Register error handlers
    register_error_handlers(app)
    
    # Set up CORS
    origins = app.config.get('ALLOWED_ORIGINS', ['http://localhost:3000'])
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
    logger.debug(f"CORS configured with origins: {origins}")
    
    # Enable sessions
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    
    # Register all blueprints - handle imports carefully to catch errors
    blueprints = [
        # Core blueprints
        ('app.auth.routes', 'auth_bp', '/auth'),
        ('app.video.routes', 'video_bp', '/video'),
        ('app.summarizer.routes', 'summarizer', '/summarizer'),
        
        # API blueprints
        ('app.api.routes', 'api_bp', None),
        ('app.api.youtube_routes', 'youtube_bp', None),
        ('app.api.olympus_routes', 'olympus_bp', None),
        ('app.api.extension_routes', 'extension_bp', None),
        ('app.api.admin_routes', 'admin_bp', None),
        ('app.api.dashboard_routes', 'dashboard_bp', None)
    ]
    
    for module_path, blueprint_name, url_prefix in blueprints:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
            logger.info(f"Registered blueprint: {blueprint_name}")
        except ImportError as e:
            logger.error(f"Failed to import {module_path}.{blueprint_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error registering blueprint {blueprint_name}: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Create extension_routes.py if it doesn't exist
    extension_routes_path = os.path.join(os.path.dirname(__file__), 'api', 'extension_routes.py')
    if not os.path.exists(extension_routes_path):
        logger.info("Creating missing extension_routes.py file")
        create_extension_routes_file(extension_routes_path)
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Could not create database tables: {e}")
    
    logger.info(f"Application created successfully with config: {config_name}")
    return app

def create_extension_routes_file(file_path):
    """Create extension_routes.py file if it doesn't exist."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
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
            'api_url': current_app.config.get('API_URL', 'http://localhost:8080'),
            'ai_provider': 'ollama',
            'summary_length': 'medium',
            'transcript_enabled': True,
            'summary_enabled': True,
            'debug_mode': current_app.config.get('DEBUG', False)
        }
    })
'''
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(extension_routes_content)
    
    logger.info(f"Created extension_routes.py at {file_path}") 