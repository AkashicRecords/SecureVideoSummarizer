from flask import Flask
from app.utils.logging_config import setup_logging
from app.utils.error_handlers import register_error_handlers
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key'),
        VIDEOS_DIR=os.path.join(app.root_path, '..', os.environ.get('VIDEOS_DIR', 'videos')),
        SUMMARIES_DIR=os.path.join(app.root_path, '..', os.environ.get('SUMMARIES_DIR', 'summaries')),
        LOGS_DIR=os.path.join(app.root_path, '..', os.environ.get('LOGS_DIR', 'logs')),
    )
    
    # Ensure directories exist
    os.makedirs(app.config['VIDEOS_DIR'], exist_ok=True)
    os.makedirs(app.config['SUMMARIES_DIR'], exist_ok=True)
    os.makedirs(app.config['LOGS_DIR'], exist_ok=True)
    
    # Set up logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.auth.routes import auth
    from app.video.routes import video
    from app.summarizer.routes import summarizer
    
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(video, url_prefix='/video')
    app.register_blueprint(summarizer, url_prefix='/summarizer')
    
    return app 