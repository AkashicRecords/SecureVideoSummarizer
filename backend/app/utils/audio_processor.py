"""
Utility functions for processing audio files
"""
import os
import logging
import subprocess
import tempfile
import time
import traceback
from pathlib import Path
from flask import current_app
from pydub import AudioSegment
from app.summarizer.processor import process_audio, validate_audio, convert_to_wav_enhanced, summarize_text_enhanced
from app.utils.errors import AudioProcessingError, TranscriptionError, SummarizationError
from app.summarizer.ollama_client import ollama_client
import elevenlabs

logger = logging.getLogger(__name__)

def process_audio_file(audio_path, options=None):
    """
    Process an audio file to generate a transcription and summary
    
    Args:
        audio_path (str): Path to the audio file
        options (dict, optional): Options for processing and summarization
        
    Returns:
        dict: Dictionary containing transcription, summary, and success status
        
    Raises:
        AudioProcessingError: If audio processing fails
        TranscriptionError: If transcription fails
        SummarizationError: If summarization fails
    """
    logger.info(f"Processing audio file: {audio_path}")
    
    try:
        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio file not found: {audio_path}")
            
        if os.path.getsize(audio_path) == 0:
            raise AudioProcessingError(f"Audio file is empty: {audio_path}")
            
        result = process_audio(audio_path, options)
        
        if not result["success"]:
            error_type = result.get("error_type", "unknown")
            error_msg = result.get("error", "Unknown error")
            
            if error_type == "audio_processing":
                raise AudioProcessingError(error_msg)
            elif error_type == "transcription":
                raise TranscriptionError(error_msg)
            elif error_type == "summarization":
                raise SummarizationError(error_msg)
            else:
                raise Exception(error_msg)
                
        return result
        
    except (AudioProcessingError, TranscriptionError, SummarizationError) as e:
        logger.error(f"Error processing audio file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing audio file: {str(e)}")
        raise AudioProcessingError(f"Unexpected error: {str(e)}")
        
def validate_audio_file(audio_path):
    """
    Validate an audio file to ensure it can be processed
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        bool: True if the audio file is valid, False otherwise
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return False
        
    if os.path.getsize(audio_path) == 0:
        logger.error(f"Audio file is empty: {audio_path}")
        return False
        
    # If not a WAV file, convert it first
    if not audio_path.lower().endswith('.wav'):
        try:
            temp_wav = convert_to_wav_enhanced(audio_path)
            is_valid = validate_audio(temp_wav)
            
            # Clean up temporary file
            if os.path.exists(temp_wav):
                os.unlink(temp_wav)
                
            return is_valid
        except Exception as e:
            logger.error(f"Error validating audio file: {str(e)}")
            return False
    else:
        return validate_audio(audio_path)

def process_audio(audio_file_path):
    """
    Process an audio file to generate transcript and summary.
    
    Args:
        audio_file_path (str): Path to the audio file
    
    Returns:
        tuple: (transcript, summary)
    """
    try:
        # Validate audio file
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Check file format and convert if needed
        audio_file_path = ensure_wav_format(audio_file_path)
        
        # Generate transcript from audio
        transcript = generate_transcript(audio_file_path)
        
        # Generate summary from transcript
        summary = generate_summary(transcript)
        
        return transcript, summary
        
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}")
        logger.error(traceback.format_exc())
        raise e

def ensure_wav_format(audio_file_path):
    """
    Ensure the audio file is in WAV format, convert if needed.
    
    Args:
        audio_file_path (str): Path to the audio file
    
    Returns:
        str: Path to WAV audio file
    """
    try:
        # Check if file is already WAV
        if audio_file_path.lower().endswith('.wav'):
            return audio_file_path
        
        # Convert to WAV using pydub
        logger.info(f"Converting audio file to WAV format: {audio_file_path}")
        
        # Get file extension
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        
        # Load audio with appropriate format
        if file_ext == '.mp3':
            audio = AudioSegment.from_mp3(audio_file_path)
        elif file_ext == '.ogg':
            audio = AudioSegment.from_ogg(audio_file_path)
        elif file_ext == '.flac':
            audio = AudioSegment.from_file(audio_file_path, format="flac")
        elif file_ext in ['.m4a', '.aac']:
            audio = AudioSegment.from_file(audio_file_path, format="m4a")
        else:
            # Try generic loading
            audio = AudioSegment.from_file(audio_file_path)
        
        # Create WAV file in same directory
        wav_path = os.path.splitext(audio_file_path)[0] + '.wav'
        
        # Export as WAV (16kHz, mono)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")
        
        logger.info(f"Converted audio to WAV: {wav_path}")
        return wav_path
        
    except Exception as e:
        logger.error(f"Error converting audio to WAV: {str(e)}")
        # Return original file if conversion fails
        return audio_file_path

def generate_transcript(audio_file_path, max_duration=None):
    """
    Generate a transcript from an audio file using Ollama
    """
    try:
        logger.info(f"Generating transcript for {audio_file_path}")
        if max_duration and is_audio_too_long(audio_file_path, max_duration):
            raise TranscriptionError(f"Audio duration exceeds maximum of {max_duration} seconds")
            
        # Convert the audio to the appropriate format if needed
        wav_file = convert_to_wav_enhanced(audio_file_path)
        
        # Process the audio using ollama_client
        result = ollama_client.transcribe(wav_file)
        
        if not result or not result.get('text'):
            raise TranscriptionError("Failed to generate transcript - empty response")
            
        return result['text']
    except Exception as e:
        logger.error(f"Error generating transcript: {str(e)}")
        logger.error(traceback.format_exc())
        raise TranscriptionError(f"Failed to generate transcript: {str(e)}")

def generate_summary(transcript, options=None):
    """
    Generate a summary from a transcript using Ollama
    """
    try:
        logger.info("Generating summary from transcript")
        if not transcript or len(transcript.strip()) < 50:
            raise SummarizationError("Transcript too short to summarize")
            
        options = options or {}
        max_length = options.get('max_length', 150)
        min_length = options.get('min_length', 30)
        format_type = options.get('format', 'paragraph')
        focus_key_points = options.get('focus_key_points', True)
        focus_details = options.get('focus_details', False)
        
        # Process with ollama_client
        prompt = f"""Summarize the following transcript into a {format_type} format.
        Focus on {'key points' if focus_key_points else 'overall content'} and
        include {'detailed information' if focus_details else 'only essential information'}.
        Make the summary between {min_length} and {max_length} words.
        
        TRANSCRIPT:
        {transcript}
        
        SUMMARY:"""
        
        result = ollama_client.summarize(prompt)
        
        if not result:
            raise SummarizationError("Failed to generate summary - empty response")
            
        return result
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise SummarizationError(f"Failed to generate summary: {str(e)}")

def is_audio_too_long(audio_path, max_duration_seconds):
    """Check if audio exceeds maximum duration"""
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_seconds = len(audio) / 1000
        return duration_seconds > max_duration_seconds
    except Exception:
        # If we can't determine the length, assume it's within limits
        return False