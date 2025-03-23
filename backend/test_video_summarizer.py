#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv
from app.summarizer.processor import VideoSummarizer

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Make sure environment variables are loaded
load_dotenv()

# Temporarily set the environment variable for the test
os.environ['OLLAMA_MODEL'] = 'deepseek-r1:1.5b'

def test_video_summarizer():
    """Test the VideoSummarizer class with Ollama integration"""
    print("\n" + "="*80)
    print("TESTING VIDEO SUMMARIZER WITH OLLAMA")
    print("="*80 + "\n")
    
    # Initialize the VideoSummarizer
    try:
        summarizer = VideoSummarizer(trust_remote_code=True)
        print("✅ VideoSummarizer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize VideoSummarizer: {str(e)}")
        return False
    
    # Test text summarization
    test_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural 
    intelligence displayed by humans or animals. The term "artificial intelligence" is often used to 
    describe machines (or computers) that mimic cognitive functions that humans associate with 
    the human mind, such as learning and problem solving.
    
    As machines become increasingly capable, tasks considered to require "intelligence" are often 
    removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical 
    character recognition is frequently excluded from things considered to be AI, having become 
    a routine technology.
    """
    
    print("\nTest text for summarization:")
    print("-"*80)
    print(test_text)
    print("-"*80)
    
    try:
        # Test summarization
        summary = summarizer.summarize_text(test_text, min_length=30, max_length=100)
        
        if summary:
            word_count = len(summary.split())
            print(f"\n✅ Summary generated: {word_count} words")
            print("-"*80)
            print(summary)
            print("-"*80)
            return True
        else:
            print("❌ Failed to generate summary")
            return False
    except Exception as e:
        print(f"❌ Error during summarization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_video_summarizer()
    sys.exit(0 if success else 1) 