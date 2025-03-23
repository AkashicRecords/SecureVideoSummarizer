from flask import Blueprint, jsonify, request, current_app, send_from_directory
import os
import logging
import glob
import json
import datetime
from pathlib import Path
import psutil
import threading

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

# In-memory storage for active jobs and their progress
# Format: { job_id: { 'id': str, 'type': str, 'status': str, 'progress': int, 'started': str, 'video_id': str, ... } }
active_jobs = {}
completed_jobs = []  # Store recently completed jobs in memory

def register_job(job_id, job_type, video_id, metadata=None):
    """Register a new job for tracking"""
    job = {
        'id': job_id,
        'type': job_type,
        'status': 'running',
        'progress': 0,
        'started': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'video_id': video_id,
        'metadata': metadata or {}
    }
    active_jobs[job_id] = job
    logger.info(f"Registered new job: {job_id} ({job_type}) for video {video_id}")
    return job

def update_job_progress(job_id, progress, status=None):
    """Update the progress of a job (0-100)"""
    if job_id in active_jobs:
        active_jobs[job_id]['progress'] = min(max(0, progress), 100)
        if status:
            active_jobs[job_id]['status'] = status
        
        # If job is complete, move to completed jobs list
        if progress >= 100 or status in ['completed', 'failed']:
            complete_job(job_id, status or 'completed')
            
        logger.debug(f"Updated job {job_id}: progress={progress}, status={status or active_jobs[job_id]['status']}")
        return True
    return False

def complete_job(job_id, status='completed'):
    """Mark a job as completed and move it to completed jobs list"""
    if job_id in active_jobs:
        job = active_jobs[job_id]
        job['status'] = status
        job['progress'] = 100 if status == 'completed' else job['progress']
        job['completed'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate duration
        started = datetime.datetime.strptime(job['started'], '%Y-%m-%d %H:%M:%S')
        completed = datetime.datetime.strptime(job['completed'], '%Y-%m-%d %H:%M:%S')
        duration = completed - started
        job['duration'] = str(duration).split('.')[0]  # Remove microseconds
        
        # Move to completed jobs
        completed_jobs.insert(0, job)  # Add to front of list
        while len(completed_jobs) > 20:  # Keep only 20 most recent
            completed_jobs.pop()
            
        # Remove from active jobs
        del active_jobs[job_id]
        logger.info(f"Completed job {job_id} with status {status}")
        return True
    return False

@admin_bp.route('/status', methods=['GET'])
def get_status():
    """Get the overall system status"""
    try:
        # Get server uptime
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        
        # Count total processed videos
        video_count = len(glob.glob(os.path.join(current_app.config['UPLOAD_FOLDER'], '*.mp4')))
        
        # Count total summaries
        summary_count = len(glob.glob(os.path.join(current_app.config['SUMMARIES_FOLDER'], '*.json')))
        
        # Get disk usage
        disk_usage = psutil.disk_usage('/')
        disk_free_gb = round(disk_usage.free / (1024 * 1024 * 1024), 2)
        disk_used_percent = disk_usage.percent
        
        # Get memory usage
        memory_usage = psutil.virtual_memory()
        memory_used_percent = memory_usage.percent
        
        # Estimating error rate (placeholder - would need actual error tracking)
        error_rate = 0  # Placeholder
        
        # Count active jobs
        active_job_count = len(active_jobs)
        
        return jsonify({
            'status': 'online',
            'uptime': str(uptime).split('.')[0],  # Remove microseconds
            'metrics': {
                'video_count': video_count,
                'summary_count': summary_count,
                'error_rate': error_rate,
                'active_jobs': active_job_count,
                'disk_free_gb': disk_free_gb,
                'disk_used_percent': disk_used_percent,
                'memory_used_percent': memory_used_percent
            },
            'last_checked': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get system status: {str(e)}"
        }), 500

@admin_bp.route('/logs', methods=['GET'])
def get_logs():
    """Get the most recent logs"""
    try:
        # Parameters
        log_file = request.args.get('file', 'app.log')
        level = request.args.get('level', 'ALL')
        limit = int(request.args.get('limit', 100))
        
        # Validate log file (security check to prevent path traversal)
        if '..' in log_file or log_file.startswith('/'):
            return jsonify({
                'status': 'error',
                'message': 'Invalid log file specified'
            }), 400
        
        # Get path to log file
        log_path = os.path.join(current_app.config.get('LOG_FOLDER', 'logs'), log_file)
        
        if not os.path.exists(log_path):
            return jsonify({
                'status': 'error',
                'message': f'Log file {log_file} not found'
            }), 404
        
        # Read the log file
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Process and parse log entries
        logs = []
        for line in lines[-limit:]:  # Get the last 'limit' lines
            # Parse log line - adjust this based on your log format
            try:
                parts = line.split(' - ')
                if len(parts) >= 3:
                    timestamp = parts[0]
                    level_part = parts[2].split(' ')[0]
                    message = ' '.join(parts[2:])
                    
                    # Filter by level if specified
                    if level != 'ALL' and level != level_part:
                        continue
                    
                    logs.append({
                        'timestamp': timestamp,
                        'level': level_part,
                        'message': message.strip()
                    })
            except Exception as e:
                logger.warning(f"Could not parse log line: {line}. Error: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'log_file': log_file,
            'total_lines': len(lines),
            'returned_lines': len(logs),
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get logs: {str(e)}"
        }), 500

