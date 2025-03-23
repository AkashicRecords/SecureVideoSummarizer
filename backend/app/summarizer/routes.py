from flask import Blueprint, request, jsonify, current_app
import os
import json
import uuid
from datetime import datetime
from app.utils.helpers import generate_unique_id, get_video_path, create_summary_directory
from app.utils.error_handlers import APIError
from app.summarizer.processor import VideoSummarizer
from app.api.admin_routes import register_job, update_job_progress

summarizer = Blueprint('summarizer', __name__)
video_summarizer = VideoSummarizer()

@summarizer.route('/summarize/<video_id>', methods=['POST'])
def summarize_video(video_id):
    """
    Summarize a video based on its ID
    
    Expected JSON payload:
    {
        "options": {
            "format": "text|bullets|transcript",
            "length": "short|medium|long",
            "focus": ["key_points", "action", "dialogue"]
        }
    }
    """
    try:
        # Get summarization options from request
        data = request.get_json() or {}
        options = data.get('options', {
            'format': 'text',
            'length': 'medium',
            'focus': ['key_points']
        })
        
        # Validate options
        if options.get('format') not in ['text', 'bullets', 'transcript']:
            raise APIError("Invalid format option. Must be one of: text, bullets, transcript", 400)
            
        if options.get('length') not in ['short', 'medium', 'long']:
            raise APIError("Invalid length option. Must be one of: short, medium, long", 400)
        
        # Get video path
        video_path = get_video_path(video_id)
        if not os.path.exists(video_path):
            raise APIError("Video not found", 404)
            
        # Generate a unique ID for the summary
        summary_id = generate_unique_id()
        
        # Create a directory for the summary if it doesn't exist
        summary_dir = create_summary_directory(summary_id)
        
        # Log the summarization request
        current_app.logger.info(f"Starting summarization for video {video_id} with options: {options}")
        
        # Create a job ID for tracking
        job_id = f"summary_{uuid.uuid4().hex[:8]}"
        
        # Register the job for tracking in the dashboard
        register_job(job_id, 'summarization', video_id, {
            'summary_id': summary_id,
            'options': options,
            'video_path': video_path
        })
        
        # Start processing in background thread with progress updates
        result = process_video_with_progress(job_id, video_path, options, video_id, summary_id, summary_dir)
        
        return jsonify({
            "message": "Summary creation started",
            "summary_id": summary_id,
            "job_id": job_id,
            "status": "processing"
        })
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error during summarization: {str(e)}")
        raise APIError(f"Failed to summarize video: {str(e)}", 500)

def process_video_with_progress(job_id, video_path, options, video_id, summary_id, summary_dir):
    """Process video with progress updates to the dashboard"""
    import threading
    
    def process_thread():
        try:
            # Set initial progress
            update_job_progress(job_id, 5, "running")
            
            # Define a progress callback
            def progress_callback(stage, progress):
                # Map stages to progress percentages
                stage_weights = {
                    'extracting_audio': 20,
                    'transcribing': 50,
                    'summarizing': 30
                }
                
                # Calculate overall progress
                if stage == 'extracting_audio':
                    overall_progress = int(5 + (progress * stage_weights[stage] / 100))
                elif stage == 'transcribing':
                    overall_progress = int(25 + (progress * stage_weights[stage] / 100))
                elif stage == 'summarizing':
                    overall_progress = int(75 + (progress * stage_weights[stage] / 100))
                else:
                    # Unknown stage
                    overall_progress = progress
                
                # Update job progress
                update_job_progress(job_id, overall_progress)
                
            # Process the video and generate summary with progress updates
            result = video_summarizer.process_video(video_path, options, progress_callback)
            
            # Set progress to 95% while saving
            update_job_progress(job_id, 95, "saving")
            
            # Create the summary object
            summary = {
                "summary_id": summary_id,
                "video_id": video_id,
                "created_at": datetime.now().isoformat(),
                "options": options,
                "transcript": result["transcript"],
                "content": result["summary"],
                "job_id": job_id,
                "status": "completed"
            }
            
            # Save the summary to a file
            with open(os.path.join(summary_dir, 'summary.json'), 'w') as f:
                json.dump(summary, f)
            
            current_app.logger.info(f"Summarization completed for video {video_id}, summary ID: {summary_id}")
            
            # Set progress to 100% when done
            update_job_progress(job_id, 100, "completed")
            
        except Exception as e:
            current_app.logger.error(f"Error in summarization thread: {str(e)}")
            update_job_progress(job_id, 0, "failed")
    
    # Start processing in a background thread
    thread = threading.Thread(target=process_thread)
    thread.daemon = True
    thread.start()
    
    return {"status": "processing", "job_id": job_id}

@summarizer.route('/summary/<summary_id>', methods=['GET'])
def get_summary(summary_id):
    """Get a summary by its ID"""
    try:
        # In a real implementation, you would retrieve the summary from a database or file system
        summary_dir = os.path.join(current_app.config.get('SUMMARIES_DIR', 'summaries'), summary_id)
        summary_path = os.path.join(summary_dir, 'summary.json')
        
        if not os.path.exists(summary_path):
            raise APIError("Summary not found", 404)
            
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            
        return jsonify(summary)
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error retrieving summary: {str(e)}")
        raise APIError(f"Failed to retrieve summary: {str(e)}", 500)

@summarizer.route('/summaries', methods=['GET'])
def list_summaries():
    """List all summaries for the authenticated user"""
    # In a real implementation, you would filter summaries by user ID
    try:
        summaries = []
        summaries_dir = current_app.config.get('SUMMARIES_DIR', 'summaries')
        
        if os.path.exists(summaries_dir):
            for summary_id in os.listdir(summaries_dir):
                summary_path = os.path.join(summaries_dir, summary_id, 'summary.json')
                if os.path.exists(summary_path):
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)
                        summaries.append({
                            "summary_id": summary.get("summary_id"),
                            "video_id": summary.get("video_id"),
                            "created_at": summary.get("created_at"),
                            "job_id": summary.get("job_id"),
                            "status": summary.get("status")
                        })
        
        return jsonify({"summaries": summaries})
        
    except Exception as e:
        current_app.logger.error(f"Error listing summaries: {str(e)}")
        raise APIError(f"Failed to list summaries: {str(e)}", 500) 