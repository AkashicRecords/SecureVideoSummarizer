from app import create_app
from flask import Flask, request
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
from app.config import config
from app.auth.routes import auth_bp

def create_app(config_name=None):
    """Application factory function"""
    # Load environment variables
    load_dotenv()
    
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
    # ... register other blueprints ...
    
    # Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG']) 