@admin_bp.route('/files', methods=['GET'])
def get_files():
    """Get information about files and directories"""
    try:
        # Key directories to track
        directories = [
            {'name': 'videos', 'path': current_app.config.get('UPLOAD_FOLDER', 'videos')},
            {'name': 'summaries', 'path': current_app.config.get('SUMMARIES_FOLDER', 'summaries')},
            {'name': 'logs', 'path': current_app.config.get('LOG_FOLDER', 'logs')},
            {'name': 'sessions', 'path': current_app.config.get('SESSION_FILE_DIR', 'flask_session')}
        ]
        
        result = []
        for directory in directories:
            try:
                path = directory['path']
                if not os.path.exists(path):
                    directory_info = {
                        'name': directory['name'],
                        'path': path,
                        'exists': False,
                        'file_count': 0,
                        'size_bytes': 0,
                        'size_human': '0 B',
                        'files': []
                    }
                else:
                    # Get all files in the directory
                    files = []
                    total_size = 0
                    
                    for file_path in glob.glob(os.path.join(path, '*')):
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            
                            # Get file info
                            file_info = {
                                'name': os.path.basename(file_path),
                                'path': file_path,
                                'size_bytes': file_size,
                                'size_human': _human_readable_size(file_size),
                                'modified': datetime.datetime.fromtimestamp(
                                    os.path.getmtime(file_path)
                                ).strftime('%Y-%m-%d %H:%M:%S')
                            }
                            files.append(file_info)
                    
                    # Sort files by modified date (newest first)
                    files.sort(key=lambda x: x['modified'], reverse=True)
                    
                    directory_info = {
                        'name': directory['name'],
                        'path': path,
                        'exists': True,
                        'file_count': len(files),
                        'size_bytes': total_size,
                        'size_human': _human_readable_size(total_size),
                        'files': files[:10]  # Return only the 10 most recent files
                    }
                
                result.append(directory_info)
            except Exception as e:
                logger.error(f"Error processing directory {directory['name']}: {str(e)}")
                
        return jsonify({
            'status': 'success',
            'directories': result
        })
    except Exception as e:
        logger.error(f"Error getting file information: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get file information: {str(e)}"
        }), 500

@admin_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Get information about active and recently completed jobs"""
    try:
        # Convert active jobs to list and sort by start time (most recent first)
        active_jobs_list = list(active_jobs.values())
        active_jobs_list.sort(key=lambda job: job['started'], reverse=True)
        
        # Combine with recent completed jobs
        all_jobs = active_jobs_list + completed_jobs
        
        return jsonify({
            'status': 'success',
            'active_count': len(active_jobs_list),
            'completed_count': len(completed_jobs),
            'jobs': all_jobs
        })
    except Exception as e:
        logger.error(f"Error getting job information: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get job information: {str(e)}"
        }), 500

@admin_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get detailed information about a specific job"""
    try:
        # Check active jobs first
        if job_id in active_jobs:
            return jsonify({
                'status': 'success',
                'job': active_jobs[job_id]
            })
        
        # Check completed jobs
        for job in completed_jobs:
            if job['id'] == job_id:
                return jsonify({
                    'status': 'success',
                    'job': job
                })
        
        # Job not found
        return jsonify({
            'status': 'error',
            'message': f'Job {job_id} not found'
        }), 404
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get job information: {str(e)}"
        }), 500

