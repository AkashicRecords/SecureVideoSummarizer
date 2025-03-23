"""
Eleven Labs API client for speech-to-text operations
"""
import os
import logging
import tempfile
import json
import time
import requests
import elevenlabs
from elevenlabs.api import Speech
from app.utils.errors import TranscriptionError, SummarizationError

logger = logging.getLogger(__name__)

class ElevenLabsClient:
    """Client for Eleven Labs API"""
    
    def __init__(self, api_key=None):
        """Initialize the client with API key"""
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if self.api_key:
            elevenlabs.set_api_key(self.api_key)
        else:
            logger.warning("No Eleven Labs API key found. Using default configuration.")
    
    def transcribe(self, audio_file):
        """
        Transcribe audio using Eleven Labs API
        
        Args:
            audio_file (str): Path to the audio file
            
        Returns:
            dict: Transcription result
        """
        try:
            logger.info(f"Transcribing audio with Eleven Labs: {audio_file}")
            
            # For now, we'll use Ollama as a fallback since Eleven Labs is primarily a TTS service
            # We need to use the ollama_client here and make it clear this is a placeholder
            from app.summarizer.ollama_client import ollama_client
            
            logger.warning("Eleven Labs doesn't offer an STT API yet, using Ollama as fallback")
            result = ollama_client.transcribe(audio_file)
            
            if not result or not result.get('text'):
                logger.error("Failed to transcribe with Ollama fallback")
                return {'success': False, 'error': 'Failed to transcribe audio'}
                
            return {'success': True, 'text': result.get('text')}
            
        except Exception as e:
            logger.error(f"Error transcribing with Eleven Labs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def text_to_speech(self, text, voice_id="premade/Adam"):
        """
        Convert text to speech using Eleven Labs
        
        Args:
            text (str): Text to convert to speech
            voice_id (str): Voice ID to use
            
        Returns:
            bytes: Audio data
        """
        try:
            logger.info(f"Converting text to speech with Eleven Labs, length: {len(text)}")
            
            # Generate speech with Eleven Labs
            audio = elevenlabs.generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
            
            return audio
            
        except Exception as e:
            logger.error(f"Error generating speech with Eleven Labs: {str(e)}")
            raise Exception(f"Failed to generate speech: {str(e)}")

# Create a singleton instance
elevenlabs_client = ElevenLabsClient() 