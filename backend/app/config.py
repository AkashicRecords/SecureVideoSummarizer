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