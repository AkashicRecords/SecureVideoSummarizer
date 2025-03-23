from flask import Blueprint, jsonify, request, current_app
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