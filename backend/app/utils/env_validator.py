import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EnvironmentError(Exception):
    """Exception raised for errors in the environment configuration."""
    pass

def validate_environment_variables():
    """
    Validate that all required environment variables are set and valid.
    Raises EnvironmentError if validation fails.
    """
    # Critical variables that must be set
    required_vars = [
        'SECRET_KEY',
        'GOOGLE_CLIENT_SECRETS_FILE',
        'FRONTEND_URL',
        'BROWSER_EXTENSION_ID',
        'ALLOWED_ORIGINS'
    ]
    
    # Check required variables
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    # Validate SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key and (len(secret_key) < 16 or secret_key == 'your-secret-key-here'):
        error_msg = "SECRET_KEY is too short or using default value. Please set a strong secret key."
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    # Validate GOOGLE_CLIENT_SECRETS_FILE
    client_secrets_path = os.environ.get('GOOGLE_CLIENT_SECRETS_FILE')
    if client_secrets_path and not Path(client_secrets_path).is_file():
        error_msg = f"GOOGLE_CLIENT_SECRETS_FILE does not exist at path: {client_secrets_path}"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    # Validate directories
    for dir_var in ['VIDEOS_DIR', 'SUMMARIES_DIR', 'LOGS_DIR']:
        dir_path = os.environ.get(dir_var)
        if dir_path:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory for {dir_var}: {dir_path}")
                except Exception as e:
                    error_msg = f"Failed to create directory for {dir_var}: {str(e)}"
                    logger.error(error_msg)
                    raise EnvironmentError(error_msg)
    
    # Validate FLASK_ENV
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env not in ['development', 'testing', 'production']:
        logger.warning(f"FLASK_ENV has invalid value: {flask_env}. Using 'development' instead.")
    
    # Validate rate limiting settings if present
    if os.environ.get('RATELIMIT_DEFAULT'):
        try:
            # Simple validation that it follows the format "X per Y" where X is a number
            rate_limit = os.environ.get('RATELIMIT_DEFAULT')
            parts = rate_limit.split(' per ')
            int(parts[0])  # Should be a number
        except (ValueError, IndexError):
            error_msg = f"RATELIMIT_DEFAULT has invalid format: {rate_limit}. Expected format: 'X per Y'"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)
    
    logger.info("Environment variables validated successfully")
    return True 