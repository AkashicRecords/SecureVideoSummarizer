import os
from dotenv import load_dotenv
import secrets
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Generate a secure random key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    GOOGLE_CLIENT_SECRETS_FILE = os.environ.get('GOOGLE_CLIENT_SECRETS_FILE')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:8080')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', './flask_session')
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = os.environ.get('SESSION_USE_SIGNER', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security headers
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Flask
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # Google OAuth
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/callback')
    
    # Frontend and extension
    BROWSER_EXTENSION_ID = os.environ.get('BROWSER_EXTENSION_ID', 'dummy_extension_id')
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:8080,chrome-extension://*').split(',')
    
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
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    
    # File upload settings
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'mp3', 'wav', 'm4a'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max upload

    # Authentication settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:8081/api/auth/callback')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8080,http://localhost:5173').split(',')

    # Ollama configuration
    SUMMARIZER_MODEL = os.environ.get('SUMMARIZER_MODEL', 'openai/whisper-small')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    OAUTHLIB_INSECURE_TRANSPORT = '1'  # Allow OAuth over HTTP for development
    # In development, we might want to disable some security features
    SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP in development
    CORS_ORIGINS = ['http://localhost:8080', 'http://localhost:5173', 'http://127.0.0.1:5173']

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    OAUTHLIB_INSECURE_TRANSPORT = '1'
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CORS_ORIGINS = ['http://localhost:8080', 'http://localhost:5173']

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    
    # Security headers
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://yourdomain.com').split(',')

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
