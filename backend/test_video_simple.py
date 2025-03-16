#!/usr/bin/env python
import os
import sys
import json
import argparse
import subprocess
import logging
import time
import signal
import tempfile
from app.summarizer.processor import VideoSummarizer
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_simple.log')
    ]
)

logger = logging.getLogger("video_simple")

# Global variables for process control
TIMEOUT = 60  # Default timeout in seconds for each operation

def timeout_handler(signum, frame):
    """Handle timeout by raising an exception"""
    print("\n\n*** TIMEOUT OCCURRED - OPERATION TOOK TOO LONG ***\n")
    raise TimeoutError("Operation took too long")

# Set up the timeout signal handler
signal.signal(signal.SIGALRM, timeout_handler)

def run_with_timeout(func, timeout, *args, **kwargs):
    """Run a function with a timeout"""
    print(f"Starting operation with {timeout}s timeout...")
    signal.alarm(timeout)
    try:
        result = func(*args, **kwargs)
        signal.alarm(0)  # Cancel the alarm
        print("Operation completed successfully")
        return result
    except TimeoutError:
        print("Operation timed out!")
        raise
    finally:
        signal.alarm(0)  # Ensure the alarm is canceled

def extract_short_segment(video_path, duration=5):
    """Extract a very short segment from the video"""
    print(f"Extracting {duration} second segment from video...")
    
    # Create a temporary file for the segment
    fd, output_path = tempfile.mkstemp(suffix='.mp4')
    os.close(fd)
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-t', str(duration),
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_path,
        '-y'
    ]
    
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Error extracting segment: {result.stderr}")
            return None
        
        print(f"Successfully extracted segment to {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        print("FFmpeg process timed out!")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None
    except Exception as e:
        print(f"Error in extract_short_segment: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

def simple_summarize(text, max_sentences=3):
    """Simple text summarization by extracting first few sentences"""
    print(f"Using simple summarization for text of length {len(text)}")
    
    try:
        # Try to use NLTK for better sentence splitting
        try:
            from nltk.tokenize import sent_tokenize
            import nltk
            nltk.download('punkt', quiet=True)
            sentences = sent_tokenize(text)
        except (ImportError, ModuleNotFoundError):
            # Fall back to simple splitting if NLTK not available
            print("NLTK not available, using simple sentence splitting")
            sentences = text.replace('!', '.').replace('?', '.').split('.')
            sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        # Create summary from first few sentences
        if len(sentences) > max_sentences:
            summary = ' '.join(sentences[:max_sentences])
            if not summary.endswith('.'):
                summary += '.'
            return summary + f" [Truncated from {len(sentences)} sentences]"
        else:
            return text
    except Exception as e:
        print(f"Error in simple summarization: {str(e)}")
        # Final fallback - just return first 100 chars
        return text[:100] + "... [Truncated due to error]"

def test_ollama_summarization():
    """Test if Ollama is available and can summarize text"""
    print("Testing Ollama for summarization...")
    
    try:
        # Try to import the Ollama client
        from app.summarizer.ollama_client import ollama_client
        
        # Test if the Ollama server is running
        if not ollama_client.health_check():
            print("Ollama server is not available")
            return False
        
        # Test summarization with a simple text
        test_text = "This is a test text for the Ollama summarization. " * 10
        summary = ollama_client.summarize(test_text, min_length=30, max_length=100)
        
        if summary:
            print(f"Ollama summarization successful: {summary}")
            return True
        else:
            print("Ollama summarization returned empty result")
            return False
    except Exception as e:
        print(f"Error testing Ollama: {str(e)}")
        return False

def summarize_from_text(text):
    """Directly test summarization from a given text"""
    print(f"Summarizing text of length {len(text)} characters...")
    
    # 1. Try using Ollama
    try:
        from app.summarizer.ollama_client import ollama_client
        
        if ollama_client.health_check():
            summary = ollama_client.summarize(text, min_length=30, max_length=100)
            if summary:
                print(f"Ollama summarization success: {len(summary)} characters")
                return summary
            else:
                print("Ollama returned empty result, trying fallbacks...")
    except Exception as e:
        print(f"Ollama error: {str(e)}")
    
    # 2. Try using transformers directly if available
    try:
        print("Attempting to use transformers directly...")
        import torch
        from transformers import pipeline
        
        # Use a smaller, faster model for testing
        device = 0 if torch.cuda.is_available() else -1
        try:
            print("Loading BART model...")
            summarizer = pipeline("summarization", model="facebook/bart-base", device=device)
            
            # Split text into chunks if it's too long
            max_chunk_length = 1024
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            summaries = []
            for chunk in chunks:
                if len(chunk.split()) < 20:  # Skip very short chunks
                    continue
                
                result = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                summaries.append(result[0]['summary_text'])
            
            # Combine the summaries
            final_summary = " ".join(summaries)
            print(f"Direct transformers summarization complete: {len(final_summary)} chars")
            return final_summary
            
        except Exception as transformer_error:
            print(f"Error with transformer model: {str(transformer_error)}")
    except ImportError:
        print("Transformers library not available")
    
    # 3. Try VideoSummarizer as last ML option
    try:
        print("Attempting to use VideoSummarizer...")
        app = Flask(__name__)
        app.config['TESTING'] = True
        with app.app_context():
            summarizer = VideoSummarizer()
            
            result = summarizer.summarize_text(text, min_length=30, max_length=100)
            if result != text:  # Check if it actually summarized
                print(f"VideoSummarizer result: {len(result)} characters")
                return result
            else:
                print("VideoSummarizer returned original text, using fallback...")
    except Exception as e:
        print(f"VideoSummarizer error: {str(e)}")
    
    # 4. Final fallback: use simple summarization
    print("All ML summarization methods failed, using simple summarization...")
    return simple_summarize(text, max_sentences=3)

def main():
    parser = argparse.ArgumentParser(description="Simple video processing test")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds to extract")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout for each operation in seconds")
    parser.add_argument("--text", help="Test text to summarize directly (skips video processing)")
    args = parser.parse_args()
    
    global TIMEOUT
    TIMEOUT = args.timeout
    
    print("\n===================================================")
    print("TESTING COMPONENTS INDIVIDUALLY")
    print("===================================================\n")
    
    # First test if Ollama is available
    print("\nTESTING OLLAMA:")
    ollama_available = run_with_timeout(test_ollama_summarization, TIMEOUT)
    print(f"Ollama available: {ollama_available}")
    
    # If text is provided, test summarization directly
    if args.text:
        print("\nTESTING DIRECT SUMMARIZATION:")
        summary = run_with_timeout(summarize_from_text, TIMEOUT, args.text)
        print("\n===================================================")
        print("SUMMARY RESULT:")
        print("===================================================")
        print(summary)
        print("===================================================\n")
        return 0
    
    # Otherwise, process video
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return 1
    
    print("\n===================================================")
    print(f"PROCESSING VIDEO: {args.video_path}")
    print(f"Segment duration: {args.duration} seconds")
    print(f"Operation timeout: {TIMEOUT} seconds")
    print("===================================================\n")
    
    try:
        # Just test extracting a segment
        print("\nTESTING VIDEO SEGMENT EXTRACTION:")
        segment_path = run_with_timeout(extract_short_segment, TIMEOUT, args.video_path, args.duration)
        if not segment_path:
            print("Failed to extract segment. Exiting.")
            return 1
            
        # Clean up the segment
        if os.path.exists(segment_path):
            os.remove(segment_path)
            print(f"Removed temporary segment file: {segment_path}")
        
        # Test with a more realistic sample text
        sample_text = """
        In this lecture on artificial intelligence, we explored the fundamental concepts of machine learning and neural networks. 
        The professor began by discussing supervised learning techniques, where models are trained on labeled data to make predictions on new, unseen examples.
        We then moved on to deep learning architectures, focusing on convolutional neural networks for image recognition and recurrent neural networks for sequence data.
        The lecture highlighted recent advances in natural language processing, particularly the transformer architecture that powers models like GPT and BERT.
        Several real-world applications were presented, including autonomous vehicles, medical diagnosis systems, and recommendation engines.
        The ethical implications of AI were also addressed, with discussions on bias, privacy concerns, and the potential impact on employment.
        The professor concluded by emphasizing the importance of responsible AI development and the need for diverse perspectives in the field.
        Students were encouraged to consider both the technical challenges and societal impacts when developing AI systems.
        """
        
        print("\nTESTING SUMMARIZATION WITH REALISTIC SAMPLE TEXT:")
        summary = run_with_timeout(summarize_from_text, TIMEOUT, sample_text)
        
        print("\n===================================================")
        print("RESULTS")
        print("===================================================")
        print("SAMPLE TEXT:")
        print(sample_text[:150] + "...")
        print("\nSUMMARY:")
        print(summary)
        print("===================================================\n")
        
        return 0
    
    except TimeoutError:
        print("\nProcess timed out. Exiting.")
        return 1
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 