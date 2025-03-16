from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app, g
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
import secrets
from functools import wraps
import logging
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint('auth', __name__)

# Setup logging
logger = logging.getLogger(__name__)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def get_client_secrets_file():
    """Get the path to the client secrets file from environment variables"""
    client_secrets_path = os.environ.get('GOOGLE_CLIENT_SECRETS_FILE')
    if not client_secrets_path or not os.path.exists(client_secrets_path):
        logger.error("Google client secrets file not found")
        raise FileNotFoundError("Google client secrets file not found")
    return client_secrets_path

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For development/testing, allow requests without authentication
        if os.environ.get('FLASK_ENV') == 'development' and os.environ.get('BYPASS_AUTH_FOR_TESTING') == 'true':
            return f(*args, **kwargs)
            
        if 'user_info' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            else:
                return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET'])
@limiter.limit("5 per minute")
def login():
    """Initiate the Google OAuth2 login flow"""
    try:
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        if hasattr(g, 'request_id'):
            request_id = g.request_id
            logger.info(f"Request {request_id} | Login attempt | IP: {client_ip} | User-Agent: {user_agent}")
        else:
            logger.info(f"Login attempt | IP: {client_ip} | User-Agent: {user_agent}")
        
        # Generate a secure state token to prevent CSRF
        state = secrets.token_hex(16)
        session['oauth_state'] = state
        
        # Create the flow instance
        flow = Flow.from_client_secrets_file(
            get_client_secrets_file(),
            scopes=[
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ],
            redirect_uri=url_for('auth.callback', _external=True)
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Enable refresh tokens
            include_granted_scopes='true',  # Include any previously granted scopes
            state=state,  # Pass the state token
            prompt='consent'  # Force the consent screen to appear
        )
        
        logger.info(f"Redirecting to Google OAuth | State: {state[:5]}... | Redirect URI: {flow.redirect_uri}")
        return redirect(authorization_url)
    
    except Exception as e:
        if hasattr(g, 'request_id'):
            logger.error(f"Request {g.request_id} | Login error: {str(e)}", exc_info=True)
        else:
            logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500

@auth_bp.route('/callback', methods=['GET'])
@limiter.limit("5 per minute")
def callback():
    """Handle the OAuth2 callback from Google"""
    try:
        client_ip = request.remote_addr
        
        if hasattr(g, 'request_id'):
            request_id = g.request_id
            logger.info(f"Request {request_id} | OAuth callback | IP: {client_ip}")
        else:
            logger.info(f"OAuth callback | IP: {client_ip}")
        
        # Verify state parameter to prevent CSRF
        state = request.args.get('state', '')
        stored_state = session.pop('oauth_state', None)
        
        if not state or state != stored_state:
            logger.warning(f"Invalid state parameter in OAuth callback | Received: {state[:5]}... | Expected: {stored_state[:5] if stored_state else 'None'}...")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Create the flow instance
        flow = Flow.from_client_secrets_file(
            get_client_secrets_file(),
            scopes=[
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ],
            redirect_uri=url_for('auth.callback', _external=True)
        )
        
        # Exchange authorization code for access token
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        # Get user info
        user_info = get_user_info(credentials)
        
        # Store user info in session
        session['user_info'] = user_info
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': datetime.utcnow() + timedelta(hours=1)  # Store expiration time
        }
        
        # Set the initial last_activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        
        logger.info(f"User authenticated successfully | Email: {user_info.get('email')} | Name: {user_info.get('name')}")
        
        # Redirect to frontend with success
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/auth-success")
    
    except Exception as e:
        if hasattr(g, 'request_id'):
            logger.error(f"Request {g.request_id} | Callback error: {str(e)}", exc_info=True)
        else:
            logger.error(f"Callback error: {str(e)}", exc_info=True)
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/auth-error?error={str(e)}")

def get_user_info(credentials):
    """Get user information from Google API"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        # Log user info (with partial redaction for privacy)
        email = user_info.get('email', '')
        name = user_info.get('name', '')
        
        # Redact email for privacy in logs
        if email:
            parts = email.split('@')
            if len(parts) == 2:
                redacted_email = f"{parts[0][:3]}{'*' * (len(parts[0])-3)}@{parts[1]}"
            else:
                redacted_email = f"{email[:3]}{'*' * (len(email)-3)}"
        else:
            redacted_email = 'None'
            
        logger.info(f"Retrieved user info | Email: {redacted_email} | Name: {name}")
        
        return {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'email_verified': user_info.get('verified_email', False)
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}", exc_info=True)
        raise

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the user by clearing the session"""
    if 'user_info' in session:
        user_email = session.get('user_info', {}).get('email', 'Unknown')
        
        if hasattr(g, 'request_id'):
            logger.info(f"Request {g.request_id} | User logout | Email: {user_email}")
        else:
            logger.info(f"User logout | Email: {user_email}")
    
    session.clear()
    return jsonify({'message': 'Successfully logged out'})

@auth_bp.route('/user', methods=['GET'])
@login_required
def get_current_user():
    """Get the current logged-in user's information"""
    user_info = session.get('user_info', {})
    user_email = user_info.get('email', 'Unknown')
    
    if hasattr(g, 'request_id'):
        logger.info(f"Request {g.request_id} | Get current user | Email: {user_email}")
    else:
        logger.info(f"Get current user | Email: {user_email}")
        
    return jsonify(user_info)

@auth_bp.route('/refresh-token', methods=['POST'])
@limiter.limit("10 per minute")
def refresh_token():
    """Refresh the access token using the refresh token"""
    if 'credentials' not in session:
        if hasattr(g, 'request_id'):
            logger.warning(f"Request {g.request_id} | Token refresh failed | No credentials found")
        else:
            logger.warning(f"Token refresh failed | No credentials found")
            
        return jsonify({'error': 'No credentials found'}), 401
    
    try:
        creds_data = session['credentials']
        user_email = session.get('user_info', {}).get('email', 'Unknown')
        
        if hasattr(g, 'request_id'):
            logger.info(f"Request {g.request_id} | Token refresh attempt | User: {user_email}")
        else:
            logger.info(f"Token refresh attempt | User: {user_email}")
        
        # Check if we have a refresh token
        if not creds_data.get('refresh_token'):
            logger.warning(f"No refresh token available for user: {user_email}")
            session.clear()
            return jsonify({'error': 'No refresh token available, please login again'}), 401
        
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )
        
        # Check if credentials are expired and refresh if needed
        if credentials.expired:
            try:
                logger.info(f"Refreshing expired token for user: {user_email}")
                credentials.refresh(Request())
            except Exception as e:
                logger.error(f"Token refresh failed for user {user_email}: {str(e)}", exc_info=True)
                session.clear()
                return jsonify({'error': 'Token refresh failed, please login again'}), 401
            
            # Update session with new credentials
            session['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': datetime.utcnow() + timedelta(hours=1)  # Store expiration time
            }
            
            logger.info(f"Token refreshed successfully for user: {user_email}")
        else:
            logger.info(f"Token still valid for user: {user_email}")
        
        return jsonify({
            'access_token': credentials.token,
            'expires_in': 3600  # Typical expiration time in seconds
        })
    
    except Exception as e:
        user_email = session.get('user_info', {}).get('email', 'Unknown')
        
        if hasattr(g, 'request_id'):
            logger.error(f"Request {g.request_id} | Token refresh error for user {user_email}: {str(e)}", exc_info=True)
        else:
            logger.error(f"Token refresh error for user {user_email}: {str(e)}", exc_info=True)
            
        session.clear()  # Clear invalid session
        return jsonify({'error': 'Failed to refresh token', 'details': str(e)}), 401 