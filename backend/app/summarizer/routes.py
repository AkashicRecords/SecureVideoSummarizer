from flask import Blueprint, request, jsonify, current_app
import os
import json
from datetime import datetime
from app.utils.helpers import generate_unique_id, get_video_path, create_summary_directory
from app.utils.error_handlers import APIError
from app.summarizer.processor import VideoSummarizer

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
        
        # Process the video and generate summary
        result = video_summarizer.process_video(video_path, options)
        
        # Create the summary object
        summary = {
            "summary_id": summary_id,
            "video_id": video_id,
            "created_at": datetime.now().isoformat(),
            "options": options,
            "transcript": result["transcript"],
            "content": result["summary"],
            "status": "completed"
        }
        
        # Save the summary to a file
        with open(os.path.join(summary_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f)
        
        current_app.logger.info(f"Summarization completed for video {video_id}, summary ID: {summary_id}")
        
        return jsonify({
            "message": "Summary created successfully",
            "summary_id": summary_id,
            "status": "completed"
        })
        
    except APIError as e:
        # APIError will be caught by the error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error during summarization: {str(e)}")
        raise APIError(f"Failed to summarize video: {str(e)}", 500)

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
                            "status": summary.get("status")
                        })
        
        return jsonify({"summaries": summaries})
        
    except Exception as e:
        current_app.logger.error(f"Error listing summaries: {str(e)}")
        raise APIError(f"Failed to list summaries: {str(e)}", 500) 