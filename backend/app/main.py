from app import create_app
from flask import Flask, request, session, g, jsonify
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
from app.config import config
from app.auth.routes import auth_bp
from datetime import datetime, timedelta
from app.utils.env_validator import validate_environment_variables
from app.video.routes import video_bp
from app.utils.error_handlers import register_error_handlers
import argparse
import sys
import json
from app.api.routes import api_bp

def create_app(config_name=None):
    """Application factory function"""
    # Load environment variables
    load_dotenv()
    
    # Validate environment variables
    try:
        validate_environment_variables()
    except Exception as e:
        print(f"Environment validation error: {str(e)}")
        # In production, you might want to exit here
        # import sys; sys.exit(1)
    
    # Determine configuration to use
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    Session(app)
    
    # Initialize rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    
    # Apply specific rate limits to auth routes
    limiter.limit("10 per minute")(auth_bp)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(video_bp, url_prefix='/video')
    app.register_blueprint(api_bp, url_prefix='/api')
    # ... register other blueprints ...
    
    # Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Add session expiry middleware
    @app.before_request
    def check_session_expiry():
        """Check if the session has expired and clear it if necessary"""
        if 'user_info' in session:
            # Get the last activity time
            last_activity = session.get('last_activity')
            
            # If last_activity is not set or session has expired
            if not last_activity or datetime.utcnow() - datetime.fromisoformat(last_activity) > timedelta(minutes=30):
                session.clear()
                return jsonify({'error': 'Session expired, please login again'}), 401
            
            # Update last activity time
            session['last_activity'] = datetime.utcnow().isoformat()
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Secure Video Summarizer')
    parser.add_argument('--audio-file', help='Path to audio file for processing')
    parser.add_argument('--mode', choices=['web', 'summarize'], default='web', 
                        help='Application mode: web server or summarize audio')
    args = parser.parse_args()
    
    if args.mode == 'summarize' and args.audio_file:
        # Process the audio file directly
        from app.summarizer.processor import process_audio_file
        try:
            result = process_audio_file(args.audio_file)
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            sys.exit(1)
    else:
        # Start the web server
        app = create_app()
        app.run(debug=app.config['DEBUG']) 