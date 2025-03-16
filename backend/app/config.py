import os
from dotenv import load_dotenv
import secrets

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Generate a secure random key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    GOOGLE_CLIENT_SECRETS_FILE = os.environ.get('GOOGLE_CLIENT_SECRETS_FILE')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Session configuration
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', './flask_session')
    SESSION_PERMANENT = os.environ.get('SESSION_PERMANENT', 'False').lower() == 'true'
    SESSION_USE_SIGNER = os.environ.get('SESSION_USE_SIGNER', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400))  # 24 hours in seconds
    
    # Security headers
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Flask
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # Google OAuth
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    # Frontend and extension
    BROWSER_EXTENSION_ID = os.environ.get('BROWSER_EXTENSION_ID', 'dummy_extension_id')
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    
    # Ollama configuration
    OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'DeepSeek-R1')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '60'))
    OLLAMA_MAX_TOKENS = int(os.environ.get('OLLAMA_MAX_TOKENS', '2048'))
    OLLAMA_CONTEXT_SIZE = int(os.environ.get('OLLAMA_CONTEXT_SIZE', '8192'))
    
    # File paths
    VIDEOS_DIR = os.environ.get('VIDEOS_DIR', 'videos')
    SUMMARIES_DIR = os.environ.get('SUMMARIES_DIR', 'summaries')
    LOGS_DIR = os.environ.get('LOGS_DIR', 'logs')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # File upload settings
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'mp4,avi,mov,wmv,flv,mkv').split(','))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '100000000'))  # Default 100MB

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    OAUTHLIB_INSECURE_TRANSPORT = '1'  # Allow OAuth over HTTP for development
    # In development, we might want to disable some security features
    SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP in development

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    OAUTHLIB_INSECURE_TRANSPORT = '1'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the appropriate configuration based on environment."""
    config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
