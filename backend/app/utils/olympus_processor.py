"""
Utility functions for processing Olympus Learning Platform videos
"""
import logging
import os
import tempfile
import time
from urllib.parse import urlparse, parse_qs

from app.utils.audio_processor import process_audio_file
from app.summarizer.processor import summarize_text_enhanced
from app.config import Config

logger = logging.getLogger(__name__)

def is_olympus_url(url):
    """Check if the URL is from Olympus Learning Platform"""
    parsed_url = urlparse(url)
    return "olympus" in parsed_url.netloc.lower() or "olympus" in parsed_url.path.lower()

def extract_video_id(url):
    """Extract the video ID from an Olympus URL"""
    parsed_url = urlparse(url)
    
    # Extract ID from query parameters if present
    query_params = parse_qs(parsed_url.query)
    
    if 'videoId' in query_params:
        return query_params['videoId'][0]
    elif 'id' in query_params:
        return query_params['id'][0]
    
    # Extract ID from path components
    path_components = parsed_url.path.split('/')
    for component in path_components:
        if component.startswith('v-') or component.isdigit():
            return component
    
    # If we can't find a specific ID, return the last path component
    if path_components and path_components[-1]:
        return path_components[-1]
    
    # Fallback: use sanitized URL as ID
    return url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')

def process_olympus_transcript(transcript_data, options=None):
    """
    Process a transcript from Olympus video
    
    Args:
        transcript_data (dict): Contains transcript text and metadata
        options (dict): Processing options
        
    Returns:
        dict: Processed results including summary
    """
    if not transcript_data or not transcript_data.get('text'):
        raise ValueError("Invalid transcript data")
    
    text = transcript_data['text']
    video_title = transcript_data.get('title', 'Olympus Video')
    
    if not options:
        options = {}
    
    # Process with default parameters if not specified
    if 'max_length' not in options:
        options['max_length'] = 150
    if 'min_length' not in options:
        options['min_length'] = 30
    
    try:
        summary = summarize_text_enhanced(text, options)
        
        return {
            'transcript': text,
            'summary': summary,
            'title': video_title,
            'timestamp': time.time(),
            'source': 'olympus',
            'video_id': transcript_data.get('video_id', 'unknown')
        }
    except Exception as e:
        logger.error(f"Error processing Olympus transcript: {str(e)}")
        raise 