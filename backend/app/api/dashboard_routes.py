from flask import Blueprint, render_template, send_from_directory, current_app
import os
import logging

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
logger = logging.getLogger(__name__)

@dashboard_bp.route('/', methods=['GET'])
def index():
    """Serve the main dashboard page"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/logs', methods=['GET'])
def logs():
    """Serve the logs view"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/files', methods=['GET'])
def files():
    """Serve the files view"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/jobs', methods=['GET'])
def jobs():
    """Serve the jobs view"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/extension', methods=['GET'])
def extension():
    """Serve the extension monitoring view"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/docs', methods=['GET'])
def docs():
    """Serve the documentation view"""
    return render_template('dashboard_index.html')

@dashboard_bp.route('/static/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'js'), filename)

@dashboard_bp.route('/static/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'css'), filename)

@dashboard_bp.route('/static/media/<path:filename>')
def serve_media(filename):
    """Serve media files"""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'media'), filename) 