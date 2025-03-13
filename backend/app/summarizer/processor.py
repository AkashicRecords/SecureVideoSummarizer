import os
import subprocess
import tempfile
from flask import current_app
import speech_recognition as sr
from transformers import pipeline
import torch
from app.utils.helpers import generate_unique_id

class VideoSummarizer:
    """Class to handle video summarization process"""
    
    def __init__(self):
        # Initialize the summarization model
        self.device = 0 if torch.cuda.is_available() else -1
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=self.device)
        self.recognizer = sr.Recognizer()
    
    def extract_audio(self, video_path):
        """Extract audio from video file"""
        current_app.logger.info(f"Extracting audio from video: {video_path}")
        
        # Create a temporary file for the audio
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        try:
            # Use ffmpeg to extract audio
            command = [
                'ffmpeg', '-i', video_path, 
                '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', 
                temp_audio_path
            ]
            
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                current_app.logger.error(f"Error extracting audio: {stderr.decode()}")
                raise Exception(f"Failed to extract audio: {stderr.decode()}")
                
            current_app.logger.info(f"Audio extracted successfully to {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            current_app.logger.error(f"Exception during audio extraction: {str(e)}")
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            raise
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file to text"""
        current_app.logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            with sr.AudioFile(audio_path) as source:
                # Adjust for ambient noise and record
                self.recognizer.adjust_for_ambient_noise(source)
                audio_data = self.recognizer.record(source)
                
                # Use Google's speech recognition
                text = self.recognizer.recognize_google(audio_data)
                
                current_app.logger.info(f"Transcription complete: {len(text)} characters")
                return text
                
        except sr.UnknownValueError:
            current_app.logger.error("Speech recognition could not understand audio")
            raise Exception("Speech recognition could not understand audio")
        except sr.RequestError as e:
            current_app.logger.error(f"Could not request results from speech recognition service: {str(e)}")
            raise Exception(f"Could not request results from speech recognition service: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Exception during transcription: {str(e)}")
            raise
        finally:
            # Clean up the temporary audio file
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    def summarize_text(self, text, options):
        """Summarize the transcribed text"""
        current_app.logger.info(f"Summarizing text: {len(text)} characters")
        
        try:
            # Determine max and min length based on options
            if options.get('length') == 'short':
                max_length = 100
                min_length = 30
            elif options.get('length') == 'long':
                max_length = 250
                min_length = 100
            else:  # medium (default)
                max_length = 150
                min_length = 50
            
            # Split text into chunks if it's too long (BART has a limit)
            max_chunk_length = 1024
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            summaries = []
            for chunk in chunks:
                if len(chunk) < 50:  # Skip very short chunks
                    continue
                    
                summary = self.summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            
            # Combine the summaries
            final_summary = " ".join(summaries)
            
            # Format based on options
            if options.get('format') == 'bullets':
                # Simple bullet point conversion - in a real app, you'd use NLP to identify key points
                sentences = [s.strip() for s in final_summary.split('.') if s.strip()]
                final_summary = "\n".join([f"• {s}." for s in sentences])
            
            current_app.logger.info(f"Summarization complete: {len(final_summary)} characters")
            return final_summary
            
        except Exception as e:
            current_app.logger.error(f"Exception during summarization: {str(e)}")
            raise
    
    def process_video(self, video_path, options):
        """Process a video file and generate a summary"""
        current_app.logger.info(f"Processing video for summarization: {video_path}")
        
        try:
            # Extract audio from video
            audio_path = self.extract_audio(video_path)
            
            # Transcribe audio to text
            transcript = self.transcribe_audio(audio_path)
            
            # Summarize the transcript
            summary = self.summarize_text(transcript, options)
            
            # Return both the transcript and summary
            return {
                "transcript": transcript,
                "summary": summary
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to process video: {str(e)}")
            raise 