@admin_bp.route('/jobs/<job_id>/progress', methods=['POST'])
def update_job(job_id):
    """Update the progress of a job"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        progress = data.get('progress')
        status = data.get('status')
        
        if progress is None:
            return jsonify({
                'status': 'error',
                'message': 'Progress value is required'
            }), 400
        
        if update_job_progress(job_id, progress, status):
            return jsonify({
                'status': 'success',
                'message': f'Job {job_id} updated'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to update job: {str(e)}"
        }), 500

@admin_bp.route('/jobs', methods=['POST'])
def create_job():
    """Create a new job for tracking"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        job_id = data.get('id')
        job_type = data.get('type')
        video_id = data.get('video_id')
        metadata = data.get('metadata')
        
        if not job_id or not job_type or not video_id:
            return jsonify({
                'status': 'error',
                'message': 'id, type, and video_id are required'
            }), 400
        
        job = register_job(job_id, job_type, video_id, metadata)
        return jsonify({
            'status': 'success',
            'message': f'Job {job_id} created',
            'job': job
        })
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to create job: {str(e)}"
        }), 500

@admin_bp.route('/extension/logs', methods=['GET', 'POST'])
def handle_extension_logs():
    """Handle extension logs - both retrieving and submitting"""
    try:
        if request.method == 'POST':
            # Handle submission of logs from extension
            data = request.json
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            # Save the extension logs
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"extension_logs_{timestamp}.json"
            
            logs_dir = os.path.join(current_app.config.get('LOG_FOLDER', 'logs'), 'extension')
            os.makedirs(logs_dir, exist_ok=True)
            
            with open(os.path.join(logs_dir, filename), 'w') as f:
                json.dump(data, f, indent=2)
            
            return jsonify({
                'status': 'success',
                'message': 'Extension logs saved',
                'filename': filename
            })
        else:
            # Get saved extension logs
            logs_dir = os.path.join(current_app.config.get('LOG_FOLDER', 'logs'), 'extension')
            os.makedirs(logs_dir, exist_ok=True)
            
            log_files = glob.glob(os.path.join(logs_dir, 'extension_logs_*.json'))
            log_files.sort(reverse=True)  # Most recent first
            
            logs = []
            for log_file in log_files[:10]:  # Get only 10 most recent logs
                try:
                    with open(log_file, 'r') as f:
                        log_data = json.load(f)
                        logs.append({
                            'timestamp': log_data.get('timestamp', 'Unknown'),
                            'browser': log_data.get('browser', 'Unknown'),
                            'url': log_data.get('url', 'Unknown'),
                            'content': log_data.get('content', {})
                        })
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {str(e)}")
            
            return jsonify({
                'status': 'success',
                'logs': logs
            })
    except Exception as e:
        logger.error(f"Error handling extension logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to handle extension logs: {str(e)}"
        }), 500

@admin_bp.route('/content-script', methods=['POST'])
def submit_content_script_state():
    """Endpoint for content script to submit its state/logs"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Save the content script state
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"content_script_state_{timestamp}.json"
        
        report_dir = os.path.join(current_app.config.get('LOG_FOLDER', 'logs'), 'content_script')
        os.makedirs(report_dir, exist_ok=True)
        
        with open(os.path.join(report_dir, filename), 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Content script state saved',
            'filename': filename
        })
    except Exception as e:
        logger.error(f"Error saving content script state: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to save content script state: {str(e)}"
        }), 500

def _human_readable_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

# Clean up completed jobs on server shutdown
def cleanup_jobs():
    """Clean up completed jobs when application shuts down"""
    completed_jobs.clear()
    logger.info("Cleaned up completed jobs on shutdown") 