import pytest
import os
import json
import time
from datetime import datetime, timedelta
from unittest import mock
from app.main import create_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Mock environment variables
    with mock.patch.dict(os.environ, {
        'GOOGLE_CLIENT_SECRETS_FILE': 'dummy_path',
        'FRONTEND_URL': 'http://localhost:3000',
        'BROWSER_EXTENSION_ID': 'test_extension_id',
        'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id'
    }):
        # Create a test Flask app with testing config
        app = create_app('testing')
        
        # Configure app for testing
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False,
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id',
            'SESSION_TYPE': 'filesystem',
            'SECRET_KEY': 'test_secret_key'
        })
        
        yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_rate_limiting(app, client):
    """Test that rate limiting is working."""
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["3 per minute"],
        storage_uri="memory://",
    )
    
    # Define a test route with rate limiting
    @app.route('/test-rate-limit')
    @limiter.limit("1 per minute")
    def test_route():
        return 'OK'
    
    # First request should succeed
    response = client.get('/test-rate-limit')
    assert response.status_code == 200
    
    # Second request should be rate limited
    response = client.get('/test-rate-limit')
    assert response.status_code == 429  # Too Many Requests

def test_session_expiry(app, client):
    """Test session expiry functionality"""
    # Setup session with expiry
    with client.session_transaction() as sess:
        sess['user_info'] = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        # Set last activity to a time in the past (beyond expiry window)
        sess['last_activity'] = (datetime.now() - timedelta(hours=1)).isoformat()
    
    # Try to access protected endpoint
    response = client.get('/auth/user')
    
    # Session should be expired, response should indicate auth required
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Session expired' in data['error']